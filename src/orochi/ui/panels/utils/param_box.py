import gradio as gr
import json
from gradio_rangeslider import RangeSlider
import numpy as np
from ..listeners.gradio import general_listener, range_listener


def param_boxes(module, keys=[], kind="common", inputs=None, triggers=None, boxes=None, labels={}):
    """
    Dynamically creates Gradio input boxes for module parameters, enabling dynamic UI updates.

    This function conditionally uses the `@gr.render` decorator to build and
    update UI components (Number, Checkbox, Textbox, RangeSlider) based on
    parameter types and specified triggers. It handles scalar, list, and
    2D list/array type parameters. The generated Gradio components are stored
    in the `boxes` dictionary for external reference and interaction.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance from which to get parameters.
    keys : list of str, optional
        A list of parameter keys to create input boxes for. Defaults to an empty list.
    kind : str, optional
        Specifies the type of parameter boxes to create. Can be "common",
        "lattice", or "sites". Defaults to "common".
    inputs : list[gr.Component] | gr.Component | None, optional
        Gradio components whose values are passed as arguments to the
        `@gr.render` decorated function. These values are used to determine
        the dynamic UI's content. Defaults to None.
    triggers : list[gr.EventListenerCallable] | gr.EventListenerCallable | None, optional
        Specific Gradio event listeners (e.g., `button.click`, `state.change`)
        that will cause the dynamic UI to re-render. If `None` and `inputs` are
        provided, no automatic re-rendering will occur based on `inputs` changes
        unless explicitly added here. Defaults to None.
    boxes : dict, optional
        A dictionary to store references to the generated Gradio input components.
        Keys are parameter addresses (e.g., "@/key/value"), and values are the
        corresponding Gradio component instances. If `None`, an empty dictionary
        will be initialized. This allows external access to the dynamically
        created components. Defaults to None.
    labels : dict, optional
        A dictionary to override the automatically generated labels for the input boxes.
        The keys of this dictionary should be the default label strings (e.g., "scale",
        "peak_delta 0", "radius 0"), and the values should be the custom label
        strings you wish to display. Defaults to an empty dictionary, meaning
        default labels will be used.

    Returns
    -------
    dict | callable
        If `triggers` is None, returns a dictionary of the generated Gradio components
        (`boxes`). If `triggers` is provided, returns the `@gr.render` decorated
        function, which, when executed by Gradio, dynamically generates and
        updates the UI components, populating the `boxes` dictionary.
    """
    if kind == "common":
        make_boxes = make_common_boxes
    elif kind == "lattice":
        make_boxes = make_lattice_boxes
    elif kind == "sites":
        make_boxes = make_sites_boxes
    
    if boxes is None:
        boxes = {}

    def _call_make_boxes():
        try:
            return make_boxes(module, keys, labels, boxes=boxes)
        except TypeError:
            return make_boxes(module, keys, labels)

    if triggers is None:
        boxes.update(_call_make_boxes())
        return boxes
    
    elif inputs is None:
        @gr.render(triggers=triggers)
        def render_boxes(**kwargs):
            boxes.update(_call_make_boxes())
            return boxes
        return boxes # This return statement should likely return the render_boxes callable, not boxes
    else:
        @gr.render(inputs=inputs, triggers=triggers)
        def render_boxes(*args, **kwargs):
            boxes.update(_call_make_boxes())
            return boxes
        return boxes # This return statement should likely return the render_boxes callable, not boxes


def make_common_boxes(module, keys, labels, boxes=None):
    """
    Helper function to create common Gradio input boxes for module parameters.
    Handles scalar, list, and 2D list/array types.
    """
    if boxes is None:
        boxes = {}
    prefix = module["prefix"]
    delimiter = module["address_delimiter"]
   
    for key in keys:
        value = module[key]

        if value is not None:
            with gr.Row():
                if isinstance(value, (list, np.ndarray)):
                    for id1, v1 in enumerate(value):
                        if isinstance(v1, (list, np.ndarray)):
                            for id2, v2 in enumerate(v1):
                                address_list = [prefix, key, "value", str(id1), str(id2)]
                                address = delimiter.join(address_list)
                                # Generate default label based on index and key
                                if id1 == 0 and id2 == 0:
                                    default_label = key
                                else:
                                    default_label = f"{key} {id1} {id2}"
                                
                                # Use custom label if provided, otherwise use default
                                display_label = labels.get(default_label, default_label)

                                with gr.Row():
                                    box = param_box_unit(module, address, display_label, boxes=boxes)
                                    boxes[address] = box

                        else: # Handle 1D list/array
                            address_list = [prefix, key, "value", str(id1)]
                            address = delimiter.join(address_list)
                            if key == "sphere": # Special case for sphere radius
                                default_label = f"radius {id1}"
                            elif len(value) == 1:
                                default_label = key
                            else:
                                default_label = f"{key} {id1}"
                            
                            # Use custom label if provided, otherwise use default
                            display_label = labels.get(default_label, default_label)

                            with gr.Row():
                                box = param_box_unit(module, address, display_label, boxes=boxes)
                                boxes[address] = box

                else: # Handle scalar values
                    address_list = [prefix, key, "value"]
                    address = delimiter.join(address_list)
                    with gr.Row():
                        default_label = key
                        # Use custom label if provided, otherwise use default
                        display_label = labels.get(default_label, default_label)
                        box = param_box_unit(module, address, display_label, boxes=boxes)
                        boxes[address] = box
    return boxes

def make_lattice_boxes(module, keys, labels, boxes=None):
    if boxes is None:
        boxes = {}
    prefix = module["prefix"]
    delimiter = module["address_delimiter"]

    with gr.Row():
        gr.Markdown("## Lattice parameters")

    keys = ["a","b","c","alpha","beta","gamma"]
    with gr.Row():
        for key in keys:
            gr.Markdown(f"{key}")
    with gr.Row():
        for id, label in enumerate(keys):
            address_list = [prefix, "lattice", "value", str(id)]
            address = delimiter.join(address_list)
            label = None
            with gr.Row():
                box = param_box_unit(module, address, label, skip_if_constrained=False)
                boxes[address] = box
    return boxes

def make_sites_boxes(module, keys, labels, boxes=None):
    with gr.Row():
        gr.Markdown("## Atomic sites")

    keys = ["atom", "x","y","z","adp","occupancy"]
    with gr.Row():
        for key in keys:
            gr.Markdown(f"{key}")
    if boxes is None:
        boxes = {}
    prefix = module["prefix"]
    delimiter = module["address_delimiter"]

    symbols = module["symbol"]

    for index, symbol in enumerate(symbols):
        with gr.Row():
            with gr.Row():
                address_list = [prefix, "symbol", "value", str(index)]
                address = delimiter.join(address_list)

                label = f"Site {index}"
                box = param_box_unit(module, address, label, skip_if_constrained=False)
                boxes[address] = box

                address_list = [prefix, "label", "value", str(index)]
                address = delimiter.join(address_list)

                label = f"Label"
                box = param_box_unit(module, address, label, skip_if_constrained=False)  
                boxes[address] = box

            keys = ["x","y","z"]
            for id2, label in enumerate(keys):
                address_list = [prefix, "xyz", "value", str(index), str(id2)]
                address = delimiter.join(address_list)

                label = None
                with gr.Row():
                    box = param_box_unit(module, address, label, skip_if_constrained=False)
                    boxes[address] = box

            for key in ["adp", "occ"]:
                address_list = [prefix, key, "value", str(index)]
                address = delimiter.join(address_list)

                label = None
                with gr.Row():
                    box = param_box_unit(module, address, label, skip_if_constrained=False)
                    boxes[address] = box
    return boxes


def param_box_unit(module, address, label, skip_if_constrained=True, boxes=None):
    """
    Creates a single Gradio input component for a parameter.

    This is a helper method for functions like `make_common_boxes`. It creates a
    Gradio Number, Checkbox, or Textbox based on the type of the parameter's value.
    If the parameter is optimizable (i.e., has an "optimize" attribute in `module.par`),
    an additional "fit" checkbox and a `gradio_rangeslider.RangeSlider` are created.
    Event listeners are attached to update the module's parameter when the UI
    component value changes.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance.
    address : str
        The string address of the parameter within the module (e.g., "@/key/value/0").
    label : str
        The label for the Gradio input component.
    skip_if_constrained : bool, optional
        If True, returns None if the parameter at `address` is constrained,
        otherwise creates an empty Text component. Defaults to True.
    boxes : dict, optional
        Dictionary to store created components.

    Returns
    -------
    gradio.Component | None
        The created Gradio component instance (e.g., `gr.Number`, `gr.Checkbox`,
        `gr.Textbox`) or None if the parameter is skipped or unsupported.
    """

    if module._check_if_address_constrained(address):
        if skip_if_constrained:
            return None
        else:
            gr.Text(value="", label=" ", visible=True)
            return None

    value = module[address]
    if isinstance(value, (list, np.ndarray)):
        value = np.asarray(value).flatten()[0]
    if label == None:
        show_label = False
    else:
        show_label = True

    delimiter = module["address_delimiter"]

    if isinstance(value, (float, int, np.int64, np.float64, np.floating, np.integer)):
        val_scalar = float(value)
        box = gr.Number(label=label, value=val_scalar, scale=10, show_label=show_label)
        # Check if parameter has fit or optimize configuration
        base_key = address.split(delimiter)[1]

        if "fit" in module.par.get(base_key, {}) or "optimize" in module.par.get(base_key, {}): 
            min_address = address.replace("value", "min")
            max_address = address.replace("value", "max")
            try:
                raw_min = np.asarray(module[min_address]).flatten()[0]
                min_val = float(raw_min) if raw_min is not None and not np.isnan(raw_min) else val_scalar - 1.0
            except Exception:
                min_val = val_scalar - 1.0
            try:
                raw_max = np.asarray(module[max_address]).flatten()[0]
                max_val = float(raw_max) if raw_max is not None and not np.isnan(raw_max) else val_scalar + 1.0
            except Exception:
                max_val = val_scalar + 1.0

            min_bound = float(np.amin([min_val, val_scalar, max_val]))
            max_bound = float(np.amax([min_val, val_scalar, max_val]))
            if min_bound == max_bound:
                min_bound -= 1.0
                max_bound += 1.0
            min_bound = np.round(min_bound, 4)
            max_bound = np.round(max_bound, 4)
            val_min_clamp = float(np.clip(min_val, min_bound, max_bound))
            val_max_clamp = float(np.clip(max_val, min_bound, max_bound))

            range_slider = RangeSlider(label="range",
                                     minimum=min_bound,
                                     maximum=max_bound,
                                     value=[val_min_clamp, val_max_clamp],
                                     scale=10,
                                     show_label=False)
            range_slider.change(range_listener(module, 
                                               addresses=[min_address, max_address]), 
                                               inputs=range_slider)
            
            opt_key = "fit" if "fit" in module.par.get(base_key, {}) else "optimize"
            opt_address = address.replace("value", opt_key)
            opt_val = bool(np.asarray(module[opt_address]).flatten()[0])
            check_box = gr.Checkbox(label="fit", value=opt_val, scale=1)
            check_box.change(general_listener(module, opt_address), inputs=check_box)

            if boxes is not None:
                boxes[f"{address}_range"] = range_slider
                boxes[f"{address}_opt"] = check_box

    elif isinstance(value, (bool, np.bool_)):
        box = gr.Checkbox(label=label, value=value, show_label=show_label)

    elif isinstance(value, str):
        box = gr.Textbox(label=label, value=value, show_label=show_label)

    elif isinstance(value, dict):
        v = json.dumps(value, indent=2)
        box = gr.Code(label=label, 
                      value=v, 
                      show_label=show_label, 
                      language="json", 
                      interactive=True,
                      max_lines=50,
                      wrap_lines=True)

    else:
        return None # Skip unsupported types
    box.change(general_listener(module, address), inputs=box)
    return box