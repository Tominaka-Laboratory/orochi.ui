
def run_ui(panels: dict, 
           work_dir: str, 
           study_name: str, 
           server: str = "127.0.0.1"
           ):
    """
    Launches the Orochi Graphical User Interface with a customized set of panels and environment settings.

    This function serves as the high-level entry point for Orochi. It dynamically constructs 
    the sidebar-based UI by mapping dictionary keys in `panels` to internal `add_panel` methods. 
    This allows for flexible UI layouts tailored to specific crystallographic analysis tasks, 
    such as structure modification, PDF simulation, or AI monitoring.

    Example `panels` configuration:
    ------------------------------
    panels = {
        "instruction": {},
        "system": {},
        "files": {"modules": [phase, simulator]},
        "phase": {
            "module": phase, 
            "keys": ["sphere", "pbc"], 
            "const_keys": ["spherical_constraints", "lattice_constraints", "symmetry_constraints"]
        },
        "simulation": {
            "module": simulator, 
            "keys": ["rmin", "rmax", "rstep", "qmax", "qmin", "scale", "qdamp", "qbroad"]
        },
        "least_squares": {"module": optimizer, "keys": ["fit_min", "fit_max", "max_nfev"]},
        "bayes": {"module": bayes, "keys": ["fit_min", "n_trials", "n_job"]},
        "ai": {"analyzer": analyzer} # Monitor for AI-driven reasoning and RW progress
    }

    Parameters
    ----------
    panels : dict
        A configuration dictionary where keys define the panel type (e.g., "files", "phase") 
        and values are keyword arguments passed to the corresponding `add_{key}_panel` method.
    work_dir : str
        The filesystem path where session data, exported parameters (JSON), and 
        execution logs will be stored.
    study_name : str
        A unique identifier for the current analysis session, often used as the 
        sample name or project ID.
    server : str, optional
        The network address to host the Gradio interface. Defaults to "127.0.0.1" (localhost).
    Returns
    -------
    None
        This function starts the Gradio web server and blocks execution until the server is stopped.
    """
    import os
    from orochi.ui.ui import BaseUI as UI 
        
    os.makedirs(work_dir, exist_ok=True)
    ui = UI()
    ui.work_dir = work_dir
    ui.study_name = study_name
    ui["server"] = server

    for key, value in panels.items():
        if hasattr(ui, f"add_{key}_panel"):
            getattr(ui, f"add_{key}_panel")(**value)
        else:
            ui._logger.info(f"run_ui: Panel type '{key}' is not supported.")

    ui()