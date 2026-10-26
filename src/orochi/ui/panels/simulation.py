import os
import gradio as gr
from .markdown import general
from .utils.param_box import param_boxes
from .listeners.figure import plot_interactive_sim
from .listeners.module import run_module
from .utils.fit_reporter import export_simulation_json, LATEX_DELIMITERS

def add_panel(self, 
          module, 
          keys=None, 
          title="Simulation", 
          header=None, 
          footer=None, 
          tips: bool = True):
    if keys is None:
        keys = ["rmin", "rmax", "rstep", "qmax", "qmin", "scale", "qdamp", "qbroad", "delta1", "delta2"]
    """
    Creates a Gradio tab for PDF simulation.

    This method returns a function (`make_ui`) that, when called, constructs a Gradio
    `TabItem` for running and visualizing PDF simulations. The tab provides:
    - A "Simulate" button to trigger the simulation.
    - A plot area to display the simulated G(r) output.
    - Dynamic input boxes for **displaying and updating module parameters**
        relevant to the simulation, as specified by `keys`.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance used for PDF simulation (e.g., an
        instance of `orochi.pdfsim.Simulator`). It's assumed to be callable
        to run the simulation and have attributes like `r` and `Gr` for plotting.
    keys : list of str
        A list of parameter keys from the `module` to be displayed and
        made interactive in the UI.
    title : str, optional
        The title of the tab. Defaults to "Simulation".
    header : str, optional
        Markdown string for the header of the tab. If `None`, no header is displayed.
    footer : str, optional
        Markdown string for the footer of the tab. If `None`, no footer is displayed.
    tips : bool, optional
        If `True`, the tab will display the general instruction markdown
        (`markdown.general.instruction`). If `False`, no general tips are displayed.
        Defaults to `True`.

    Returns
    -------
    function
        A function that, when executed, constructs the Gradio TabItem for PDF simulation.
    """

    from .utils.fit_reporter import LATEX_DELIMITERS

    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        instruction = general.simulation if tips else None 
        if header: gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)
        if instruction:
            with gr.Accordion("Tips", open=False):
                gr.Markdown(instruction, latex_delimiters=LATEX_DELIMITERS)

        ## Panel Uniwue Contents ###
        with gr.Column():
            self.simulation_state = gr.State(value="INIT")
            self.simulation_boxes = {}

            with gr.Row():
                run_button = gr.Button("Simulate")
                update_button = gr.Button("Refresh GUI")

            with gr.Column():
                sim_output = gr.Plot()

                # JSON Export Section below figure
                study_name = getattr(module, "study_name", "pdfsim") or "pdfsim"
                default_json_name = f"{study_name}_simulation_result.json"
                with gr.Row():
                    save_json_path = gr.Textbox(
                        label="Save Simulation JSON (Filename or Relative/Absolute Path)",
                        value=default_json_name,
                        placeholder="e.g. simulation_result.json or output/my_sim.json",
                        scale=4,
                    )
                    save_json_btn = gr.Button("💾 Save JSON", variant="secondary", scale=1)

                with gr.Row():
                    save_json_status = gr.Markdown(value="", latex_delimiters=LATEX_DELIMITERS)
                    save_json_file = gr.File(label="Download Saved JSON", interactive=False, visible=False)

                def do_save_sim_json(target_path):
                    try:
                        work_dir = getattr(self, "work_dir", None) or getattr(module, "work_dir", None)
                        saved_path = export_simulation_json(module, target_path, work_dir=work_dir)
                        msg = f"✅ **Saved successfully**: `{os.path.basename(saved_path)}`<br>📁 Full path: `{saved_path}`"
                        return msg, gr.update(value=saved_path, visible=True)
                    except Exception as e:
                        return f"❌ **Save failed**: {e}", gr.update(visible=False)

                save_json_btn.click(
                    fn=do_save_sim_json,
                    inputs=[save_json_path],
                    outputs=[save_json_status, save_json_file],
                )

                run_button.click(run_module(module,
                                            func=plot_interactive_sim(module)),
                                            outputs=sim_output)
                
            triggers = [self.ui.load, update_button.click]
            if hasattr(self, "param_sync_state"):
                triggers.append(self.param_sync_state.change)
                self.param_sync_state.change(
                    fn=plot_interactive_sim(module),
                    outputs=sim_output,
                )
            labels = {} #{"peak_delta 0": "delta1",
                        #"peak_delta 1": "delta2"}
            constants = []
            variables = []
            for key in keys:
                if key in module.par:
                    if "optimize" in module.par[key] or "fit" in module.par[key]:
                        variables.append(key)
                    else:
                        constants.append(key)

            if constants:
                gr.Markdown("## Constants")
                with gr.Row():
                    param_boxes(module, constants, 
                                triggers=triggers, 
                                boxes=self.simulation_boxes,
                                labels=labels)

            if variables:
                gr.Markdown("## Variables")
                with gr.Row():
                    param_boxes(module, variables, 
                                triggers=triggers, 
                                boxes=self.simulation_boxes,
                                labels=labels)
        ###

        if footer: gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel