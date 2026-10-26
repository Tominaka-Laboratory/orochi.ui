import os
import gradio as gr
from .markdown import general
from .utils.param_box import param_boxes
from .listeners.figure import plot_interactive_fit
from .utils.fit_reporter import (
    format_least_squares_results,
    export_least_squares_json,
    LATEX_DELIMITERS,
)

def add_panel(self, 
          module, 
          keys: list = None, 
          title="Least Squares", 
          header=None, 
          footer=None, 
          tips: bool = True):
    """
    Creates a Gradio tab for performing least-squares fitting of experimental data.

    This tab provides:
    - A "Fit" button to initiate the fitting process.
    - A plot area to display observed vs. simulated G(r) and difference curves.
    - Real-time fit metrics (Rw, R², reduced χ²).
    - Refined parameters table with ±1σ uncertainties.
    - Collapsible accordion with full LMfit diagnostic fit report.
    - Interactive parameter controls.
    """

    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        instruction = general.least_squares if tips else None 
        if header: gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)
        if instruction:
            with gr.Accordion("Tips", open=False):
                gr.Markdown(instruction, latex_delimiters=LATEX_DELIMITERS)

        ## Panel Unique Contents ###
        
        self.least_squares_state = gr.State(value="INIT")
        self.least_squares_boxes = {}
        with gr.Column():
            run_button = gr.Button("Fit", variant="primary")
            func = plot_interactive_fit(module)

            sim_output = gr.Plot(value=func)

            # JSON Export Section below figure
            study_name = getattr(module, "study_name", "least_squares") or "least_squares"
            default_json_name = f"{study_name}_fit_result.json"
            with gr.Row():
                save_json_path = gr.Textbox(
                    label="Save Results JSON (Filename or Relative/Absolute Path)",
                    value=default_json_name,
                    placeholder="e.g. fit_result.json or output/my_fit.json",
                    scale=4,
                )
                save_json_btn = gr.Button("💾 Save JSON", variant="secondary", scale=1)

            with gr.Row():
                save_json_status = gr.Markdown(value="", latex_delimiters=LATEX_DELIMITERS)
                save_json_file = gr.File(label="Download Saved JSON", interactive=False, visible=False)

            def do_save_json(target_path):
                try:
                    work_dir = getattr(self, "work_dir", None) or getattr(module, "work_dir", None)
                    saved_path = export_least_squares_json(module, target_path, work_dir=work_dir)
                    msg = f"✅ **Saved successfully**: `{os.path.basename(saved_path)}`<br>📁 Full path: `{saved_path}`"
                    return msg, gr.update(value=saved_path, visible=True)
                except Exception as e:
                    return f"❌ **Save failed**: {e}", gr.update(visible=False)

            save_json_btn.click(
                fn=do_save_json,
                inputs=[save_json_path],
                outputs=[save_json_status, save_json_file],
            )

            gr.Markdown("### Fit Metrics & Refined Parameters", latex_delimiters=LATEX_DELIMITERS)
            init_rw, init_r2, init_chi2, init_table, init_log = format_least_squares_results(module)

            with gr.Row():
                rw_box = gr.Textbox(
                    label="Rw (Profile Residual)", 
                    value=init_rw, 
                    interactive=False, 
                    scale=2
                )
                r2_box = gr.Textbox(
                    label="R² Goodness-of-Fit", 
                    value=init_r2, 
                    interactive=False, 
                    scale=1
                )
                chi2_box = gr.Textbox(
                    label="Reduced χ²", 
                    value=init_chi2, 
                    interactive=False, 
                    scale=1
                )

            params_table = gr.Markdown(value=init_table, latex_delimiters=LATEX_DELIMITERS)

            with gr.Accordion("Optimization Diagnostics & Fit Report", open=False):
                log_box = gr.Textbox(
                    value=init_log,
                    interactive=False,
                    lines=12,
                    show_label=False,
                )

            def do_fit():
                try:
                    module.set_fit_range()
                except Exception:
                    pass

                # If no obsx is loaded, try pulling from registered pdfget module if available
                if (module.obsx is None or len(module.obsx) == 0) and hasattr(self, "_build_items") and "pdfget" in self._build_items:
                    item = self._build_items["pdfget"]
                    pdf_m = item[2].get("module", item[1][0] if len(item[1]) > 0 else None)
                    if pdf_m is not None:
                        module.set_obs_data(pdf_m)
                        try:
                            module.set_fit_range()
                        except Exception:
                            pass

                if module.obsx is None or len(module.obsx) == 0:
                    gr.Warning("No experimental PDF observation data found! Please execute 'Convert to PDF' in the 1D -> PDF tab first.")
                    return (
                        None,
                        "N/A",
                        "N/A",
                        "N/A",
                        "⚠️ **No Observation Data**: Please run PDF reduction in `1D -> PDF (PDFget)` first to transfer G(r) data into the optimizer.",
                        "No observation data found in optimizer. Run 'Convert to PDF' in the 1D -> PDF tab first.",
                    )

                module()
                fig = func()
                rw_s, r2_s, chi2_s, tbl_md, rep_log = format_least_squares_results(module)
                import time
                state_val = f"OPTIMIZED_{int(time.time() * 1000)}"
                return fig, rw_s, r2_s, chi2_s, tbl_md, rep_log, state_val

            sync_target = getattr(self, "param_sync_state", self.least_squares_state)
            run_button.click(
                fn=do_fit,
                inputs=None,
                outputs=[sim_output, rw_box, r2_box, chi2_box, params_table, log_box, sync_target],
            )

            if hasattr(self, "param_sync_state"):
                def refresh_lls_preview(sync_val):
                    if sync_val and isinstance(sync_val, str) and not sync_val.startswith("OPTIMIZED_"):
                        return gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip()
                    rw_val, r2_val, chi2_val, t_md, l_log = format_least_squares_results(module)
                    return rw_val, r2_val, chi2_val, t_md, l_log

                self.param_sync_state.change(
                    fn=refresh_lls_preview,
                    inputs=[self.param_sync_state],
                    outputs=[rw_box, r2_box, chi2_box, params_table, log_box],
                )

        gr.Markdown("## Parameters", latex_delimiters=LATEX_DELIMITERS)
        with gr.Row():
            target_keys = keys if keys is not None else ["fit_min", "fit_max", "max_nfev", "ftol"]
            param_boxes(module, target_keys, triggers=None)

        ###
        if footer: gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel