import os

def update_work_dir(modules):
    """
    Creates a listener function to update the working directory for multiple modules.

    This function returns an inner `get_selected_path` function, suitable for a
    Gradio File or Directory input's `change` event. When called with a `path`,
    it determines if the path is a directory or file, extracts the directory path,
    and then sets the `work_dir` attribute for all provided `modules` to this path.

    Parameters
    ----------
    modules : list of OrochiBase
        A list of Orochi module instances whose `work_dir` attribute will be updated.

    Returns
    -------
    function
        A `get_selected_path` function (`fn` callable) that takes a path string
        (from a Gradio File/Directory component) and updates the `work_dir` of
        the modules. It returns the determined directory path or `None`.
    """
    def get_selected_path(path):
        if path is None:
            return None
        elif os.path.isdir(path):
            for module in modules:
                module.work_dir = path
            return path
        elif os.path.isfile(path):
            path = os.path.dirname(path)
            for module in modules:
                module.work_dir = path
            return path
        else:
            return None
    return get_selected_path

def update_study_name(modules):
    """
    Creates a listener function to update the study name for multiple modules.

    This function returns an inner `get_selected_path` (misnamed from original code,
    it should be `update_name_action` or similar for clarity) function, suitable for
    a Gradio Textbox or similar input's `change` event. When called with a `name`
    string, it sets the `study_name` attribute for all provided `modules` to this name.

    Parameters
    ----------
    modules : list of OrochiBase
        A list of Orochi module instances whose `study_name` attribute will be updated.

    Returns
    -------
    function
        An action function (`fn` callable) that takes a string `name` and updates the
        `study_name` of the modules. It returns the provided `name`.
    """
    def get_selected_path(name):
        for module in modules:
            module.study_name = name
        return name
    return get_selected_path

def run_module(module, func=None):
    """
    Creates a function to execute an Orochi module's main process and optionally plot results.

    This function returns an inner `action` function, suitable for a Gradio
    Button's `click` event. When `action` is called, it first executes the
    `module`'s main process (by calling `module()`). If an optional `func`
    (or list of functions) is provided, it then calls these functions
    (passing the module implicitly if needed) to generate plot data,
    which is returned for display in a Gradio plot component.

    Parameters
    ----------
    module : OrochiBase (or callable)
        The Orochi module instance to run. It must be callable (e.g., have a
        `__call__` method) to execute its main processing logic.
    func : callable | list of callable, optional
        A function or a list of functions to call after running the module.
        Each function in `func` should typically return a plot object (e.g.,
        a Matplotlib figure or a Plotly figure) compatible with `gr.Plot`,
        or another Gradio-compatible output. If `func` is a list, its
        results are concatenated into a single list. Defaults to None.

    Returns
    -------
    function
        An `action` function (`fn` callable) that executes the module and
        returns its results (typically plots) for Gradio output.
    """

    def action():
        module() # Run the module's __call__ or main processing
        if func is not None:
            if isinstance(func, list):
                res = []
                for f in func:
                    result = f()
                    if isinstance(result, list):
                        res.extend(result) # Flatten nested lists if func returns a list
                    else:
                        res.append(result)
                return res
            else:
                res = func()
            return res
        return None # Required if no output is specified for the click event
    return action

