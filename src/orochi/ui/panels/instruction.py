import os
import gradio as gr
from .markdown import general
from .utils.fit_reporter import LATEX_DELIMITERS


def add_panel(
    self,
    title="Instruction",
    header=None,
    note=None,
    markdown_file=None,
    footer=None,
    tips: bool = True,
):
    """Creates a Gradio panel displaying tutorial Markdown (from a string or `.md` file) and general GUI tips."""
    if markdown_file is not None and os.path.isfile(markdown_file):
        with open(markdown_file, "r", encoding="utf-8") as f:
            note = f.read()
    elif isinstance(note, str) and note.endswith(".md") and os.path.isfile(note):
        with open(note, "r", encoding="utf-8") as f:
            note = f.read()

    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        if header:
            gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)

        if note is not None:
            gr.Markdown(note, latex_delimiters=LATEX_DELIMITERS)

        if tips:
            if note is not None:
                with gr.Accordion("General GUI Usage Instructions", open=False):
                    gr.Markdown(general.instruction, latex_delimiters=LATEX_DELIMITERS)
            else:
                gr.Markdown(general.instruction, latex_delimiters=LATEX_DELIMITERS)

        if footer:
            gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel
