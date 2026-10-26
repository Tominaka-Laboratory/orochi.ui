import gradio as gr
import os
from orochi.base.core import OrochiBase
from .params import default
from .css import CSS
from .fullscreen_js import FULLSCREEN_JS
from .icons import *
from .theme import get_theme, OrochiTheme

ICON_FILENAME = os.path.join(os.path.dirname(__file__), "orochi_icon.png")

def _patch_gradio_queue():
    """Defensively prevent unhandled KeyError/IndexError when stale clients or unrendered components connect to the queue."""
    try:
        import gradio.queueing
        orig_push = gradio.queueing.Queue.push
        if getattr(orig_push, "_orochi_safe", False):
            return

        async def safe_push(self, body, request, username):
            try:
                return await orig_push(self, body, request, username)
            except (KeyError, IndexError) as e:
                idx = getattr(body, "fn_index", None)
                return False, f"Function index {idx} not found in active session: {e}", "error"

        safe_push._orochi_safe = True
        gradio.queueing.Queue.push = safe_push
    except Exception:
        pass

_patch_gradio_queue()



class _TabProxy:
    """Backward-compatibility proxy mapping legacy ui.tab.* calls to add_*_panel."""

    def __init__(self, ui):
        self._ui = ui

    def instruction(self, *args, **kwargs):
        self._ui.add_instruction_panel(*args, **kwargs)
        return "instruction"

    def pdfget(self, *args, **kwargs):
        self._ui.add_pdfget_panel(*args, **kwargs)
        return "pdfget"

    def phase(self, *args, **kwargs):
        self._ui.add_phase_panel(*args, **kwargs)
        return "phase"

    def simulation(self, *args, **kwargs):
        self._ui.add_simulation_panel(*args, **kwargs)
        return "simulation"

    def least_squares(self, *args, **kwargs):
        self._ui.add_least_squares_panel(*args, **kwargs)
        return "least_squares"

    def bayes(self, *args, **kwargs):
        self._ui.add_bayes_panel(*args, **kwargs)
        return "bayes"

    def files(self, *args, **kwargs):
        self._ui.add_files_panel(*args, **kwargs)
        return "files"

    def pixia(self, *args, **kwargs):
        self._ui.add_pixia_panel(*args, **kwargs)
        return "pixia"

    def ai(self, *args, **kwargs):
        self._ui.add_ai_panel(*args, **kwargs)
        return "ai"

    def system(self, *args, **kwargs):
        self._ui.add_system_panel(*args, **kwargs)
        return "system"

    def log(self, *args, **kwargs):
        self._ui.add_log_panel(*args, **kwargs)
        return "log"


class BaseUI(OrochiBase):
    """
    A base class for creating Gradio user interfaces for Orochi modules.

    This class provides a foundational structure for building interactive web UIs
    using Gradio. It handles the setup of the Gradio Blocks interface,
    manages tabs for different functionalities, and includes helper methods
    for creating UI components related to Orochi modules. It inherits from `OrochiBase`
    to manage parameters and logging.

    Attributes
    ----------
    server_name : str
        The server name for launching the Gradio app. Defaults to "127.0.0.1".
    title : str
        The title of the Gradio application. Defaults to "Orochi".
    tabs : list
        A list to store functions that create individual tabs in the UI.
    ui : gradio.Blocks
        The main Gradio Blocks object that holds the UI.
    theme : gradio.themes.Theme
        The Gradio theme applied to the UI.
    """
    phase_param_triggers = [] # This appears to be a class-level attribute, often used for shared triggers.

    @property
    def tab(self):
        """Backward-compatibility proxy for legacy ui.tab.* calls."""
        return _TabProxy(self)

    @property
    def tabs(self):
        return list(self._panels.keys())

    @tabs.setter
    def tabs(self, value):
        # Gracefully accept legacy ui.tabs = [...] assignments without error
        pass

    def __init__(self, theme: str = "Orochi"):
        """
        Initializes the BaseUI class, setting up default parameters, theme, and tab manager.

        This constructor initializes the `OrochiBase` parent class, sets the UI
        title, configures the Gradio theme based on the input `theme` (supporting custom
        Orochi scientific blue themes, built-in Gradio themes, or custom ThemeClass instances).

        Parameters
        ----------
        theme : str or gr.themes.ThemeClass, optional
            The theme name or instance to use (e.g. 'Orochi', 'OrochiBlue', 'OrochiOcean',
            'Citrus', 'Soft', 'Default'). Defaults to 'Orochi' (custom high-contrast sapphire & slate).
        """
        self.par = default.par
        self._par_key_info = default.par_key_info

        super().__init__() # Initializes OrochiBase, which might set self["server"] etc.
        self.title = "Orochi"
        self._panels = {}
        self._buttons = {}
        self._build_items = {}
        
        try:
            self.theme = get_theme(theme)
        except Exception as e:
            self._logger.error(f"Error loading theme '{theme}': {e}. Falling back to default OrochiTheme.")
            self.theme = OrochiTheme

    def __call__(self):
        """
        Builds and launches the Gradio user interface.

        This method serves as the entry point to construct and run the Gradio application.
        It first calls `_make_ui` to initialize the main Blocks object,
        then `add_tabs` to populate the UI with defined tabs, and finally `launch`
        to start the Gradio web server.
        """
        self._make_ui()

        self.ui.launch(server_name=self["server"], 
                       share=False, # Sharing is typically disabled for local deployments
                       favicon_path=ICON_FILENAME) # Set a custom favicon for the browser tab

    def _make_ui(self):
        """
        Creates the main Gradio Blocks interface.

        Initializes the `self.ui` attribute with a `gradio.Blocks` instance,
        applying the configured `title` and `theme`. It also sets up a `gr.State`
        component, `self._state`, which can be used to manage UI-wide state.
        """
        head_html = f'<link rel="icon" type="image/png" href="data:image/png;base64,{ICON_BASE64}">\n' if ICON_BASE64 else ""
        head_html += FULLSCREEN_JS
        self.ui = gr.Blocks(title=self.title, 
                            theme=self.theme, 
                            fill_height=True, 
                            fill_width=True, 
                            css=CSS,
                            head=head_html)
        
        self._state = gr.State(value=None) # Initialize a Gradio State component

        with self.ui:
            self.param_sync_state = gr.State(value="INIT")
            with gr.Column():
                # Separate main calculation workflow panels from auxiliary panels (Lesson Note / Execution Log)
                workflow_keys = [k for k in self._build_items if k not in ("instruction", "log_viewer")]
                aux_keys = [k for k in ["instruction", "log_viewer"] if k in self._build_items]

                # Render workflow panels first so that the first workflow panel is active and visible by default
                build_order = (workflow_keys + aux_keys) if workflow_keys else aux_keys
                for k in build_order:
                    func, args, kwargs = self._build_items[k]
                    func(self, *args, **kwargs)

                # Initial linkage: propagate Pixia parameters (rambda, energy) to PDFget
                if "pixia" in self._build_items and "pdfget" in self._build_items:
                    try:
                        px_item = self._build_items["pixia"]
                        px_m = px_item[2].get("module", px_item[1][0] if len(px_item[1]) > 0 else None)
                        pg_item = self._build_items["pdfget"]
                        pg_m = pg_item[2].get("module", pg_item[1][0] if len(pg_item[1]) > 0 else None)
                        if px_m is not None and pg_m is not None:
                            if hasattr(pg_m, "sync_from_pixia"):
                                pg_m.sync_from_pixia(px_m, copy_params_only=True)
                            elif "rambda" in px_m.par and "rambda" in pg_m.par and px_m["rambda"] is not None:
                                pg_m["rambda"] = px_m["rambda"]
                    except Exception:
                        pass

                # Initial linkage: propagate PDF reduction parameters (qmax, qmin, rambda) to simulation
                if "pdfget" in self._build_items and "simulation" in self._build_items:
                    try:
                        p_item = self._build_items["pdfget"]
                        pdf_m = p_item[2].get("module", p_item[1][0] if len(p_item[1]) > 0 else None)
                        s_item = self._build_items["simulation"]
                        sim_m = s_item[2].get("module", s_item[1][0] if len(s_item[1]) > 0 else None)
                        if pdf_m is not None and sim_m is not None:
                            if hasattr(sim_m, "sync_from_pdfget"):
                                sim_m.sync_from_pdfget(pdf_m, auto_range=True)
                            else:
                                for qk in ["qmax", "qmin", "rambda", "energy"]:
                                    if qk in pdf_m.par and qk in sim_m.par and pdf_m[qk] is not None:
                                        sim_m[qk] = pdf_m[qk]
                    except Exception:
                        pass

            with gr.Sidebar(elem_id="my-sidebar"):

                gr.HTML(f"""<div class="sidebar-logo">{logo_svg}<span class="sidebar-logo-text">Orochi</span><span class="sidebar-logo-nexus">GUI</span></div>""")

                # Separate panel titles into workflow titles and auxiliary titles
                aux_titles = []
                for k in aux_keys:
                    _, args, kwargs = self._build_items[k]
                    def_t = "Instruction" if k == "instruction" else "Execution Log"
                    t = kwargs.get("title", args[0] if len(args) > 0 else def_t)
                    if t in self._panels and t not in aux_titles:
                        aux_titles.append(t)

                for t in list(self._panels.keys()):
                    tl = t.lower()
                    if ("lesson" in tl or "instruction" in tl or "log" in tl) and t not in aux_titles:
                        aux_titles.append(t)

                # Ensure Lesson Note is second from bottom and Execution Log is at the very bottom
                aux_titles.sort(key=lambda t: 1 if "log" in t.lower() else 0)

                workflow_titles = [t for t in self._panels.keys() if t not in aux_titles]
                first_active = workflow_titles[0] if workflow_titles else (aux_titles[0] if aux_titles else None)

                # 1. Main calculation workflow navigation buttons
                for title in workflow_titles:
                    self._buttons[title] = gr.Button(
                        title, 
                        variant="primary" if title == first_active else "secondary",
                        elem_classes=["sidebar-nav-btn", "sidebar-workflow-btn"],
                    )

                # 2. Divider line and section header separating calculation workflow from auxiliary panels
                if aux_titles:
                    gr.HTML("""<div class="sidebar-divider"></div><div class="sidebar-section-title">Reference & Logs</div>""")

                    # 3. Auxiliary buttons: Lesson Note (second from bottom), Execution Log (bottom)
                    for title in aux_titles:
                        self._buttons[title] = gr.Button(
                            title, 
                            variant="primary" if title == first_active else "secondary",
                            elem_classes=["sidebar-nav-btn", "sidebar-aux-btn"],
                        )
  
            def switch_panel(name):
                # Synchronize Pixia -> PDFget (rambda, energy, 1D data if available)
                if hasattr(self, "_build_items") and "pixia" in self._build_items and "pdfget" in self._build_items:
                    try:
                        px_item = self._build_items["pixia"]
                        px_m = px_item[2].get("module", px_item[1][0] if len(px_item[1]) > 0 else None)
                        pg_item = self._build_items["pdfget"]
                        pg_m = pg_item[2].get("module", pg_item[1][0] if len(pg_item[1]) > 0 else None)
                        if px_m is not None and pg_m is not None:
                            if hasattr(pg_m, "sync_from_pixia"):
                                pg_m.sync_from_pixia(px_m, copy_params_only=(getattr(px_m, "tt1d", None) is None))
                            elif "rambda" in px_m.par and "rambda" in pg_m.par and px_m["rambda"] is not None:
                                pg_m["rambda"] = px_m["rambda"]
                    except Exception:
                        pass

                # Synchronize PDF reduction parameters (qmax, qmin, rambda, energy) to simulation
                if hasattr(self, "_build_items") and "pdfget" in self._build_items and "simulation" in self._build_items:
                    try:
                        p_item = self._build_items["pdfget"]
                        pdf_m = p_item[2].get("module", p_item[1][0] if len(p_item[1]) > 0 else None)
                        s_item = self._build_items["simulation"]
                        sim_m = s_item[2].get("module", s_item[1][0] if len(s_item[1]) > 0 else None)
                        if pdf_m is not None and sim_m is not None:
                            if hasattr(sim_m, "sync_from_pdfget"):
                                sim_m.sync_from_pdfget(pdf_m, auto_range=False)
                            else:
                                for qk in ["qmax", "qmin", "rambda", "energy"]:
                                    if qk in pdf_m.par and qk in sim_m.par and pdf_m[qk] is not None:
                                        sim_m[qk] = pdf_m[qk]
                    except Exception:
                        pass

                upd_panels = ()
                upd_btns = ()
                for key in self._panels.keys():
                    upd_panels += (gr.update(visible=key == name),)
                    upd_btns += (gr.update(variant="primary" if key == name else "secondary"),)
                return upd_panels + upd_btns

            for name, btn in self._buttons.items():
                btn.click(
                    fn=switch_panel,
                    inputs=[gr.State(name)],
                    outputs=list(self._panels.values()) + list(self._buttons.values())
                )


    def add_instruction_panel(self, *args, **kwargs):
        """
        Adds an instruction panel to the UI.
        """
        from .panels.instruction import add_panel
        self._build_items["instruction"] = [add_panel, args, kwargs]

    def add_system_panel(self, *args, **kwargs):
        """
        Adds a system panel to the UI.
        """
        from .panels.system import add_panel
        self._build_items["system"] = [add_panel, args, kwargs]

    def add_files_panel(self, *args, **kwargs):
        """
        Adds a files panel to the UI.
        """
        from .panels.files import add_panel
        self._build_items["files"] = [add_panel, args, kwargs]

    def add_phase_panel(self, *args, **kwargs):
        """
        Adds a phase panel to the UI.
        """
        from .panels.phase import add_panel
        self._build_items["phase"] = [add_panel, args, kwargs]

    def add_simulation_panel(self, *args, **kwargs):
        """
        Adds a simulation panel to the UI.
        """
        from .panels.simulation import add_panel
        self._build_items["simulation"] = [add_panel, args, kwargs]

    def add_least_squares_panel(self, *args, **kwargs):
        """
        Adds a least squares panel to the UI.
        """
        from .panels.least_squares import add_panel
        self._build_items["least_squares"] = [add_panel, args, kwargs]

    def add_bayes_panel(self, *args, **kwargs):
        """
        Adds a Bayesian optimization panel to the UI.
        """
        from .panels.bayes import add_panel
        self._build_items["bayes"] = [add_panel, args, kwargs]

    def add_ai_panel(self, *args, **kwargs):
        """
        Adds an AI monitoring panel to the UI.
        """
        from .panels.ai import add_panel
        self._build_items["ai"] = [add_panel, args, kwargs]

    def add_pixia_panel(self, *args, **kwargs):
        """
        Adds a 2D image integration (Pixia) panel to the UI.
        """
        from .panels.pixia import add_panel
        self._build_items["pixia"] = [add_panel, args, kwargs]

    def add_pdfget_panel(self, *args, **kwargs):
        """
        Adds a 1D-to-PDF data reduction (PDFget) panel to the UI.
        """
        from .panels.pdfget import add_panel
        self._build_items["pdfget"] = [add_panel, args, kwargs]

    def add_log_panel(self, *args, **kwargs):
        """
        Adds an execution log viewer panel to inspect _info.log / _error.log.
        """
        from .panels.log_viewer import add_panel
        self._build_items["log_viewer"] = [add_panel, args, kwargs]





    




        