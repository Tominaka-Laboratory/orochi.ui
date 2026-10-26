import gradio as gr
import os
from .markdown import general
from .listeners.file import save_param_json_file, load_param_json_file, read_file, save_file
from .listeners.module import update_study_name, update_work_dir



def add_panel(self, 
          title="Files", 
          modules:list=[], 
          header=None, 
          footer=None, 
          tips: bool = True):
    """
    Creates a Gradio tab for file management, including study name, work directory,
    and loading/saving parameter and data files.

    This method returns a function (`make_ui`) that, when called, constructs a
    Gradio `TabItem` dedicated to file operations. It allows users to:
    - Edit the **study name** and **working directory**.
    - **Load/Save JSON parameter files** for specified `modules`.
    - **Read files** into modules that support a `read_file` method.

    Parameters
    ----------
    title : str, optional
        The title of the files tab. Defaults to "Files".
    modules : list of OrochiBase, optional
        A list of Orochi module instances that support file operations
        (e.g., `save()`, `load()`, `read_file()`, `study_name`, `work_dir`).
        Defaults to an empty list.
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
        A function that, when executed, constructs the Gradio TabItem for
        file management.
    """

    from .utils.fit_reporter import LATEX_DELIMITERS

    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        instruction = general.files if tips else None 
        if header: gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)
        if instruction:
            with gr.Accordion("Tips", open=False):
                gr.Markdown(instruction, latex_delimiters=LATEX_DELIMITERS)

        ## Panel Uniwue Contents ###

        with gr.Column():
            gr.Markdown("## Study name & work directory")
            with gr.Row():
                study_text = gr.Textbox(label="study_name", value=self.study_name, interactive=True)
                study_text.change(fn=update_study_name(modules),
                                    inputs=study_text)          

                work_dir_text = gr.Textbox(label="work_dir", value=self.work_dir, interactive=True)
                work_dir_text.change(fn=update_work_dir(modules),
                                        inputs=work_dir_text)

        with gr.Column():
            gr.Markdown("## Read files")
            with gr.Row():
                for module in modules:
                    with gr.Column():
                        if "read_file" in dir(module):
                            load_input = gr.File(label=f"{module.name}", interactive=True)
                            load_input.change(read_file(module),
                                                inputs=load_input)
                        else:
                            gr.Text(value="", label=" ", visible=True)

        with gr.Column():
            gr.Markdown("## Save data files")
            with gr.Row():
                for module in modules:
                    with gr.Column():
                        if "save_file" in dir(module):
                            save_button = gr.Button(f"{module.name}")
                            work_dir = os.path.join(self.work_dir, self.study_name, module.name)
                            save_button.click(save_file(module, work_dir))
                        else:
                            gr.Text(value="", label=" ", visible=True)

        with gr.Column():
            gr.Markdown("## Load JSON param files") # Consistent casing
            with gr.Row():
                for module in modules:
                    with gr.Column():
                        load_input = gr.File(label=f"{module.name}", interactive=True)
                        load_input.change(load_param_json_file(module),
                                            inputs=load_input)
                        
        with gr.Column():
            gr.Markdown("## Save JSON param files") # Consistent casing
            with gr.Row():
                for module in modules:
                    with gr.Column():
                        save_button = gr.Button(f"{module.name}")
                        save_button.click(save_param_json_file(module))          
        ###
        if footer: gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel