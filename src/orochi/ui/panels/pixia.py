import os
import gradio as gr
import numpy as np
from .markdown import general
from .utils.param_box import param_boxes
from .listeners.figure import (
    plot_interactive_pixia,
    plot_interactive_pixia_2d,
    plot_interactive_pixia_diagnostics,
)
from .utils.fit_reporter import export_pixia_json, LATEX_DELIMITERS


def add_panel(
    self,
    module,
    keys=None,
    title="2D Integration (Pixia)",
    header=None,
    footer=None,
    tips: bool = True,
    downstream_pdfget=None,
):
    """Creates a Gradio tab for 2D X-ray detector image integration (`orochi.pixia`)."""
    if keys is None:
        keys = [
            "rambda",
            "energy",
            "distance",
            "x0",
            "y0",
            "tiltx",
            "tilty",
            "polar",
            "thickness",
            "mur",
            "ttmin",
            "ttmax",
            "ttstep",
            "outlier",
            "background_scale",
        ]

    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        instruction = general.pixia if tips else None
        if header:
            gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)
        if instruction:
            with gr.Accordion("Tips", open=False):
                gr.Markdown(instruction, latex_delimiters=LATEX_DELIMITERS)

        with gr.Column():
            self.pixia_state = gr.State(value="INIT")
            self.pixia_boxes = {}

            def _normalize_init_files(val, multiple=False):
                if val is None:
                    return None
                if isinstance(val, (list, tuple)):
                    valid = [str(x) for x in val if x and os.path.exists(str(x))]
                    if not valid:
                        return None
                    return valid if multiple else valid[0]
                if os.path.exists(str(val)):
                    return [str(val)] if multiple else str(val)
                return None

            init_sample = _normalize_init_files(module["sample_file"] if "sample_file" in module.par else None, multiple=True)
            init_bg = _normalize_init_files(module["background_file"] if "background_file" in module.par else None, multiple=True)
            init_mask = _normalize_init_files(module["mask_file"] if "mask_file" in module.par else None, multiple=False)

            # Pre-read initial files if available and not yet loaded into numpy array
            if init_sample and not isinstance(getattr(module, "sample", None), np.ndarray):
                try:
                    module.read()
                except Exception as e:
                    print(f"Notice: initial 2D read in Pixia panel: {e}")

            plot_2d_fn = plot_interactive_pixia_2d(module)
            plot_1d_fn = plot_interactive_pixia(module)

            # Classify keys into Detector Integration parameters (constants) and Calibration Geometry parameters (variables)
            constants = []
            variables = []
            for key in keys:
                if key in module.par:
                    if "optimize" in module.par[key]:
                        variables.append(key)
                    else:
                        constants.append(key)

            # Azimuthal Integration Sector (β Angle Range) Detection & Helpers
            def _detect_sector_mode(mod):
                bmin = getattr(mod, "par", {}).get("betamin", {}).get("value", None)
                bmax = getattr(mod, "par", {}).get("betamax", {}).get("value", None)
                if bmin is None or bmax is None:
                    return "Full (360°)", 18.0, "-180", "180"
                bmin_arr = np.atleast_1d(bmin)
                bmax_arr = np.atleast_1d(bmax)
                if len(bmin_arr) == 1 and np.isclose(bmin_arr[0], -180.0) and np.isclose(bmax_arr[0], 180.0):
                    return "Full (360°)", 18.0, "-180", "180"
                if len(bmin_arr) == 4 and len(bmax_arr) == 4:
                    centers = (bmin_arr + bmax_arr) / 2.0
                    if np.allclose(centers, [45.0, 135.0, -135.0, -45.0], atol=1.0):
                        w = float((bmax_arr[0] - bmin_arr[0]) / 2.0)
                        return "Diagonals (±45°, ±135°)", w, ", ".join(f"{x:.1f}" for x in bmin_arr), ", ".join(f"{x:.1f}" for x in bmax_arr)
                if len(bmin_arr) == 2 and len(bmax_arr) == 2:
                    centers = (bmin_arr + bmax_arr) / 2.0
                    if np.allclose(centers, [90.0, -90.0], atol=1.0):
                        w = float((bmax_arr[0] - bmin_arr[0]) / 2.0)
                        return "Vertical (±90°)", w, ", ".join(f"{x:.1f}" for x in bmin_arr), ", ".join(f"{x:.1f}" for x in bmax_arr)
                    elif np.allclose(centers, [0.0, 180.0], atol=1.0):
                        w = float((bmax_arr[0] - bmin_arr[0]) / 2.0)
                        return "Horizontal (0°, 180°)", w, ", ".join(f"{x:.1f}" for x in bmin_arr), ", ".join(f"{x:.1f}" for x in bmax_arr)
                bmin_str = ", ".join(f"{x:.1f}" for x in bmin_arr) if len(bmin_arr) > 1 else f"{bmin_arr[0]:.1f}"
                bmax_str = ", ".join(f"{x:.1f}" for x in bmax_arr) if len(bmax_arr) > 1 else f"{bmax_arr[0]:.1f}"
                return "Manual (Custom β)", 18.0, bmin_str, bmax_str

            init_mode, init_width, init_bmin_str, init_bmax_str = _detect_sector_mode(module)
            init_sec_summary = getattr(module, "get_azimuthal_mode_summary", lambda: "")() or f"Mode: {init_mode}"

            # Separate Tabs: 2D Detector Image & Mask on Tab 1, 1D Integration & Profile on Tab 2, Calibration on Tab 3
            with gr.Tabs():
                with gr.Tab("🖼️ 2D Detector Image & Mask", id="pixia_tab_2d"):
                    # 1. 2D Data Uploads
                    with gr.Row():
                        sample_upload = gr.File(
                            label="Sample 2D Image (.tif/.img/.his) — Multi-file auto-averages",
                            value=init_sample,
                            file_count="multiple",
                            interactive=True,
                            height=95,
                            elem_classes=["compact-file"],
                        )
                        bg_upload = gr.File(
                            label="Background 2D Image (optional) — Multi-file auto-averages",
                            value=init_bg,
                            file_count="multiple",
                            interactive=True,
                            height=95,
                            elem_classes=["compact-file"],
                        )
                        mask_upload = gr.File(
                            label="Mask 2D Image (optional)",
                            value=init_mask,
                            file_count="single",
                            interactive=True,
                            height=95,
                            elem_classes=["compact-file"],
                        )

                    # 2. Azimuthal Integration Sector (β Angle Range) Controls
                    with gr.Group():
                        with gr.Row():
                            sector_mode = gr.Dropdown(
                                choices=[
                                    "Diagonals (±45°, ±135°)",
                                    "Full (360°)",
                                    "Vertical (±90°)",
                                    "Horizontal (0°, 180°)",
                                    "Manual (Custom β)",
                                ],
                                value=init_mode,
                                label="📐 Azimuthal Integration Sector (β Mode)",
                                scale=3,
                            )
                            sector_width = gr.Slider(
                                minimum=1.0,
                                maximum=45.0,
                                value=init_width,
                                step=0.5,
                                label="Sector Half-Width Δβ (deg)",
                                visible=("Full" not in init_mode and "Manual" not in init_mode),
                                scale=2,
                            )
                            sector_summary = gr.Textbox(
                                value=init_sec_summary,
                                label="Active Integration β Range",
                                interactive=False,
                                scale=4,
                            )
                        with gr.Row(visible=("Manual" in init_mode)) as manual_sector_row:
                            manual_bmin = gr.Textbox(
                                value=init_bmin_str,
                                label="β min (deg) — scalar or comma-separated",
                                placeholder="e.g. -45, 135 or -30",
                                scale=3,
                            )
                            manual_bmax = gr.Textbox(
                                value=init_bmax_str,
                                label="β max (deg) — scalar or comma-separated",
                                placeholder="e.g. 45, -135 or 30",
                                scale=3,
                            )
                            apply_manual_btn = gr.Button("Apply Manual β", variant="secondary", scale=1)

                    # 3. 2D Display & Mask Operations
                    with gr.Row():
                        view_mode = gr.Dropdown(
                            choices=["Sample + Mask Overlay", "Sample (Raw 2D)", "Detector Mask (Binary)", "Background (2D)"],
                            value="Sample + Mask Overlay",
                            label="2D Display Mode",
                            scale=3,
                        )
                        refresh_2d_btn = gr.Button("🔄 Refresh 2D View", scale=1)
                        auto_mask_btn = gr.Button("🎯 Auto-Detect Mask", variant="secondary", scale=1)
                        save_mask_btn = gr.Button("💾 Save Mask as TIFF", variant="secondary", scale=1)

                    pixia_2d_plot = gr.Plot(value=lambda: plot_2d_fn("Sample + Mask Overlay"))

                    with gr.Row():
                        mask_save_name = gr.Textbox(
                            label="Mask Save Path / Filename",
                            value="detector_mask_2d.tif",
                            placeholder="detector_mask_2d.tif",
                            scale=3,
                        )
                        mask_download_file = gr.File(label="Download Saved Mask", interactive=False, visible=False, scale=2)

                    mask_status = gr.Markdown("", latex_delimiters=LATEX_DELIMITERS)

                with gr.Tab("📈 1D Integration", id="pixia_tab_1d"):
                    with gr.Row(equal_height=True):
                        run_button = gr.Button("Integrate 2D -> 1D", variant="primary", scale=3)
                        update_button = gr.Button("Refresh GUI", scale=1)

                    pixia_1d_plot = gr.Plot(value=plot_1d_fn)

                    status_box = gr.Textbox(
                        label="Integration Status",
                        value="Ready to integrate 2D image." if init_sample else "Please upload or verify 2D detector image.",
                        interactive=False,
                        lines=3,
                        max_lines=6,
                    )

                    # JSON Export Section below figure
                    study_name = getattr(module, "study_name", "pixia") or "pixia"
                    default_json_name = f"{study_name}_integration_result.json"
                    with gr.Row():
                        save_json_path = gr.Textbox(
                            label="Save Integration JSON (Filename or Relative/Absolute Path)",
                            value=default_json_name,
                            placeholder="e.g. pixia_integration.json or output/my_pixia.json",
                            scale=4,
                        )
                        save_json_btn = gr.Button("💾 Save JSON", variant="secondary", scale=1)

                    with gr.Row():
                        save_json_status = gr.Markdown(value="", latex_delimiters=LATEX_DELIMITERS)
                        save_json_file = gr.File(label="Download Saved JSON", interactive=False, visible=False)

                    # Detector & Integration Parameters inside Tab 2
                    if constants:
                        gr.Markdown("## Detector & Integration Parameters")
                        with gr.Row():
                            param_boxes(
                                module,
                                constants,
                                triggers=None,
                                boxes=self.pixia_boxes,
                            )

                with gr.Tab("🎯 Geometry Calibration", id="pixia_tab_calib"):
                    default_std = "Ni" if (init_sample and "ni" in str(init_sample).lower()) else "CeO2"
                    with gr.Row(equal_height=True):
                        cal_standard = gr.Dropdown(
                            choices=["Ni", "CeO2"],
                            value=default_std,
                            label="Standard Calibrant Sample",
                            scale=2,
                        )
                        cal_mode = gr.Dropdown(
                            choices=[
                                "pn (Opposing ±X, ±Y - Centered Beam)",
                                "xp-yp (+X vs +Y - Bottom-Left Corner)",
                                "xn-yp (-X vs +Y - Bottom-Right Corner)",
                                "xp-yn (+X vs -Y - Top-Left Corner)",
                                "xn-yn (-X vs -Y - Top-Right Corner)",
                            ],
                            value="pn (Opposing ±X, ±Y - Centered Beam)",
                            label="Calibration Mode",
                            scale=3,
                        )
                        cal_engine = gr.Dropdown(
                            choices=[
                                "LLS (Least Squares / LMFIT - Fast & Accurate)",
                                "Bayesian (Optuna / CMA-ES - Robust Global)",
                                "Bayesian (Optuna / TPE)",
                            ],
                            value="LLS (Least Squares / LMFIT - Fast & Accurate)",
                            label="Optimization Engine",
                            scale=3,
                        )
                        cal_button = gr.Button("Calibrate Geometry", variant="primary", scale=2)

                    with gr.Row(equal_height=True):
                        diag_unit = gr.Radio(
                            choices=["2θ (deg)", "Radius R (mm)"],
                            value="2θ (deg)",
                            label="Axis Unit",
                            scale=2,
                        )
                        diag_width = gr.Slider(
                            minimum=1.0,
                            maximum=30.0,
                            value=10.0,
                            step=1.0,
                            label="Diagnostic Sector Half-Width Δβ (deg)",
                            scale=3,
                        )
                        refresh_diag_btn = gr.Button("🔄 Refresh Diagnostics", scale=1)

                    cal_status_box = gr.Markdown(
                        "**Calibration Guide**: Select standard sample (`Ni` or `CeO2`) and calibration mode (`pn` for centered beam, or `xp-yp` for corner beam). "
                        "Check the **`fit`** checkboxes for parameters to refine in *Calibratable Geometry Parameters* below, then click **`Calibrate Geometry`**.<br>"
                        "Verification graphs below show sector profiles and green theoretical Bragg markers.",
                        latex_delimiters=LATEX_DELIMITERS,
                    )

                    plot_diag_fn = plot_interactive_pixia_diagnostics(module)
                    pixia_diag_plot = gr.Plot(value=lambda: plot_diag_fn(default_std, "2θ (deg)", 10.0, "pn"))

                    gr.Markdown(
                        "> **🔍 How to evaluate calibration:**<br>"
                        "- **Centered Mode (`pn`)**:<br>"
                        "  - **Horizontal (+X vs -X)**: Blue (+X) and Red (-X) should overlap. Center $x_0$ aligns low angles; detector tilt $tilt_x$ aligns high angles.<br>"
                        "  - **Vertical (+Y vs -Y)**: Cyan (+Y) and Amber (-Y) should overlap. Center $y_0$ aligns low angles; detector tilt $tilt_y$ aligns high angles.<br>"
                        "- **Corner Modes (`xp-yp`, `xn-yp`, etc.)**:<br>"
                        "  - **Orthogonal Sectors**: Blue and Cyan curves should overlap in peak positions. Fits center coordinates, tilts, distance, and wavelength simultaneously.<br>"
                        "  - **Diagonal Sector**: Purple curve verifies the third angular projection across the sensor diagonal.<br>"
                        "- **Green Dotted Markers**: Theoretical Bragg reflection positions ($2\\theta_{calc}$ / $R_{calc}$) for the selected calibrant. Distance $L$ and wavelength $\\lambda$ align the experimental peaks with these green lines.",
                        latex_delimiters=LATEX_DELIMITERS,
                    )

                    # Calibratable Geometry Parameters inside Tab 3
                    cal_geom_boxes = {}
                    if variables:
                        with gr.Row(equal_height=True):
                            gr.Markdown("## Calibratable Geometry Parameters")
                            set_bounds_btn = gr.Button(
                                "Set Synchrotron Bounds (±3% λ, ±5% L, ±1° tilt, ±5px center)",
                                variant="secondary",
                            )
                        with gr.Row():
                            param_boxes(
                                module,
                                variables,
                                triggers=None,
                                boxes=cal_geom_boxes,
                            )

            # Wiring 2D View events
            def _update_2d(m):
                return plot_2d_fn(m)

            view_mode.change(fn=_update_2d, inputs=[view_mode], outputs=[pixia_2d_plot])
            refresh_2d_btn.click(fn=_update_2d, inputs=[view_mode], outputs=[pixia_2d_plot])

            # Wiring Azimuthal Sector events
            def _on_sector_mode_change(choice, width_val, view_m):
                if "Full" in choice:
                    module.set_azimuthal_mode("full")
                    summary = module.get_azimuthal_mode_summary()
                    fig = plot_2d_fn(view_m)
                    return gr.update(visible=False), gr.update(visible=False), summary, fig
                elif "Diagonals" in choice:
                    module.set_azimuthal_mode("diagonals", width=float(width_val))
                    summary = module.get_azimuthal_mode_summary()
                    fig = plot_2d_fn(view_m)
                    return gr.update(visible=True, value=float(width_val)), gr.update(visible=False), summary, fig
                elif "Vertical" in choice:
                    module.set_azimuthal_mode("vertical", width=float(width_val))
                    summary = module.get_azimuthal_mode_summary()
                    fig = plot_2d_fn(view_m)
                    return gr.update(visible=True, value=float(width_val)), gr.update(visible=False), summary, fig
                elif "Horizontal" in choice:
                    module.set_azimuthal_mode("horizontal", width=float(width_val))
                    summary = module.get_azimuthal_mode_summary()
                    fig = plot_2d_fn(view_m)
                    return gr.update(visible=True, value=float(width_val)), gr.update(visible=False), summary, fig
                else:  # Manual
                    summary = "Manual Mode: specify β min and β max below and click Apply."
                    return gr.update(visible=False), gr.update(visible=True), summary, gr.update()

            sector_mode.change(
                fn=_on_sector_mode_change,
                inputs=[sector_mode, sector_width, view_mode],
                outputs=[sector_width, manual_sector_row, sector_summary, pixia_2d_plot],
            )

            def _on_sector_width_change(width_val, choice, view_m):
                if "Diagonals" in choice:
                    module.set_azimuthal_mode("diagonals", width=float(width_val))
                elif "Vertical" in choice:
                    module.set_azimuthal_mode("vertical", width=float(width_val))
                elif "Horizontal" in choice:
                    module.set_azimuthal_mode("horizontal", width=float(width_val))
                else:
                    return gr.update(), gr.update()
                summary = module.get_azimuthal_mode_summary()
                fig = plot_2d_fn(view_m)
                return summary, fig

            sector_width.change(
                fn=_on_sector_width_change,
                inputs=[sector_width, sector_mode, view_mode],
                outputs=[sector_summary, pixia_2d_plot],
            )

            def _on_apply_manual(bmin_text, bmax_text, view_m):
                try:
                    def _parse_vals(t):
                        parts = [float(x.strip()) for x in str(t).split(",") if x.strip()]
                        if not parts:
                            raise ValueError("Angle list cannot be empty")
                        return parts[0] if len(parts) == 1 else parts
                    bmin_parsed = _parse_vals(bmin_text)
                    bmax_parsed = _parse_vals(bmax_text)
                    module.set_azimuthal_mode("manual", betamin=bmin_parsed, betamax=bmax_parsed)
                    summary = module.get_azimuthal_mode_summary()
                    fig = plot_2d_fn(view_m)
                    return summary, fig
                except Exception as e:
                    return f"Error parsing angles: {e}", gr.update()

            apply_manual_btn.click(
                fn=_on_apply_manual,
                inputs=[manual_bmin, manual_bmax, view_mode],
                outputs=[sector_summary, pixia_2d_plot],
            )

            def _extract_single(item):
                if item is None:
                    return None
                if isinstance(item, str):
                    return item
                if isinstance(item, dict):
                    return item.get("path") or item.get("name")
                if hasattr(item, "path") and item.path:
                    return item.path
                if hasattr(item, "name") and item.name:
                    return item.name
                return str(item)

            def _extract_paths(f):
                if f is None:
                    return None
                if isinstance(f, (list, tuple)):
                    paths = [_extract_single(item) for item in f]
                    valid = [p for p in paths if p and os.path.exists(p)]
                    if not valid:
                        return None
                    return valid if len(valid) > 1 else valid[0]
                single = _extract_single(f)
                return single if (single and os.path.exists(single)) else None

            def _on_sample_change(f, m):
                paths = _extract_paths(f)
                if paths:
                    module.read_file(paths, target="sample")
                return plot_2d_fn(m)

            sample_upload.change(fn=_on_sample_change, inputs=[sample_upload, view_mode], outputs=[pixia_2d_plot])

            def _on_bg_change(f, m):
                paths = _extract_paths(f)
                if paths:
                    module.read_file(paths, target="background")
                return plot_2d_fn(m)

            bg_upload.change(fn=_on_bg_change, inputs=[bg_upload, view_mode], outputs=[pixia_2d_plot])

            def _on_mask_change(f, m):
                paths = _extract_paths(f)
                if paths:
                    mask_path = paths[0] if isinstance(paths, list) else paths
                    module.read_file(mask_path, target="mask")
                return plot_2d_fn(m)

            mask_upload.change(fn=_on_mask_change, inputs=[mask_upload, view_mode], outputs=[pixia_2d_plot])

            # Auto-detect mask handler
            def do_auto_mask(m_mode):
                try:
                    stop_r = module.auto_beamstop_mask()
                    m = module.get_mask()
                    module.mask = m
                    msg = f"[OK] **Auto-mask complete**: beamstop shadow radius = **{stop_r} px** detected around nominal center $(x_0={module['x0']}, y_0={module['y0']})$.<br>Active sensor area: **{m.mean()*100:.1f}%**. Ready to integrate or save as TIFF."
                    fig = plot_2d_fn(m_mode)
                    return fig, msg
                except Exception as e:
                    return None, f"[Error] Auto-mask failed: {e}"

            auto_mask_btn.click(fn=do_auto_mask, inputs=[view_mode], outputs=[pixia_2d_plot, mask_status])

            # Save mask as TIFF handler
            def do_save_mask_tiff(target_name, m_mode):
                try:
                    import tifffile
                    work_dir = getattr(self, "work_dir", None) or getattr(module, "work_dir", None) or os.getcwd()
                    if not target_name or not str(target_name).strip():
                        target_name = "detector_mask_2d.tif"
                    if not os.path.isabs(target_name):
                        target_path = os.path.join(work_dir, target_name)
                    else:
                        target_path = target_name
                    target_path = os.path.abspath(target_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    m = getattr(module, "mask", None)
                    if m is None or not isinstance(m, np.ndarray):
                        m = module.get_mask()
                        module.mask = m

                    tifffile.imwrite(target_path, m.astype(np.float32))
                    module["mask_file"] = target_path
                    module.mask_image = m
                    msg = f"[OK] **Mask saved as TIFF**: `{os.path.basename(target_path)}`<br>Full path: `{target_path}`<br>[Active] Set as active mask in Pixia."
                    fig = plot_2d_fn(m_mode)
                    return fig, msg, gr.update(value=target_path, visible=True)
                except Exception as e:
                    return None, f"[Error] Failed to save mask: {e}", gr.update(visible=False)

            save_mask_btn.click(fn=do_save_mask_tiff, inputs=[mask_save_name, view_mode], outputs=[pixia_2d_plot, mask_status, mask_download_file])

            # JSON export handler
            def do_save_pixia_json(target_path):
                try:
                    work_dir = getattr(self, "work_dir", None) or getattr(module, "work_dir", None)
                    saved_path = export_pixia_json(module, target_path, work_dir=work_dir)
                    msg = f"[OK] **Saved successfully**: `{os.path.basename(saved_path)}`<br>Full path: `{saved_path}`"
                    return msg, gr.update(value=saved_path, visible=True)
                except Exception as e:
                    return f"[Error] **Save failed**: {e}", gr.update(visible=False)

            save_json_btn.click(
                fn=do_save_pixia_json,
                inputs=[save_json_path],
                outputs=[save_json_status, save_json_file],
            )

            # 1D Integration & Save handler
            sync_targets = [self.param_sync_state] if hasattr(self, "param_sync_state") else []

            def _integrate_and_save():
                module()
                fig_1d = plot_interactive_pixia(module)()
                work_dir = getattr(module, "work_dir", os.getcwd())
                study_name = getattr(module, "study_name", "pixia")
                save_path = os.path.join(work_dir, f"{study_name}_1d.txt")
                sec_info = getattr(module, "get_azimuthal_mode_summary", lambda: "")()
                try:
                    module.save_file(save_path)
                    n_pts = len(module.tt1d) if module.tt1d is not None else 0
                    msg = f"[OK] Integrated 1D profile generated ({n_pts} points) [{sec_info}] and saved to:\n  {save_path}"

                    pdf_target = downstream_pdfget
                    if pdf_target is None and hasattr(self, "_build_items") and "pdfget" in self._build_items:
                        p_it = self._build_items["pdfget"]
                        pdf_target = p_it[2].get("module", p_it[1][0] if len(p_it[1]) > 0 else None)

                    if pdf_target is not None:
                        if hasattr(pdf_target, "sync_from_pixia"):
                            pdf_target.sync_from_pixia(module)
                        else:
                            pdf_target.read_file(save_path, target="sample")
                        msg += "\n[OK] Forwarded to downstream PDFget module (ready for PDF reduction)!"
                except Exception as e:
                    msg = f"Integration completed, but save failed: {e}"

                import time
                sync_val = [f"PIXIA_RUN_{int(time.time() * 1000)}"] if sync_targets else []
                return (fig_1d, msg, *sync_val)

            run_button.click(
                fn=_integrate_and_save,
                inputs=None,
                outputs=[pixia_1d_plot, status_box, *sync_targets],
            )

            geom_components = list(cal_geom_boxes.values())

            def _get_geom_box_updates():
                updates = []
                delimiter = getattr(module, "address_delimiter", "/")
                for addr in cal_geom_boxes.keys():
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
                        comp = cal_geom_boxes.get(addr)
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
                        val = float(np.ravel(module[k])[0])
                        updates.append(gr.update(value=val))
                return updates

            def _on_refresh_gui():
                fig_1d = plot_interactive_pixia(module)()
                return (fig_1d, *_get_geom_box_updates())

            update_button.click(
                fn=_on_refresh_gui,
                inputs=None,
                outputs=[pixia_1d_plot, *geom_components],
            )

            if variables:
                def _on_set_bounds():
                    module.set_natural_bounds()
                    l_min = float(np.ravel(module.par["rambda"]["min"])[0])
                    l_max = float(np.ravel(module.par["rambda"]["max"])[0])
                    d_min = float(np.ravel(module.par["distance"]["min"])[0])
                    d_max = float(np.ravel(module.par["distance"]["max"])[0])
                    msg = (
                        "[OK] **Physical synchrotron bounds applied to Calibratable Parameters**:<br>"
                        f"- lambda: `[{l_min:.5f}, {l_max:.5f}]` A (+-3% around current `{float(np.ravel(module['rambda'])[0]):.5f}` A)<br>"
                        f"- Distance: `[{d_min:.2f}, {d_max:.2f}]` mm (+-5% around current `{float(np.ravel(module['distance'])[0]):.2f}` mm)<br>"
                        f"- Tilts: (theta_x, theta_y) in [+-1.0 deg] around current angles<br>"
                        f"- Center: (x0, y0) in [+-5.0 px] around current center"
                    )
                    module._state = "BOUNDS_SET"
                    return (msg, *_get_geom_box_updates())

                set_bounds_btn.click(
                    fn=_on_set_bounds,
                    inputs=None,
                    outputs=[cal_status_box, *geom_components],
                )

            def _calibrate_and_plot(std_choice, mode_choice, engine_choice, d_unit, d_width, *comp_vals):
                delimiter = getattr(module, "address_delimiter", "/")
                if comp_vals and len(comp_vals) == len(cal_geom_boxes):
                    for (addr, _), val in zip(cal_geom_boxes.items(), comp_vals):
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
                            try:
                                module[k] = float(val)
                            except Exception:
                                pass

                std_key = str(std_choice).strip().lower() if std_choice else "ceo2"
                mode_str = str(mode_choice).lower()
                if "xp-yp" in mode_str:
                    mode_key = "xp-yp"
                elif "xn-yp" in mode_str:
                    mode_key = "xn-yp"
                elif "xp-yn" in mode_str:
                    mode_key = "xp-yn"
                elif "xn-yn" in mode_str:
                    mode_key = "xn-yn"
                else:
                    mode_key = "pn"

                eng_str = str(engine_choice).lower()
                if "cma" in eng_str:
                    eng_key = "cmaes"
                    eng_label = "Optuna CMA-ES (Bayesian Global)"
                elif "tpe" in eng_str:
                    eng_key = "tpe"
                    eng_label = "Optuna TPE (Bayesian)"
                else:
                    eng_key = "lmfit"
                    eng_label = "LLS (Least Squares / LMFIT TRF)"

                all_geom_keys = ["x0", "y0", "tiltx", "tilty", "distance", "rambda"]
                active_keys = [
                    k for k in all_geom_keys
                    if bool(np.asarray(getattr(module, "par", {}).get(k, {}).get("optimize", False)).flatten()[0])
                ]

                if not active_keys:
                    active_keys = ["x0", "y0", "tiltx", "tilty", "distance"]
                    for k in active_keys:
                        if k in module.par:
                            module.par[k]["optimize"] = True

                fixed_keys = [k for k in all_geom_keys if k not in active_keys]
                init_vals = {k: float(np.ravel(module[k])[0]) for k in active_keys}
                try:
                    import time
                    t_start = time.time()
                    module.calibrate(standard=std_key, fit_keys=active_keys, mode=mode_key, engine=eng_key)
                    t_elapsed = time.time() - t_start
                    fig_diag = plot_diag_fn(std_choice, d_unit, d_width, mode_key)
                    fig_1d = plot_interactive_pixia(module)()

                    mode_label = "Opposing +-X, +-Y (Centered)" if mode_key == "pn" else f"Corner Orthogonal ({mode_key})"

                    table_lines = [
                        "| Parameter | Initial Value | Calibrated Value | Shift (Delta) | Exploration Bounds |",
                        "| :--- | :--- | :--- | :--- | :--- |",
                    ]
                    for k in active_keys:
                        init_v = init_vals[k]
                        fin_v = float(np.ravel(module[k])[0])
                        diff_v = fin_v - init_v
                        p_min = float(np.ravel(module.par[k].get("min", [np.nan]))[0])
                        p_max = float(np.ravel(module.par[k].get("max", [np.nan]))[0])
                        unit = " A" if k == "rambda" else (" mm" if k == "distance" else (" deg" if "tilt" in k else " px"))
                        sign = "+" if diff_v >= 0 else ""
                        table_lines.append(
                            f"| **`{k}`** | {init_v:.4f}{unit} | **{fin_v:.4f}{unit}** | {sign}{diff_v:.4f}{unit} | `[{p_min:.4f}, {p_max:.4f}]` |"
                        )
                    params_table_md = "\n".join(table_lines)

                    msg = (
                        f"### [OK] Calibration complete ({t_elapsed:.2f} s)\n"
                        f"- **Optimization Engine**: `{eng_label}`\n"
                        f"- **Geometry Mode**: `{mode_label}`\n"
                        f"- **Standard Calibrant**: `{std_choice}`\n\n"
                        f"{params_table_md}\n\n"
                        f"> [Note] Parameters below have been automatically synchronized with the refined geometry."
                    )
                    module._state = "CALIBRATED"
                    return (fig_diag, fig_1d, msg, *_get_geom_box_updates())
                except Exception as e:
                    fig_diag = plot_diag_fn(std_choice, d_unit, d_width, mode_key)
                    fig_1d = plot_interactive_pixia(module)()
                    return (fig_diag, fig_1d, f"[Error] Calibration failed: {e}", *_get_geom_box_updates())

            cal_button.click(
                fn=_calibrate_and_plot,
                inputs=[cal_standard, cal_mode, cal_engine, diag_unit, diag_width, *geom_components],
                outputs=[pixia_diag_plot, pixia_1d_plot, cal_status_box, *geom_components],
            )

            def _update_diag(std, mode_c, unit, width):
                mode_str = str(mode_c).lower()
                if "xp-yp" in mode_str:
                    mk = "xp-yp"
                elif "xn-yp" in mode_str:
                    mk = "xn-yp"
                elif "xp-yn" in mode_str:
                    mk = "xp-yn"
                elif "xn-yn" in mode_str:
                    mk = "xn-yn"
                else:
                    mk = "pn"
                return plot_diag_fn(std, unit, width, mk)

            diag_inputs = [cal_standard, cal_mode, diag_unit, diag_width]
            refresh_diag_btn.click(
                fn=_update_diag,
                inputs=diag_inputs,
                outputs=[pixia_diag_plot],
            )
            cal_standard.change(
                fn=_update_diag,
                inputs=diag_inputs,
                outputs=[pixia_diag_plot],
            )
            cal_mode.change(
                fn=_update_diag,
                inputs=diag_inputs,
                outputs=[pixia_diag_plot],
            )
            diag_unit.change(
                fn=_update_diag,
                inputs=diag_inputs,
                outputs=[pixia_diag_plot],
            )
            diag_width.change(
                fn=_update_diag,
                inputs=diag_inputs,
                outputs=[pixia_diag_plot],
            )


        if footer:
            gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel
