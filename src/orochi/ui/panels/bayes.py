import os
import gradio as gr
from .markdown import general
from .utils.param_box import param_boxes
from .listeners.figure import open_dashboard, plot_interactive_fit
from .utils.fit_reporter import (
    format_bayes_results,
    export_bayes_json,
    LATEX_DELIMITERS,
)

def add_panel(self, 
          module, 
          keys: list = None, 
          title="Bayesian Optimization", 
          header=None, 
          footer=None, 
          tips: bool = True):
    """
    Creates a Gradio tab for performing Bayesian optimization.

    This tab provides:
    - A "Fit" button to initiate the optimization process.
    - A "Dashboard" button to open the Optuna dashboard in browser.
    - A plot area to display observed vs. simulated G(r) and difference curves.
    - Best objective score (Rw) and trial progression status.
    - Best parameter values table.
    - Collapsible accordion with Optuna study summary diagnostics.
    - Dynamic input boxes for configuring parameters and trial counts.
    """

    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        instruction = general.bayes if tips else None 
        if header: gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)
        if instruction:
            with gr.Accordion("Tips", open=False):
                gr.Markdown(instruction, latex_delimiters=LATEX_DELIMITERS)

        ## Panel Unique Contents ###
            
        with gr.Column():
            self.bayes_state = gr.State(value="INIT")
            self.bayes_boxes = {}
            with gr.Row():
                run_button = gr.Button("Fit", variant="primary")
                dashboard_button = gr.Button("Dashboard")                                        
                dashboard_button.click(open_dashboard(module))

            with gr.Column():
                func = plot_interactive_fit(module)
                sim_output = gr.Plot(value=func)

                # JSON Export Section below figure
                study_name = getattr(module, "study_name", "bayes") or "bayes"
                default_json_name = f"{study_name}_opt_result.json"
                with gr.Row():
                    save_json_path = gr.Textbox(
                        label="Save Results JSON (Filename or Relative/Absolute Path)",
                        value=default_json_name,
                        placeholder="e.g. bayes_result.json or output/my_bayes.json",
                        scale=4,
                    )
                    save_json_btn = gr.Button("💾 Save JSON", variant="secondary", scale=1)

                with gr.Row():
                    save_json_status = gr.Markdown(value="", latex_delimiters=LATEX_DELIMITERS)
                    save_json_file = gr.File(label="Download Saved JSON", interactive=False, visible=False)

                def do_save_bayes_json(target_path):
                    try:
                        work_dir = getattr(self, "work_dir", None) or getattr(module, "work_dir", None)
                        saved_path = export_bayes_json(module, target_path, work_dir=work_dir)
                        msg = f"✅ **Saved successfully**: `{os.path.basename(saved_path)}`<br>📁 Full path: `{saved_path}`"
                        return msg, gr.update(value=saved_path, visible=True)
                    except Exception as e:
                        return f"❌ **Save failed**: {e}", gr.update(visible=False)

                save_json_btn.click(
                    fn=do_save_bayes_json,
                    inputs=[save_json_path],
                    outputs=[save_json_status, save_json_file],
                )

                gr.Markdown("### Bayesian Optimization Summary", latex_delimiters=LATEX_DELIMITERS)
                init_score, init_trials, init_table, init_log = format_bayes_results(module)

                with gr.Row():
                    score_box = gr.Textbox(
                        label="Best Objective (Rw)", 
                        value=init_score, 
                        interactive=False, 
                        scale=2
                    )
                    trials_box = gr.Textbox(
                        label="Trials Status", 
                        value=init_trials, 
                        interactive=False, 
                        scale=2
                    )

                params_table = gr.Markdown(value=init_table, latex_delimiters=LATEX_DELIMITERS)

                with gr.Accordion("Bayesian Study Diagnostics & Logs", open=False):
                    log_box = gr.Textbox(
                        value=init_log,
                        interactive=False,
                        lines=12,
                        show_label=False,
                    )

                def do_bayes():
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
                            "⚠️ **No Observation Data**: Please run PDF reduction in `1D -> PDF (PDFget)` first to transfer G(r) data into the optimizer.",
                            "No observation data found in optimizer. Run 'Convert to PDF' in the 1D -> PDF tab first.",
                        )

                    module()
                    fig = func()
                    b_score, b_trials, b_tbl, b_log = format_bayes_results(module)
                    import time
                    sync_val = f"BAYES_DONE_{int(time.time() * 1000)}"
                    return fig, b_score, b_trials, b_tbl, b_log, sync_val

                sync_target = getattr(self, "param_sync_state", self.bayes_state)
                run_button.click(
                    fn=do_bayes,
                    inputs=None,
                    outputs=[sim_output, score_box, trials_box, params_table, log_box, sync_target],
                )

            gr.Markdown("## Parameters", latex_delimiters=LATEX_DELIMITERS)
            with gr.Row():
                triggers = [self.ui.load]
                target_keys = keys if keys is not None else ["fit_min", "fit_max", "n_trials"]
                param_boxes(module, target_keys, triggers=triggers)
        
        ###
        if footer: gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel