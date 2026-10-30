
def plot_interactive_fit(module):
    """
    Creates a listener function to plot fitting results: observed vs. simulated G(r).

    This function returns an inner `action` function, suitable for a Gradio
    Plot component's update. When `action` is called, it checks if `module.obsy`
    exists. If so, it uses `orochi.view.pdf.interactive.plot` to generate a
    Plotly figure displaying the observed and simulated/fitted G(r) data from
    the `module` (assuming `module.obsx`, `module.obsy`, and `module.simy`
    attributes are available).

    Parameters
    ----------
    module : object
        An object instance with attributes `obsx` (observed x-data), `obsy`
        (observed y-data), and `simy` (simulated y-data). This is typically
        an optimizer instance after a fitting operation.

    Returns
    -------
    function
        An `action` function (`fn` callable) that returns a Plotly figure object
        (`plotly.graph_objects.Figure` or similar) compatible with `gr.Plot`,
        or `None` if `module.obsy` is not available.
    """
    from orochi.view.pdf import interactive as interactive_fig
    def action():
        obsx = getattr(module, "obsx", None)
        obsy = getattr(module, "obsy", None)
        if (
            obsx is None
            or obsy is None
            or len(obsx) == 0
            or len(obsy) == 0
        ):
            return None
        simy = getattr(module, "simy", None)
        if simy is not None and len(simy) > 0:
            fig1 = interactive_fig.plot(
                obsx=obsx,
                obsy=obsy,
                simx=obsx,
                simy=simy,
                number=1,
            )
            return fig1
        return None
    return action

def plot_interactive_sim(module):
    """
    Creates a listener function to plot the simulated G(r) data from a module.

    This function returns an inner `action` function, suitable for a Gradio
    Plot component's update. When `action` is called, it uses
    `orochi.view.pdf.interactive.plot` to generate a Plotly figure showing
    the simulated G(r) data from the `module` (assuming `module.r` and `module.Gr`
    attributes are available).

    Parameters
    ----------
    module : object
        An object instance that has `r` (r-space data) and `Gr` (G(r) values)
        attributes. This is typically a PDF simulator instance after a calculation.

    Returns
    -------
    function
        An `action` function (`fn` callable) that returns a Plotly figure object
        compatible with `gr.Plot`.
    """
    from orochi.view.pdf import interactive as interactive_fig
    def action():
        r = getattr(module, "r", None)
        gr_val = getattr(module, "Gr", None)
        if r is None or gr_val is None or len(r) == 0 or len(gr_val) == 0:
            return None
        fig1 = interactive_fig.plot(simx=r,
                                     simy=gr_val, 
                                     number=1)
        return fig1
    return action


def open_dashboard(module):
    """
    Creates a listener function to open the Optuna dashboard for a module's study.

    This function returns an inner `open_dashboard_action` function, suitable for a
    Gradio Button's `click` event. When `open_dashboard_action` is called, it
    constructs the Optuna storage database URL using the module's `work_dir` and
    `study_name`. It then launches `optuna-dashboard` as a subprocess,
    pauses briefly to allow the dashboard to start, and finally opens the
    dashboard URL (from `module["dashboard_url"]`) in a new web browser tab.
    Error handling is included for `FileNotFoundError` (if `optuna-dashboard`
    is not in PATH) and other exceptions.

    Parameters
    ----------
    module : OrochiBase
        The Orochi module instance (e.g., a Bayesian optimizer) which contains
        `work_dir`, `study_name`, and `dashboard_url` attributes/keys relevant
        for configuring and accessing the Optuna study. It's assumed `module`
        also has a `_logger` for error logging.

    Returns
    -------
    function
        An `open_dashboard_action` function (`fn` callable) that triggers the
        launching and opening of the Optuna dashboard. It returns `None`.
    """
    def open_dashboard_action(): # Renamed to avoid conflict with outer scope
        import subprocess, webbrowser, time
        # Assuming module has these parameters set correctly for Optuna

        dashboard_command = ["optuna-dashboard", module.storage]
        try:
            # Using DEVNULL for stdout/stderr to prevent dashboard logs from cluttering main console
            dashboard_process = subprocess.Popen(dashboard_command,
                                                 stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
            # Give the dashboard a moment to start
            time.sleep(5)
            webbrowser.open_new_tab(module["dashboard_url"])
        except FileNotFoundError:
            module._logger.error("optuna-dashboard command not found. Is Optuna dashboard installed and in PATH?")
        except Exception as e:
            module._logger.error(f"Failed to open Optuna dashboard: {e}")
        return None # No direct Gradio output
    return open_dashboard_action


def plot_interactive_pixia(module):
    """Creates a listener returning a Plotly figure of the integrated 1D I(2theta) and dummy baseline."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    def action():
        if getattr(module, "tt1d", None) is None or getattr(module, "i1d", None) is None:
            return None
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Integrated 1D Profile I(2θ)", "Dummy-Frame Baseline B_det(2θ)"),
        )
        fig.add_trace(
            go.Scatter(
                x=module.tt1d,
                y=module.i1d,
                mode="lines",
                line=dict(color="royalblue", width=1.8),
                name="I(2θ)",
            ),
            row=1,
            col=1,
        )
        if getattr(module, "d1d", None) is not None:
            fig.add_trace(
                go.Scatter(
                    x=module.tt1d,
                    y=module.d1d,
                    mode="lines",
                    line=dict(color="darkorange", width=1.8),
                    name="Dummy baseline",
                ),
                row=1,
                col=2,
            )
        fig.update_xaxes(title_text="2θ / deg", row=1, col=1)
        fig.update_yaxes(title_text="Intensity / a.u.", row=1, col=1)
        fig.update_xaxes(title_text="2θ / deg", row=1, col=2)
        fig.update_yaxes(title_text="Dummy Baseline / a.u.", row=1, col=2)
        fig.update_layout(height=500, plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        return fig

    return action


def plot_interactive_pixia_2d(module):
    """Creates a listener returning an interactive Plotly 2D detector image plot with zoom, pan, hover coordinates, and mask overlay."""
    import os
    import numpy as np
    import plotly.graph_objects as go

    def action(current_mode="Sample + Mask Overlay"):
        mode = current_mode if current_mode else "Sample + Mask Overlay"

        pixx = int(module["pixx"]) if module["pixx"] is not None else 2048
        pixy = int(module["pixy"]) if module["pixy"] is not None else 2048
        x0 = float(module["x0"]) if module["x0"] is not None else pixx / 2.0
        y0 = float(module["y0"]) if module["y0"] is not None else pixy / 2.0

        def _get_param_path(key):
            try:
                if key in getattr(module, "par", {}):
                    v = module[key]
                    if isinstance(v, (list, tuple)):
                        valid = [str(x) for x in v if x and os.path.exists(str(x))]
                        return valid if valid else None
                    if v and os.path.exists(str(v)):
                        return str(v)
            except Exception:
                pass
            return None

        # Retrieve or read appropriate image
        img = None
        if "Sample" in mode:
            if isinstance(getattr(module, "sample", None), np.ndarray):
                img = module.sample
            else:
                s_path = _get_param_path("sample_file")
                if s_path:
                    try:
                        module.read_file(s_path, target="sample")
                        if isinstance(getattr(module, "sample", None), np.ndarray):
                            img = module.sample
                    except Exception as e:
                        print(f"Notice: read sample image: {e}")
        elif "Background" in mode:
            if isinstance(getattr(module, "background", None), np.ndarray):
                img = module.background
            else:
                bg_path = _get_param_path("background_file")
                if bg_path:
                    try:
                        module.read_file(bg_path, target="background")
                        if isinstance(getattr(module, "background", None), np.ndarray):
                            img = module.background
                    except Exception as e:
                        print(f"Notice: read background image: {e}")
        elif "Mask" in mode:
            if isinstance(getattr(module, "mask", None), np.ndarray):
                img = module.mask
            elif isinstance(getattr(module, "mask_image", None), np.ndarray):
                img = module.mask_image
            else:
                m_path = _get_param_path("mask_file")
                if m_path:
                    try:
                        module.read_file(m_path, target="mask")
                        if isinstance(getattr(module, "mask_image", None), np.ndarray):
                            img = module.mask_image
                    except Exception as e:
                        print(f"Notice: read mask image: {e}")
            if img is None:
                try:
                    img = module.get_mask()
                except Exception:
                    pass

        fig = go.Figure()

        sec_summary = getattr(module, "get_azimuthal_mode_summary", lambda: "")()

        if img is None or not isinstance(img, np.ndarray):
            fig.add_shape(type="line", x0=x0, x1=x0, y0=0, y1=pixy, line=dict(color="#ef4444", dash="dash", width=1.5))
            fig.add_shape(type="line", x0=0, x1=pixx, y0=y0, y1=y0, line=dict(color="#ef4444", dash="dash", width=1.5))
            bmin_val = getattr(module, "par", {}).get("betamin", {}).get("value", None)
            bmax_val = getattr(module, "par", {}).get("betamax", {}).get("value", None)
            if bmin_val is not None and bmax_val is not None:
                bmin_list = np.atleast_1d(bmin_val)
                bmax_list = np.atleast_1d(bmax_val)
                is_full = len(bmin_list) == 1 and np.isclose(bmin_list[0], -180.0) and np.isclose(bmax_list[0], 180.0)
                if not is_full:
                    diag_r = np.sqrt(pixx**2 + pixy**2)
                    for bmin, bmax in zip(bmin_list, bmax_list):
                        rmin_rad = np.radians(bmin)
                        rmax_rad = np.radians(bmax)
                        fig.add_shape(type="line", x0=x0, x1=x0 + diag_r * np.cos(rmin_rad), y0=y0, y1=y0 + diag_r * np.sin(rmin_rad), line=dict(color="#f59e0b", dash="dash", width=1.4))
                        fig.add_shape(type="line", x0=x0, x1=x0 + diag_r * np.cos(rmax_rad), y0=y0, y1=y0 + diag_r * np.sin(rmax_rad), line=dict(color="#f59e0b", dash="dash", width=1.4))

            fig.add_trace(go.Scatter(
                x=[x0],
                y=[y0],
                mode="markers+text",
                marker=dict(color="#ef4444", size=8, line=dict(color="white", width=1.2)),
                text=[f"Center ({x0:.1f}, {y0:.1f})"],
                textposition="top right",
                name="Beam Center",
                hoverinfo="text",
            ))
            fig.add_annotation(
                x=pixx / 2.0,
                y=pixy / 2.0,
                text="<b>No 2D image loaded yet.</b><br>Please select or upload a 2D detector image above.",
                showarrow=False,
                font=dict(size=14, color="#64748b"),
            )
            fig.update_xaxes(title_text="Pixel X (detector)", range=[0, pixx], showgrid=True, gridcolor="#e2e8f0")
            fig.update_yaxes(title_text="Pixel Y (detector)", range=[0, pixy], scaleanchor="x", scaleratio=1, showgrid=True, gridcolor="#e2e8f0")
            title_text = f"2D Detector View (No Image) | {sec_summary}" if sec_summary else "2D Detector View (No Image Loaded)"
            fig.update_layout(
                title=dict(text=title_text, x=0.03),
                height=680,
                margin=dict(l=65, r=40, t=50, b=55),
                plot_bgcolor="#f8fafc",
                paper_bgcolor="white",
                showlegend=False,
            )
            return fig

        actual_pixy, actual_pixx = img.shape
        step = 2 if max(actual_pixy, actual_pixx) >= 2048 else 1
        sub = img[::step, ::step]
        ny, nx = sub.shape
        x_coords = np.arange(nx) * step
        y_coords = np.arange(ny) * step

        if "Mask (Binary" in mode:
            fig.add_trace(go.Heatmap(
                x=x_coords,
                y=y_coords,
                z=sub,
                colorscale="gray",
                zmin=0,
                zmax=1,
                colorbar=dict(title="Mask (0/1)"),
                hovertemplate="<b>X</b>: %{x}<br><b>Y</b>: %{y}<br><b>Mask</b>: %{z}<extra></extra>",
            ))
        else:
            log_img = np.log10(np.clip(sub, 0, None) + 1.0)
            pos_vals = log_img[log_img > 0]
            vmin = float(np.percentile(pos_vals, 2.0)) if len(pos_vals) > 0 else 0.0
            vmax = float(np.percentile(pos_vals, 99.8)) if len(pos_vals) > 0 else 1.0

            fig.add_trace(go.Heatmap(
                x=x_coords,
                y=y_coords,
                z=log_img,
                text=sub,
                hovertext=sub,
                colorscale="Viridis",
                zmin=vmin,
                zmax=vmax,
                colorbar=dict(title="log<sub>10</sub>(Int)"),
                hovertemplate="<b>X</b>: %{x}<br><b>Y</b>: %{y}<br><b>Intensity</b>: %{text:.1f}<br><b>log<sub>10</sub>(I)</b>: %{z:.2f}<extra></extra>",
            ))

            if "Overlay" in mode:
                mask_arr = getattr(module, "mask", None)
                if mask_arr is None and isinstance(getattr(module, "mask_image", None), np.ndarray):
                    mask_arr = module.mask_image
                if mask_arr is None:
                    try:
                        mask_arr = module.get_mask()
                    except Exception:
                        pass
                if mask_arr is not None and isinstance(mask_arr, np.ndarray) and mask_arr.shape == img.shape:
                    mask_sub = mask_arr[::step, ::step]
                    mask_overlay = np.where(mask_sub == 0, 1.0, np.nan)
                    fig.add_trace(go.Heatmap(
                        x=x_coords,
                        y=y_coords,
                        z=mask_overlay,
                        colorscale=[[0, "rgba(239, 68, 68, 0.45)"], [1, "rgba(239, 68, 68, 0.45)"]],
                        showscale=False,
                        hoverinfo="skip",
                    ))

        # Overlay Beam Center Crosshair and reticle
        fig.add_shape(type="line", x0=x0, x1=x0, y0=0, y1=actual_pixy, line=dict(color="#00ffff", dash="dash", width=1.5))
        fig.add_shape(type="line", x0=0, x1=actual_pixx, y0=y0, y1=y0, line=dict(color="#00ffff", dash="dash", width=1.5))
        fig.add_trace(go.Scatter(
            x=[x0],
            y=[y0],
            mode="markers+text",
            marker=dict(color="#fbbf24", size=9, line=dict(color="black", width=1.5)),
            text=[f"Center ({x0:.1f}, {y0:.1f})"],
            textposition="top right",
            textfont=dict(color="#fbbf24", size=12),
            name="Beam Center",
            hoverinfo="text",
        ))

        # Overlay Integration Sector boundaries (betamin/betamax) if present
        bmin_val = getattr(module, "par", {}).get("betamin", {}).get("value", None)
        bmax_val = getattr(module, "par", {}).get("betamax", {}).get("value", None)
        if bmin_val is not None and bmax_val is not None:
            bmin_list = np.atleast_1d(bmin_val)
            bmax_list = np.atleast_1d(bmax_val)
            is_full = len(bmin_list) == 1 and np.isclose(bmin_list[0], -180.0) and np.isclose(bmax_list[0], 180.0)
            if not is_full:
                diag_r = np.sqrt(actual_pixx**2 + actual_pixy**2)
                for bmin, bmax in zip(bmin_list, bmax_list):
                    rmin_rad = np.radians(bmin)
                    rmax_rad = np.radians(bmax)
                    fig.add_shape(type="line", x0=x0, x1=x0 + diag_r * np.cos(rmin_rad), y0=y0, y1=y0 + diag_r * np.sin(rmin_rad), line=dict(color="#f59e0b", dash="dash", width=1.4))
                    fig.add_shape(type="line", x0=x0, x1=x0 + diag_r * np.cos(rmax_rad), y0=y0, y1=y0 + diag_r * np.sin(rmax_rad), line=dict(color="#f59e0b", dash="dash", width=1.4))

        fig.update_xaxes(title_text="Pixel X (detector)", range=[0, actual_pixx], showgrid=False)
        fig.update_yaxes(title_text="Pixel Y (detector)", range=[0, actual_pixy], scaleanchor="x", scaleratio=1, showgrid=False)
        title_text = f"2D Detector View: {mode} | {sec_summary}" if sec_summary else f"2D Detector View: {mode}"
        fig.update_layout(
            title=dict(text=title_text, x=0.03),
            height=680,
            margin=dict(l=65, r=40, t=50, b=55),
            plot_bgcolor="black",
            paper_bgcolor="white",
            showlegend=False,
        )
        return fig

    return action


def plot_interactive_pdfget(module):
    """Creates a listener returning a 2x2 Plotly figure of I_norm(Q), S(Q), F(Q), and G(r)."""
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    def action():
        data = getattr(module, "data", {})
        if "r" not in data or "Gr" not in data:
            return None
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "High-Q Form Factor Normalization",
                "Structure Factor S(Q)",
                "Reduced Structure Factor F(Q)",
                "Reduced PDF G(r)",
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.10,
        )
        q = data.get("q")
        if q is not None:
            if "i_normalized" in data:
                fig.add_trace(
                    go.Scatter(x=q, y=data["i_normalized"], mode="lines", name="I_coh(Q)", line=dict(color="royalblue")),
                    row=1,
                    col=1,
                )
            if "f_sq_ave" in data:
                fig.add_trace(
                    go.Scatter(x=q, y=data["f_sq_ave"], mode="lines", name="<|f|^2>", line=dict(color="crimson", dash="dash")),
                    row=1,
                    col=1,
                )
            if "sq" in data:
                fig.add_trace(
                    go.Scatter(x=q, y=data["sq"], mode="lines", name="S(Q)", line=dict(color="teal")),
                    row=1,
                    col=2,
                )
        if "fq" in data:
            q_fq = data["q"] if "q" in data and len(data["q"]) == len(data["fq"]) else data.get("q_fq")
            if q_fq is not None and len(q_fq) == len(data["fq"]):
                fig.add_trace(
                    go.Scatter(x=q_fq, y=data["fq"], mode="lines", name="F(Q)", line=dict(color="purple")),
                    row=2,
                    col=1,
                )
        r = data["r"]
        gr = data["Gr"]
        rmin = module["rmin"] if module["rmin"] is not None else 0.0
        rmax = module["rmax"] if module["rmax"] is not None else float(r[-1])
        mask = (r >= rmin) & (r <= rmax)
        fig.add_trace(
            go.Scatter(x=r[mask], y=gr[mask], mode="lines", name="G(r)", line=dict(color="firebrick")),
            row=2,
            col=2,
        )
        fig.update_xaxes(title_text="Q / Å⁻¹", row=1, col=1)
        fig.update_xaxes(title_text="Q / Å⁻¹", row=1, col=2)
        fig.update_xaxes(title_text="Q / Å⁻¹", row=2, col=1)
        fig.update_xaxes(title_text="r / Å", row=2, col=2)
        fig.update_yaxes(title_text="G(r) / Å⁻²", row=2, col=2)
        fig.update_layout(height=650, plot_bgcolor="white", paper_bgcolor="white")
        return fig

    return action


def plot_interactive_pixia_diagnostics(module):
    """Creates a listener returning interactive diagnostic plots for geometry calibration verification:
    - Horizontal symmetry (+X vs -X) for beam center x0 and tiltx.
    - Vertical symmetry (+Y vs -Y) for beam center y0 and tilty.
    - Overlay of theoretical standard calibrant Bragg reflections (Ni, CeO2) for distance and wavelength.
    """
    import os
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    def action(standard="Ni", unit="2θ (deg)", width=10.0, mode="pn"):
        # Check if sample/background is available
        if getattr(module, "sample", None) is None:
            s_file = getattr(module, "par", {}).get("sample_file", {}).get("value")
            if s_file and os.path.exists(str(s_file)):
                try:
                    module.read()
                    module.bg_subtraction()
                except Exception:
                    pass

        if getattr(module, "sample", None) is None:
            fig = go.Figure()
            fig.add_annotation(
                text="<b>No 2D image loaded.</b><br>Please load a standard calibration sample (e.g. Ni, CeO2) on Tab 1.",
                showarrow=False,
                font=dict(size=14, color="#64748b"),
            )
            fig.update_layout(height=600, plot_bgcolor="#f8fafc", paper_bgcolor="white")
            return fig

        mode_str = str(mode).lower()
        if "xp-yp" in mode_str:
            mode_key = "xp-yp"
        elif "xn-yp" in mode_str:
            mode_key = "xn-yp"
        elif "xp-yn" in mode_str:
            mode_key = "xp-yn"
        elif "xn-yn" in mode_str:
            mode_key = "xn-yn"
        else:
            mode_key = "pn"

        try:
            prof = module.get_directional_profiles(
                width=float(width),
                standard=str(standard).lower(),
                mode=mode_key,
            )
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"<b>Failed to compute diagnostic profiles:</b><br>{e}",
                showarrow=False,
                font=dict(size=13, color="#ef4444"),
            )
            fig.update_layout(height=600, plot_bgcolor="#f8fafc", paper_bgcolor="white")
            return fig

        is_radius = "Radius" in str(unit)
        x_vals = prof["radius_mm"] if is_radius else prof["tt_deg"]
        x_label = "Detector Radial Distance R (mm)" if is_radius else "Scattering Angle 2θ (deg)"

        std_name = prof["std_name"].upper()
        bragg_x = prof["std_bragg_radius"] if is_radius else prof["std_bragg_tt"]
        bragg_d = prof["std_bragg_d"]

        if mode_key == "pn":
            diff_h_score = prof.get("diff_h", 0.0)
            diff_v_score = prof.get("diff_v", 0.0)

            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.12,
                subplot_titles=(
                    f"[H-Sym] Horizontal Symmetry: +X (Right) vs -X (Left)  [x0={module['x0']:.1f}, tiltx={module['tiltx']:.4f} deg | Asymmetry Score: {diff_h_score:.2e}]",
                    f"[V-Sym] Vertical Symmetry: +Y (Top) vs -Y (Bottom)  [y0={module['y0']:.1f}, tilty={module['tilty']:.4f} deg | Asymmetry Score: {diff_v_score:.2e}]",
                ),
            )

            # Row 1: Horizontal Symmetry
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=prof["i_pos_x"],
                    mode="lines",
                    line=dict(color="#2563eb", width=2.0),
                    name="+X (Right, β ~ 0°)",
                    hovertemplate="<b>+X</b>: %{x:.3f}" + (" mm" if is_radius else "°") + "<br>Int: %{y:.1f}<extra></extra>",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=prof["i_neg_x"],
                    mode="lines",
                    line=dict(color="#dc2626", width=2.0, dash="dash"),
                    name="-X (Left, β ~ 180°)",
                    hovertemplate="<b>-X</b>: %{x:.3f}" + (" mm" if is_radius else "°") + "<br>Int: %{y:.1f}<extra></extra>",
                ),
                row=1,
                col=1,
            )

            # Row 2: Vertical Symmetry
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=prof["i_pos_y"],
                    mode="lines",
                    line=dict(color="#0891b2", width=2.0),
                    name="+Y (Top, β ~ 90°)",
                    hovertemplate="<b>+Y</b>: %{x:.3f}" + (" mm" if is_radius else "°") + "<br>Int: %{y:.1f}<extra></extra>",
                ),
                row=2,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=prof["i_neg_y"],
                    mode="lines",
                    line=dict(color="#d97706", width=2.0, dash="dash"),
                    name="-Y (Bottom, β ~ -90°)",
                    hovertemplate="<b>-Y</b>: %{x:.3f}" + (" mm" if is_radius else "°") + "<br>Int: %{y:.1f}<extra></extra>",
                ),
                row=2,
                col=1,
            )

            max_y1 = float(max(np.nanmax(prof["i_pos_x"]), np.nanmax(prof["i_neg_x"]))) * 1.05
            max_y2 = float(max(np.nanmax(prof["i_pos_y"]), np.nanmax(prof["i_neg_y"]))) * 1.05

        else:
            # Corner orthogonal modes
            if mode_key == "xp-yp":
                s1_k, s1_l, s1_c = "i_pos_x", "+X (Right, β ~ 0°)", "#2563eb"
                s2_k, s2_l, s2_c = "i_pos_y", "+Y (Top, β ~ 90°)", "#0891b2"
                sd_k, sd_l, sd_c = "i_diag_tr", "Diagonal TR (β ~ 45°)", "#8b5cf6"
                diff_score = prof.get("diff_xp_yp", 0.0)
                sub1_title = f"[Orthogonal] Sectors: +X (Right) vs +Y (Top)  [Tilt/Distance Cross-Check | Mismatch: {diff_score:.2e}]"
                sub2_title = f"[Diag-TR] Diagonal Sector (TR, β ~ 45°) & Cross Difference |+X - +Y|"
            elif mode_key == "xn-yp":
                s1_k, s1_l, s1_c = "i_neg_x", "-X (Left, β ~ 180°)", "#dc2626"
                s2_k, s2_l, s2_c = "i_pos_y", "+Y (Top, β ~ 90°)", "#0891b2"
                sd_k, sd_l, sd_c = "i_diag_tl", "Diagonal TL (β ~ 135°)", "#8b5cf6"
                diff_score = prof.get("diff_xn_yp", 0.0)
                sub1_title = f"[Orthogonal] Sectors: -X (Left) vs +Y (Top)  [Tilt/Distance Cross-Check | Mismatch: {diff_score:.2e}]"
                sub2_title = f"[Diag-TL] Diagonal Sector (TL, β ~ 135°) & Cross Difference |-X - +Y|"
            elif mode_key == "xp-yn":
                s1_k, s1_l, s1_c = "i_pos_x", "+X (Right, β ~ 0°)", "#2563eb"
                s2_k, s2_l, s2_c = "i_neg_y", "-Y (Bottom, β ~ -90°)", "#d97706"
                sd_k, sd_l, sd_c = "i_diag_br", "Diagonal BR (β ~ -45°)", "#8b5cf6"
                diff_score = prof.get("diff_xp_yn", 0.0)
                sub1_title = f"[Orthogonal] Sectors: +X (Right) vs -Y (Bottom)  [Tilt/Distance Cross-Check | Mismatch: {diff_score:.2e}]"
                sub2_title = f"[Diag-BR] Diagonal Sector (BR, β ~ -45°) & Cross Difference |+X - -Y|"
            else:  # xn-yn
                s1_k, s1_l, s1_c = "i_neg_x", "-X (Left, β ~ 180°)", "#dc2626"
                s2_k, s2_l, s2_c = "i_neg_y", "-Y (Bottom, β ~ -90°)", "#d97706"
                sd_k, sd_l, sd_c = "i_diag_bl", "Diagonal BL (β ~ -135°)", "#8b5cf6"
                diff_score = prof.get("diff_xn_yn", 0.0)
                sub1_title = f"[Orthogonal] Sectors: -X (Left) vs -Y (Bottom)  [Tilt/Distance Cross-Check | Mismatch: {diff_score:.2e}]"
                sub2_title = f"[Diag-BL] Diagonal Sector (BL, β ~ -135°) & Cross Difference |-X - -Y|"

            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.12,
                subplot_titles=(sub1_title, sub2_title),
            )

            # Row 1: Orthogonal Overlay
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=prof[s1_k],
                    mode="lines",
                    line=dict(color=s1_c, width=2.0),
                    name=s1_l,
                    hovertemplate=f"<b>{s1_l.split()[0]}</b>: %{{x:.3f}}" + (" mm" if is_radius else "°") + "<br>Int: %{y:.1f}<extra></extra>",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=prof[s2_k],
                    mode="lines",
                    line=dict(color=s2_c, width=2.0, dash="dash"),
                    name=s2_l,
                    hovertemplate=f"<b>{s2_l.split()[0]}</b>: %{{x:.3f}}" + (" mm" if is_radius else "°") + "<br>Int: %{y:.1f}<extra></extra>",
                ),
                row=1,
                col=1,
            )

            # Row 2: Diagonal Sector & Cross Difference
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=prof[sd_k],
                    mode="lines",
                    line=dict(color=sd_c, width=2.0),
                    name=sd_l,
                    hovertemplate=f"<b>{sd_l.split()[0]}</b>: %{{x:.3f}}" + (" mm" if is_radius else "°") + "<br>Int: %{y:.1f}<extra></extra>",
                ),
                row=2,
                col=1,
            )
            cross_diff = np.abs(prof[s1_k] - prof[s2_k])
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=cross_diff,
                    mode="lines",
                    line=dict(color="#ea580c", width=1.5, dash="dot"),
                    name=f"|Diff| ({s1_l.split()[0]} - {s2_l.split()[0]})",
                    hovertemplate="<b>|Diff|</b>: %{x:.3f}" + (" mm" if is_radius else "°") + "<br>Diff: %{y:.1f}<extra></extra>",
                ),
                row=2,
                col=1,
            )

            max_y1 = float(max(np.nanmax(prof[s1_k]), np.nanmax(prof[s2_k]))) * 1.05
            max_y2 = float(max(np.nanmax(prof[sd_k]), np.nanmax(cross_diff))) * 1.05

        if len(bragg_x) > 0:
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="lines",
                    line=dict(color="#059669", dash="dot", width=1.5),
                    name=f"{std_name} Bragg Refl. (Theor.)",
                ),
                row=1,
                col=1,
            )
            for bx, bd in zip(bragg_x, bragg_d):
                fig.add_shape(
                    type="line",
                    x0=bx,
                    x1=bx,
                    y0=0,
                    y1=max_y1,
                    line=dict(color="#059669", dash="dot", width=1.2),
                    row=1,
                    col=1,
                )
                fig.add_shape(
                    type="line",
                    x0=bx,
                    x1=bx,
                    y0=0,
                    y1=max_y2,
                    line=dict(color="#059669", dash="dot", width=1.2),
                    row=2,
                    col=1,
                )

        fig.update_xaxes(title_text=x_label, row=2, col=1, showgrid=True, gridcolor="#e2e8f0")
        fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", row=1, col=1)
        fig.update_yaxes(title_text="Intensity (counts)", row=1, col=1, showgrid=True, gridcolor="#e2e8f0")
        fig.update_yaxes(title_text="Intensity (counts)", row=2, col=1, showgrid=True, gridcolor="#e2e8f0")

        mode_header = f"Orthogonal Diagnostic ({mode_key.upper()})" if mode_key != "pn" else "Symmetry Diagnostic (+-X, +-Y)"
        fig.update_layout(
            title=dict(
                text=f"<b>Geometry Calibration Verification & {mode_header}</b> | Standard: {std_name} (Distance={module['distance']:.2f} mm, lambda={module['rambda']:.5f} Å)",
                x=0.03,
            ),
            height=660,
            margin=dict(l=65, r=40, t=70, b=55),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=0.98),
            hovermode="x unified",
        )
        return fig

    return action


