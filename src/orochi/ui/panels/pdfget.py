import os
import gradio as gr
import numpy as np
from .markdown import general
from .utils.param_box import param_boxes
from .listeners.figure import plot_interactive_pdfget
from .listeners.module import run_module
from .utils.fit_reporter import export_pdfget_json, LATEX_DELIMITERS


def add_panel(
    self,
    module,
    keys=None,
    pixia_module=None,
    downstream_sim=None,
    downstream_fit=None,
    title="PDF Reduction (PDFget)",
    header=None,
    footer=None,
    tips: bool = True,
):
    """Creates a Gradio tab for 1D total scattering to G(r) data reduction (`orochi.pdfget`)."""
    if pixia_module is None and hasattr(self, "_build_items") and "pixia" in self._build_items:
        p_item = self._build_items["pixia"]
        pixia_module = p_item[2].get("module", p_item[1][0] if len(p_item[1]) > 0 else None)

    if pixia_module is not None and hasattr(module, "sync_from_pixia"):
        module.sync_from_pixia(pixia_module, copy_params_only=True)

    if keys is None:
        keys = [
            "composition",
            "rambda",
            "energy",
            "qmin",
            "qmax",
            "qstep",
            "fitmin",
            "fitmax",
            "base_function_type",
            "lorch",
            "padding",
            "ripple_min_r",
            "number_density",
            "rmin",
            "rmax",
        ]

    from .utils.fit_reporter import LATEX_DELIMITERS

    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        instruction = general.pdfget if tips else None
        if header:
            gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)
        if instruction:
            with gr.Accordion("Tips", open=False):
                gr.Markdown(instruction, latex_delimiters=LATEX_DELIMITERS)

        with gr.Column():
            self.pdfget_state = gr.State(value="INIT")
            self.pdfget_boxes = {}

            init_sample_pdf = module["sample_file"] if ("sample_file" in module.par and module["sample_file"] and os.path.exists(str(module["sample_file"]))) else None
            init_bg_pdf = module["background_file"] if ("background_file" in module.par and module["background_file"] and os.path.exists(str(module["background_file"]))) else None

            def _extract_file_path(f):
                if f is None:
                    return None
                if isinstance(f, str):
                    return f
                if isinstance(f, dict):
                    return f.get("path") or f.get("name")
                if hasattr(f, "path") and f.path:
                    return f.path
                if hasattr(f, "name") and f.name:
                    return f.name
                return str(f)

            with gr.Row():
                sample_upload = gr.File(
                    label="1D Diffraction Data (2theta, I, [dummy_baseline])",
                    value=init_sample_pdf,
                    interactive=True,
                    height=95,
                    elem_classes=["compact-file"],
                )
                bg_upload = gr.File(
                    label="1D Container Background (optional)",
                    value=init_bg_pdf,
                    interactive=True,
                    height=95,
                    elem_classes=["compact-file"],
                )

            def _on_sample_upload(f):
                p = _extract_file_path(f)
                if p and os.path.exists(p):
                    module.read_file(p, target="sample")

            def _on_bg_upload(f):
                p = _extract_file_path(f)
                if p and os.path.exists(p):
                    module.read_file(p, target="background")

            # Upload listeners hooked up below after pdfget_components is constructed

            with gr.Row():
                if pixia_module is not None:
                    import_pixia_btn = gr.Button("Import 1D from Pixia")
                run_button = gr.Button("Convert to PDF", variant="primary")
                tune_button = gr.Button("Minimize Ripples")
                update_button = gr.Button("Refresh GUI")

            with gr.Column():
                pdfget_output = gr.Plot()

                # JSON Export Section below figure
                study_name = getattr(module, "study_name", "pdfget") or "pdfget"
                default_json_name = f"{study_name}_reduction_result.json"
                with gr.Row():
                    save_json_path = gr.Textbox(
                        label="Save Reduction JSON (Filename or Relative/Absolute Path)",
                        value=default_json_name,
                        placeholder="e.g. pdf_reduction.json or output/my_reduction.json",
                        scale=4,
                    )
                    save_json_btn = gr.Button("💾 Save JSON", variant="secondary", scale=1)

                with gr.Row():
                    save_json_status = gr.Markdown(value="", latex_delimiters=LATEX_DELIMITERS)
                    save_json_file = gr.File(label="Download Saved JSON", interactive=False, visible=False)

                def do_save_pdf_json(target_path):
                    try:
                        work_dir = getattr(self, "work_dir", None) or getattr(module, "work_dir", None)
                        saved_path = export_pdfget_json(module, target_path, work_dir=work_dir)
                        msg = f"[OK] **Saved successfully**: `{os.path.basename(saved_path)}`<br>Full path: `{saved_path}`"
                        return msg, gr.update(value=saved_path, visible=True)
                    except Exception as e:
                        return f"[Error] **Save failed**: {e}", gr.update(visible=False)

                save_json_btn.click(
                    fn=do_save_pdf_json,
                    inputs=[save_json_path],
                    outputs=[save_json_status, save_json_file],
                )

                def _propagate_downstream(pdf_mod):
                    r_arr = getattr(pdf_mod, "r", None)
                    gr_arr = getattr(pdf_mod, "Gr", None)
                    if r_arr is None or gr_arr is None:
                        return
                    import numpy as np
                    r = np.asarray(r_arr, dtype=float)
                    Gr = np.asarray(gr_arr, dtype=float)
                    if len(r) == 0:
                        return

                    # 1. Forward to simulation modules
                    sim_targets = []
                    if downstream_sim is not None:
                        sim_targets.append(downstream_sim)
                    elif hasattr(self, "_build_items") and "simulation" in self._build_items:
                        item = self._build_items["simulation"]
                        sim_m = item[2].get("module", item[1][0] if len(item[1]) > 0 else None)
                        if sim_m is not None:
                            sim_targets.append(sim_m)

                    for s in sim_targets:
                        try:
                            if hasattr(s, "sync_from_pdfget"):
                                s.sync_from_pdfget(pdf_mod)
                            s.set_obs_data(pdf_mod)
                        except Exception:
                            try:
                                s.set_obs_data(r, Gr)
                            except Exception:
                                pass

                    # 2. Forward to fitting modules (least_squares, bayes)
                    fit_targets = []
                    if downstream_fit is not None:
                        fit_targets.append(downstream_fit)
                    elif hasattr(self, "_build_items"):
                        for fit_key in ["least_squares", "bayes"]:
                            if fit_key in self._build_items:
                                item = self._build_items[fit_key]
                                fit_m = item[2].get("module", item[1][0] if len(item[1]) > 0 else None)
                                if fit_m is not None:
                                    fit_targets.append(fit_m)

                    for f in fit_targets:
                        try:
                            f.set_obs_data(pdf_mod)
                        except Exception:
                            try:
                                f.set_obs_data(r, Gr)
                            except Exception:
                                pass

            constants = []
            variables = []
            for key in keys:
                if key in module.par:
                    if "optimize" in module.par[key]:
                        variables.append(key)
                    else:
                        constants.append(key)

            if constants:
                gr.Markdown("## PDF Reduction Parameters")
                with gr.Row():
                    param_boxes(
                        module,
                        constants,
                        triggers=None,
                        boxes=self.pdfget_boxes,
                    )

            if variables:
                gr.Markdown("## Optimizable Reduction Parameters")
                with gr.Row():
                    param_boxes(
                        module,
                        variables,
                        triggers=None,
                        boxes=self.pdfget_boxes,
                    )

            pdfget_components = list(self.pdfget_boxes.values())

            def _get_pdfget_box_updates():
                updates = []
                delimiter = getattr(module, "address_delimiter", "/")
                for addr in self.pdfget_boxes.keys():
                    comp = self.pdfget_boxes[addr]
                    if addr.endswith("_range"):
                        base_addr = addr[:-6]
                        k = base_addr.split(delimiter)[1]
                        val = float(np.ravel(module[k])[0])
                        p_min = float(np.ravel(module.par[k].get("min", [val - 1.0]))[0])
                        p_max = float(np.ravel(module.par[k].get("max", [val + 1.0]))[0])
                        min_b = float(np.amin([p_min, val, p_max]))
                        max_b = float(np.amax([p_min, val, p_max]))
                        if min_b == max_b:
                            min_b -= 1.0
                            max_b += 1.0
                        min_b = float(np.round(min_b, 4))
                        max_b = float(np.round(max_b, 4))
                        val_min_clamp = float(np.clip(p_min, min_b, max_b))
                        val_max_clamp = float(np.clip(p_max, min_b, max_b))
                        if comp is not None:
                            comp.minimum = min_b
                            comp.maximum = max_b
                        updates.append(gr.update(minimum=min_b, maximum=max_b, value=[val_min_clamp, val_max_clamp]))
                    elif addr.endswith("_opt"):
                        base_addr = addr[:-4]
                        k = base_addr.split(delimiter)[1]
                        opt = bool(np.ravel(module.par[k].get("optimize", [False]))[0])
                        updates.append(gr.update(value=opt))
                    else:
                        k = addr.split(delimiter)[1]
                        val = module[k]
                        if isinstance(val, (float, int, np.floating, np.integer)):
                            val = float(np.ravel(val)[0])
                        elif isinstance(val, np.ndarray):
                            val = val.tolist()
                        else:
                            val = str(val)
                        updates.append(gr.update(value=val))
                return updates

            def _sync_pdfget_inputs(box_vals):
                delimiter = getattr(module, "address_delimiter", "/")
                if box_vals and len(box_vals) == len(self.pdfget_boxes):
                    for addr, val in zip(self.pdfget_boxes.keys(), box_vals):
                        if val is None:
                            continue
                        if addr.endswith("_range"):
                            base_addr = addr[:-6]
                            k = base_addr.split(delimiter)[1]
                            if isinstance(val, (list, tuple)) and len(val) == 2:
                                if k in module.par:
                                    module.par[k]["min"] = [float(val[0])]
                                    module.par[k]["max"] = [float(val[1])]
                        elif addr.endswith("_opt"):
                            base_addr = addr[:-4]
                            k = base_addr.split(delimiter)[1]
                            if k in module.par:
                                module.par[k]["optimize"] = bool(val)
                        else:
                            k = addr.split(delimiter)[1]
                            # Guard: do not let stale UI 'flat' overwrite empirical baseline
                            if k == "base_function_type":
                                has_data_baseline = (
                                    hasattr(module, "data")
                                    and isinstance(module.data, dict)
                                    and module.data.get("base_function", np.empty(0)).size > 0
                                )
                                if (
                                    has_data_baseline
                                    and module.get("base_function_type") == "data"
                                    and str(val).strip().lower() == "flat"
                                ):
                                    continue
                            try:
                                if isinstance(module[k], (float, int, np.floating, np.integer)):
                                    module[k] = float(val)
                                else:
                                    module[k] = val
                            except Exception:
                                pass

            sync_targets = [self.param_sync_state] if hasattr(self, "param_sync_state") else []

            def _run_and_plot(*box_vals):
                import time
                _sync_pdfget_inputs(box_vals)
                module()
                _propagate_downstream(module)
                fig = plot_interactive_pdfget(module)()
                sync_val = [f"PDFGET_RUN_{int(time.time() * 1000)}"] if sync_targets else []
                return (fig, *sync_val, *_get_pdfget_box_updates())

            run_button.click(
                fn=_run_and_plot,
                inputs=pdfget_components,
                outputs=[pdfget_output, *sync_targets, *pdfget_components],
            )

            def _tune_and_plot(*box_vals):
                import time
                _sync_pdfget_inputs(box_vals)
                module.tune(n_trials=40)
                _propagate_downstream(module)
                fig = plot_interactive_pdfget(module)()
                sync_val = [f"PDFGET_TUNE_{int(time.time() * 1000)}"] if sync_targets else []
                return (fig, *sync_val, *_get_pdfget_box_updates())

            tune_button.click(
                fn=_tune_and_plot,
                inputs=pdfget_components,
                outputs=[pdfget_output, *sync_targets, *pdfget_components],
            )

            def _on_refresh_gui():
                fig = plot_interactive_pdfget(module)()
                return (fig, *_get_pdfget_box_updates())

            update_button.click(
                fn=_on_refresh_gui,
                inputs=None,
                outputs=[pdfget_output, *pdfget_components],
            )

            def _on_sample_upload_and_update(f):
                _on_sample_upload(f)
                return _get_pdfget_box_updates()

            def _on_bg_upload_and_update(f):
                _on_bg_upload(f)
                return _get_pdfget_box_updates()

            sample_upload.change(
                fn=_on_sample_upload_and_update,
                inputs=sample_upload,
                outputs=pdfget_components,
            )
            bg_upload.change(
                fn=_on_bg_upload_and_update,
                inputs=bg_upload,
                outputs=pdfget_components,
            )

            if pixia_module is not None:
                def _import_and_plot():
                    import time
                    module.from_pixia(pixia_module)
                    module()
                    _propagate_downstream(module)
                    fig = plot_interactive_pdfget(module)()
                    sync_val = [f"PDFGET_IMPORT_{int(time.time() * 1000)}"] if sync_targets else []
                    return (fig, *sync_val, *_get_pdfget_box_updates())

                import_pixia_btn.click(
                    fn=_import_and_plot,
                    inputs=None,
                    outputs=[pdfget_output, *sync_targets, *pdfget_components],
                )

        if footer:
            gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel

