import os

def save_param_json_file(module):
    """
    Creates a listener function to trigger saving of module parameters to a JSON file.

    This function returns an inner `action` function suitable for a Gradio Button's
    `click` event. When this `action` is called, it simply invokes the `save()`
    method on the provided `module` instance, which is assumed to handle the
    parameter saving logic.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance that contains parameters to be saved.
        It's assumed that `module` has a `save()` method.

    Returns
    -------
    function
        An `action` function (`fn` callable) that triggers the module's save
        operation. It returns `None`.
    """
    def action():
        module.save()
        return None
    return action

def load_param_json_file(module):
    """
    Creates a listener function to trigger loading of module parameters from a JSON file.

    This function returns an inner `action` function suitable for a Gradio File
    input's `change` event. When this `action` is called with a `file` object,
    it calls the `load()` method on the provided `module` instance, passing the
    file object. This is assumed to handle the parameter loading logic.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance whose parameters will be loaded.
        It's assumed that `module` has a `load()` method.

    Returns
    -------
    function
        An `action` function (`fn` callable) that takes a file object (from `gr.File`)
        and triggers the module's load operation. It returns `None`.
    """
    def action(file):
        if file is not None:
            module.load(file)
            return None
        else:
            return None
    return action

def read_file(module):
    """
    Creates a listener to read a data file and update the module.
    """
    def read(file):
        if file is not None:
            module.read_file(file.name)
        return None
    return read

def save_file(module, dir):
    """
    Creates a listener to save the data into a data file.
    """
    import datetime
    def save():
        current_time = datetime.datetime.now()
        file_name = f"{current_time.strftime('%Y%m%d%H%M')}"
        file_path = os.path.join(dir, file_name)

        if not os.path.exists(dir):
            os.makedirs(dir)
        
        try:
            module.save_file(file_path)
            print(f"File saved successfully. Module name: {module.name}, File name: {file_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
        return None
    return save