import gradio as gr
import numpy as np
from .markdown import general
from .utils.param_box import param_boxes

def add_panel(self, 
                    module, 
                    keys, 
                    const_keys=None, 
                    title="Structure", 
                    header=None, 
                    footer=None, 
                    tips: bool = True):
    """
    Creates a Gradio tab for structure visualization and parameter editing (phase).

    This method returns a function (`make_ui`) that constructs a Gradio `TabItem`
    for managing structural information. The tab provides:
    - A 3D crystal viewer (HTML output).
    - Controls to **update the structure** and **refresh the GUI**.
    - Dynamic input boxes for **displaying and updating module parameters**
        specified by `keys` and `const_keys` (e.g., lattice parameters, atomic coordinates, ADPs).

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance representing the phase or structure (e.g.,
        an `orochi.phase.Phase` instance). It's assumed to have a `viewer`
        attribute and support dictionary-like parameter access.
    keys : list of str
        A list of parameter keys (e.g., parameter addresses) from the `module`
        that will be displayed and made interactive in the UI.
    const_keys : list of str, optional
        A list of parameter keys that represent constraints or fixed values,
        displayed separately from `keys`. Defaults to `None`.
    title : str, optional
        The title of the tab. Defaults to "Structure".
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
        structure management.
    """

    from .utils.fit_reporter import LATEX_DELIMITERS

    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        instruction = general.structure if tips else None 
        if header: gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)
        if instruction:
            with gr.Accordion("Tips", open=False):
                gr.Markdown(instruction, latex_delimiters=LATEX_DELIMITERS)

        ## Panel Uniwue Contents ###
            
        with gr.Row():
            self.phase_state = gr.State(value="INIT")
            self.phase_boxes = {}

            with gr.Column():
                # gr.Markdown("Model")
                func = plot_structure_model(module)

                if self["viewer_auto_update"]:
                    output_3d_html = gr.HTML(label="Crystal 3D View",
                                                        value=func,
                                                        every=self["viewer_update_time"],
                                                        container=True,
                                                        )
                else:
                    output_3d_html = gr.HTML(label="Crystal 3D View",
                                                        value=func,
                                                        container=True,
                                                        )
                
            with gr.Column():
                with gr.Row():
                    update_button = gr.Button("Make structure")
                    update_button.click(update_structure_info(module),
                                                        outputs=output_3d_html)
                    refresh_button = gr.Button("Refresh GUI")

                self.phase_param_triggers = [self.ui.load, refresh_button.click]
                if hasattr(self, "param_sync_state"):
                    self.phase_param_triggers.append(self.param_sync_state.change)
                    self.param_sync_state.change(fn=plot_structure_model(module), outputs=output_3d_html)
                if const_keys is not None:
                    gr.Markdown("## Constraints")
                    with gr.Row():
                        labels = {"spherical_constraints": "spherical",
                                    "lattice_constraints": "lattice",
                                    "symmetry_constraints": "symmetry"}
                        param_boxes(module, const_keys, 
                                    labels=labels,
                                    boxes=self.phase_boxes)
                        
                # Filter out lattice and atomic site keys because they are specifically
                # rendered below in make_lattice_boxes ("## Lattice parameters")
                # and make_sites_boxes ("## Atomic sites").
                excluded_from_shape = {"lattice", "adp", "atom", "symbol", "label", "xyz", "occ"}
                shape_keys = [k for k in keys if k not in excluded_from_shape] if keys else []

                if shape_keys:
                    gr.Markdown("## Shape")
                    param_boxes(module, shape_keys, 
                                triggers=self.phase_param_triggers, 
                                boxes=self.phase_boxes)
                
        param_boxes(module, kind="lattice", triggers=self.phase_param_triggers, boxes=self.phase_boxes)
        param_boxes(module, kind="sites", triggers=self.phase_param_triggers, boxes=self.phase_boxes)
        ###
        if footer: gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel

def update_structure_info(module):
    """
    Creates a listener function to update structural information and apply constraints.

    This function returns an inner `action` function, typically for a button click,
    which performs several updates on the `module`. It sets initial minimum and
    maximum values for 'adp' (atomic displacement parameters), resets all
    constraints, and then conditionally applies symmetry, lattice, and spherical
    constraints based on module flags. Finally, it clears changed parameters,
    runs the module's main calculation (`module()`), and triggers a structure model plot.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance containing structural parameters and constraint methods.
        It's assumed to have `_reset_constraints`, `set_symmetry_constraints`,
        `set_lattice_constraints`, `set_spherical_constraints`,
        `_clear_changed_parameters`, and be callable (`module()`).

    Returns
    -------
    function
        An `action` function (`fn` callable) that updates structure information,
        applies constraints, runs the module, and returns the result of plotting
        the structure model.
    """
    def action():
        module["adp", "min"] = np.ones_like(module["adp"]) *0.0001
        module["adp", "max"] = np.ones_like(module["adp"]) *0.01
        # Apply constraints
        module._reset_constraints()
        if module["symmetry_constraints"]:
            module.set_symmetry_constraints()
        if module["lattice_constraints"]:
            module.set_lattice_constraints()
        if module["spherical_constraints"]:
            module.set_spherical_constraints()
        module._clear_changed_parameters()
        module()
        
        return plot_structure_model(module)()
    return action


def plot_structure_model(module):
    """
    Creates a listener function to plot the 3D structure model.

    This function returns an inner `action` function, suitable for a Gradio
    HTML or Plot component. When `action` is called, it invokes the `viewer`
    associated with the module (assumed to be a callable method that updates
    its internal state for rendering) and then returns the HTML representation
    of the viewer for display.

    Parameters
    ----------
    module : object
        An object instance with a `viewer` attribute, which is itself
        expected to be callable and have an `html` attribute (e.g., a 3D
        viewer object).

    Returns
    -------
    function
        An `action` function (`fn` callable) that updates the viewer and
        returns its HTML content for display in Gradio.
    """
    viewer = getattr(module, "viewer", None)
    if viewer is None:
        try:
            from orochi.view.model_viewer import ModelViewer
            viewer = ModelViewer()
            viewer.phase = module
            module.viewer = viewer
        except Exception:
            viewer = None

    def action():
        if viewer is not None:
            try:
                viewer()
                return getattr(viewer, "html", "")
            except Exception:
                return "<div>Structure viewer unavailable</div>"
        return "<div>No viewer configured</div>"
    return action