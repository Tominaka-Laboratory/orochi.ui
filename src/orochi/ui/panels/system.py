import gradio as gr
from .markdown import general
from .listeners.gradio import show_hide_tabes


def add_panel(self, 
          title="System", 
          header=None, 
          footer=None, 
          tips: bool = False):
    """
    Creates a Gradio tab for system-level configurations (currently under construction).

    Parameters
    ----------
    title : str, optional
        The title of the system tab. Defaults to "System".
    header : str, optional
        Markdown string for the header of the tab. If `None`, no header is displayed.
    footer : str, optional
        Markdown string for the footer of the tab. If `None`, no footer is displayed.
    tips : bool, optional
        If `True`, the tab will display the general instruction markdown
        (`markdown.general.instruction`). If `False`, no general tips are displayed.
        Defaults to `False`.

    Returns
    -------
    function
        A function that, when executed, constructs the Gradio TabItem for
        system configurations.
    """

    with gr.Column(visible=False) as new_panel:
        instruction = general.instruction if tips else None 
        if header: gr.Markdown(header)
        if instruction:
            with gr.Accordion("Tips", open=False):
                gr.Markdown(instruction)

        ## Panel Uniwue Contents ###
        with gr.Column():
            gr.Markdown("## System Settings (Under Construction)") # Updated placeholder message
            tab_names = ["pdffit2", "orochi.pdfsim"]
            drop_down = gr.Dropdown(choices=tab_names, label="Simulator")

        tabs = []
        for tab_name in tab_names:
            tabs.append(self._panels[tab_name])
        
        drop_down.change(fn=show_hide_tabes(tab_names),
                            inputs=drop_down, outputs=tabs)
        
        ###
        if footer: gr.Markdown(footer)
        self._panels[title] = new_panel