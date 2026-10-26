import gradio as gr


def general_listener(module, address):
    """
    Creates a listener function for a Gradio component to update a single module parameter.

    This function returns an inner `action` function suitable for a Gradio event
    listener (e.g., `component.change()`). When the `action` function is called
    with a new value from the Gradio component, it sets this value to the
    specified `address` within the `module` instance.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance whose parameter will be updated. It's assumed
        that `module` supports dictionary-like item assignment (e.g., `module[address] = value`).
    address : str
        The string address (key) of the parameter to update within the `module`.

    Returns
    -------
    function
        An `action` function (`fn` callable) that takes one argument (the new
        value from the Gradio component) and is suitable for use with Gradio
        event listeners (e.g., `gr.Number.change()`, `gr.Checkbox.change()`).
        It returns `None`, as it typically performs a side effect (module update).
    """
    def action(value):
        module[address] = value
        return None # Gradio change functions often expect an output or None
    return action

def range_listener(module, addresses):
    """
    Creates a listener function for a Gradio RangeSlider component to update two module parameters.

    This function returns an inner `action` function designed for a `gradio_rangeslider.RangeSlider`'s
    `change` event. When the `action` function is called with a `range_values` tuple (min, max),
    it updates two corresponding parameters in the `module` instance.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance whose parameters will be updated. It's assumed
        that `module` supports dictionary-like item assignment.
    addresses : list of str
        A list of two string addresses (keys) corresponding to the minimum and
        maximum values that the RangeSlider controls. The first address in the
        list will receive `range_values[0]` (min), and the second will receive
        `range_values[1]` (max).

    Returns
    -------
    function
        An `action` function (`fn` callable) that takes a tuple `range_values`
        and updates the module's parameters. It returns `None`.
    """
    def action(range_values):
        module[addresses[0]] = range_values[0]
        module[addresses[1]] = range_values[1]
        return None
    return action

def checkboxgroup_listener(module, keys):
    """
    Creates a listener function for a Gradio CheckboxGroup to update multiple module parameters.

    This function returns an inner `action` function designed for a Gradio `CheckboxGroup`'s
    `change` event. When the `action` function is called with a list of boolean
    `values` (representing the state of each checkbox), it iterates through
    them and updates the corresponding parameters in the `module` using the
    provided `keys`.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance whose parameters will be updated.
    keys : list of str
        A list of string keys (addresses) corresponding to the parameters in the
        `module` that are controlled by the CheckboxGroup. The order of keys
        should match the order of values received from the CheckboxGroup.

    Returns
    -------
    function
        An `action` function (`fn` callable) that takes a list of boolean values
        and updates the module's parameters. It returns `None`.
    """
    def action(values):
        for n, value in enumerate(values):
            module[keys[n]] = value
        return None
    return action

def update_state(text):
    """
    Creates a listener function to update a Gradio State component with a static text.

    This function returns an inner `action` function suitable for a Gradio
    event listener. When `action` is called, it returns the `text` provided
    during `update_state`'s creation. This is useful for setting a fixed
    message in a `gr.State` or `gr.Textbox` based on an event.

    Parameters
    ----------
    text : str
        The static text string that the listener will return.

    Returns
    -------
    function
        An `action` function (`fn` callable) that, when invoked, returns the
        provided `text`.
    """
    def action():
        return text
    return action

def show_hide_tabes(tab_names):
    def action(select):
        res = []
        for name in tab_names:
            if select == name:
                res.append(gr.update(visible=True))
            else:
                res.append(gr.update(visible=False))
        return res
    return action


def update_boxes(module, boxes):
    """
    Creates a listener function to update the values of multiple Gradio input boxes.

    This function returns an inner `action` function, typically for a button click,
    which iterates through a provided dictionary of `boxes` (Gradio components).
    For each component, it retrieves the corresponding value from the `module`
    and creates a `gr.update` object with the new value. These `gr.update`
    objects are returned as a list, allowing Gradio to efficiently refresh
    the UI components.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance from which to retrieve the latest parameter values.
    boxes : dict
        A dictionary where keys are parameter addresses (e.g., "@/key/value")
        and values are the Gradio component instances that need to be updated.

    Returns
    -------
    function
        An `action` function (`fn` callable) that returns a list of `gr.update`
        objects, each specifying a new value for a corresponding Gradio component.
    """
    def action():
        res = []
        for address, box in boxes.items():
            value = module[address]
            res.append(gr.update(value=value))
        return res
    return action