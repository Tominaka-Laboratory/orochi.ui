"""Helper utilities for formatting optimization metrics, parameters, and logs for the Orochi GUI."""

import os
import numpy as np

LATEX_DELIMITERS = [
    {"left": "$$", "right": "$$", "display": True},
    {"left": "$", "right": "$", "display": False},
]


def _get_param_label(address, module=None):
    """Generates human-readable labels, short identifiers, and physical units for parameters."""
    clean = str(address).replace("@0_1/", "").replace("@0_0/", "").replace("@", "")
    parts = clean.split("/")
    base_name = parts[0]
    idx = None
    for p in reversed(parts[1:]):
        if p.isdigit():
            idx = int(p)
            break

    symbol_str = ""
    if idx is not None and module is not None:
        try:
            phase = getattr(module, "phase", module)
            symbols = getattr(phase, "symbol", None)
            if symbols is None and hasattr(phase, "__getitem__"):
                try:
                    symbols = phase["symbol"]
                except Exception:
                    pass
            if symbols is not None and idx < len(symbols):
                symbol_str = f" ({symbols[idx]})"
        except Exception:
            pass

    unit = ""
    if "lattice" in base_name:
        lat_names = ["a", "b", "c", "alpha", "beta", "gamma"]
        lat_units = [" Å", " Å", " Å", "°", "°", "°"]
        if idx is not None and idx < len(lat_names):
            label = f"Lattice constant *{lat_names[idx]}*"
            unit = lat_units[idx]
        else:
            label = "Lattice constant"
            unit = " Å"
    elif "adp" in base_name:
        label = f"Thermal ADP *U*<sub>iso</sub>{symbol_str}"
        unit = " Å²"
    elif "scale" in base_name:
        label = "Scale factor"
        unit = ""
    elif "qdamp" in base_name:
        label = "Resolution damping *Q*<sub>damp</sub>"
        unit = " Å⁻¹"
    elif "qbroad" in base_name:
        label = "Peak broadening *Q*<sub>broad</sub>"
        unit = " Å⁻¹"
    elif "delta2" in base_name:
        label = "Dynamic correlation δ₂"
        unit = ""
    elif "delta1" in base_name:
        label = "Dynamic correlation δ₁"
        unit = ""
    elif "xyz" in base_name or "pos" in base_name:
        coords = ["x", "y", "z"]
        coord_name = coords[idx] if (idx is not None and idx < len(coords)) else ""
        label = f"Coordinate {coord_name}{symbol_str}"
        unit = ""
    elif "occ" in base_name:
        label = f"Site occupancy{symbol_str}"
        unit = ""
    else:
        label = base_name.replace("_", " ").title()
        unit = ""

    clean_short = base_name if idx is None else f"{base_name}[{idx}]"
    return label, clean_short, unit


def format_least_squares_results(module):
    """Extracts Rw, R^2, chi^2, refined parameters table, and diagnostic report from LeastSquaresOptimizer.

    Parameters
    ----------
    module : LeastSquaresOptimizer
        Optimizer instance.

    Returns
    -------
    tuple of (str, str, str, str, str)
        rw_str, r2_str, chi2_str, params_table_md, log_str
    """
    rw = getattr(module, "Rw", None)
    if rw is not None and not np.isnan(rw) and rw != 0.0:
        rw_str = f"{rw * 100.0:.3f}% ({rw:.5f})"
    else:
        rw_str = "Not yet evaluated"

    scores = getattr(module, "best_scores", {}) or {}
    r2 = scores.get("rsquared", None)
    r2_str = f"{r2 * 100.0:.2f}%" if r2 is not None and not np.isnan(r2) else "-"
    chi2 = scores.get("chisqr", None)
    chi2_str = f"{chi2:.2f}" if chi2 is not None and not np.isnan(chi2) else "-"

    bp = getattr(module, "best_params", {}) or {}
    if not bp:
        work_dir = getattr(module, "work_dir", None)
        study_name = getattr(module, "study_name", None)
        if work_dir and study_name:
            bp_file = os.path.join(work_dir, "opt_res", study_name, "best_params.json")
            if os.path.isfile(bp_file):
                try:
                    import json
                    with open(bp_file, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                        bp = saved.get("best_params", {})
                        if not scores:
                            scores = saved.get("best_scores", {})
                            if r2_str == "-" and "rsquared" in scores:
                                r2_str = f"{scores['rsquared'] * 100.0:.2f}%"
                            if chi2_str == "-" and "chisqr" in scores:
                                chi2_str = f"{scores['chisqr']:.2f}"
                except Exception:
                    pass

    if bp:
        # Resolve initial values mapping from bp or fit_params or lmfit res
        init_map = {}
        for k, v in bp.items():
            if "/init" in k:
                base = k.replace("/init", "")
                init_map[base] = v

        fit_params = getattr(module, "fit_params", {}) or {}
        for fit_name, p_info in fit_params.items():
            addr = p_info.get("address", "")
            base = addr.replace("/value", "")
            if base and base not in init_map:
                init_map[base] = p_info.get("value", None)

        res_params = getattr(getattr(module, "res", None), "params", {}) or {}
        for p_name, p_obj in res_params.items():
            if p_name in fit_params:
                base = fit_params[p_name].get("address", "").replace("/value", "")
                if base and base not in init_map and hasattr(p_obj, "init_value"):
                    init_map[base] = p_obj.init_value

        params_map = {}
        for k, v in bp.items():
            if "/value" in k:
                base = k.replace("/value", "")
                std_key = k.replace("/value", "/std")
                std_val = bp.get(std_key, None)
                init_val = init_map.get(base, None)
                params_map[base] = (v, std_val, init_val)
            elif "/std" not in k and not k.endswith("_std") and "/init" not in k:
                if k not in params_map:
                    std_val = bp.get(f"{k}/std", bp.get(f"{k}_std", None))
                    init_val = init_map.get(k, None)
                    params_map[k] = (v, std_val, init_val)

        lines = [
            "| Parameter | Initial Value | Refined Value | Uncertainty (±1σ) | Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for key, (val, std, init_val) in params_map.items():
            mod_target = None
            if fit_params:
                for fn, p_info in fit_params.items():
                    if p_info.get("address", "").startswith(key):
                        mod_target = p_info.get("module", None)
                        break

            label, clean_short, unit = _get_param_label(key, mod_target)

            init_str = f"{init_val:.5f}{unit}" if isinstance(init_val, (float, np.floating)) else (str(init_val) if init_val is not None else "-")
            val_str = f"{val:.5f}{unit}" if isinstance(val, (float, np.floating)) else str(val)
            if std is not None and not np.isnan(std):
                if std < 0.0001:
                    std_str = f"± {std:.5e}{unit}"
                else:
                    std_str = f"± {std:.5f}{unit}"
            else:
                std_str = "-"

            status = "Converged"
            lines.append(f"| **{label}** (`{clean_short}`) | `{init_str}` | **{val_str}** | `{std_str}` | {status} |")

        table_md = "\n".join(lines)
    else:
        # Pre-fit preview: gather current values and bounds from module simulators
        if hasattr(module, "initialize_modules_and_params") and getattr(module, "simulators", None):
            try:
                module.initialize_modules_and_params()
            except Exception:
                pass

        fit_params = getattr(module, "fit_params", {}) or {}
        if fit_params:
            lines = [
                "| Parameter | Initial Value | Search Bounds [Min, Max] | Status |",
                "| :--- | :--- | :--- | :--- |",
            ]
            for fit_name, p_info in fit_params.items():
                addr = p_info.get("address", fit_name)
                val = p_info.get("value", None)
                p_min = p_info.get("min", None)
                p_max = p_info.get("max", None)
                mod_target = p_info.get("module", None)
                label, clean_short, unit = _get_param_label(addr, mod_target)

                val_str = f"{val:.5f}{unit}" if isinstance(val, (float, np.floating)) else (str(val) if val is not None else "-")
                if isinstance(p_min, (float, np.floating)) and isinstance(p_max, (float, np.floating)):
                    bounds_str = f"[{p_min:.5f}, {p_max:.5f}]{unit}"
                else:
                    bounds_str = "-"
                lines.append(f"| **{label}** (`{clean_short}`) | `{val_str}` | `{bounds_str}` | Ready to Fit |")

            lines.append("\n_Click **'Fit'** to run bounded least-squares refinement._")
            table_md = "\n".join(lines)
        else:
            table_md = "_Click **'Fit'** to run bounded least-squares refinement and view optimized parameters._"

    res = getattr(module, "res", None)
    if res is not None and hasattr(res, "fit_report"):
        try:
            log_str = res.fit_report()
        except Exception:
            log_str = str(res)
    else:
        fit_min = getattr(module, "par", {}).get("fit_min", {}).get("value", "N/A")
        fit_max = getattr(module, "par", {}).get("fit_max", {}).get("value", "N/A")
        log_str = (
            f"Optimizer: {getattr(module, 'name', 'LeastSquares')}\n"
            f"Study name: {getattr(module, 'study_name', 'N/A')}\n"
            f"Fit interval: r in [{fit_min}, {fit_max}] Å\n"
            f"Status: Ready"
        )

    return rw_str, r2_str, chi2_str, table_md, log_str


def format_bayes_results(module):
    """Extracts best trial score, trials count, parameters, and study summary from BayesOptimizer.

    Parameters
    ----------
    module : BayesOptimizer
        Bayesian optimization instance.

    Returns
    -------
    tuple of (str, str, str, str)
        best_score_str, trials_str, params_table_md, log_str
    """
    study = getattr(module, "study", None)
    if study is not None and hasattr(study, "best_value"):
        try:
            best_val = float(study.best_value)
            best_score_str = f"Rw = {best_val * 100.0:.3f}% ({best_val:.5f})"
            trials_str = f"Trial #{study.best_trial.number} (Total: {len(study.trials)} trials)"
            bp = study.best_params
            lines = [
                "| Optimized Parameter | Best Value |",
                "| :--- | :--- |",
            ]
            for k, v in bp.items():
                v_str = f"{v:.5f}" if isinstance(v, (float, np.floating)) else str(v)
                lines.append(f"| **{k}** | `{v_str}` |")
            params_table_md = "\n".join(lines)
            log_str = (
                f"Bayesian Study: {getattr(study, 'study_name', 'N/A')}\n"
                f"Total trials: {len(study.trials)}\n"
                f"Best trial value: {best_val:.6f}\n"
                f"Best params: {study.best_params}\n"
            )
        except Exception as e:
            best_score_str = "-"
            trials_str = "-"
            params_table_md = f"Error reading study: {e}"
            log_str = str(e)
    else:
        best_score_str = "Not yet run"
        trials_str = "0 trials"
        params_table_md = "_Click **'Fit'** to run Bayesian optimization._"
        log_str = "Bayesian optimization is ready to execute."

    return best_score_str, trials_str, params_table_md, log_str


import datetime
import json


def _json_serializable(obj):
    """Recursively converts NumPy types and containers into standard JSON serializable types."""
    if obj is None:
        return None
    if isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (list, tuple)):
        return [_json_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _json_serializable(v) for k, v in obj.items()}
    return str(obj)


def _resolve_filepath(filepath, default_name, work_dir=None, module=None):
    """Resolves relative or absolute path and ensures parent directories exist."""
    if not filepath or not str(filepath).strip():
        filepath = default_name
    filepath = str(filepath).strip()
    if not os.path.isabs(filepath):
        base = work_dir or getattr(module, "work_dir", None) or os.getcwd()
        filepath = os.path.join(base, filepath)
    filepath = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    return filepath


def export_least_squares_json(module, filepath=None, work_dir=None):
    """Saves least-squares optimization results as a comprehensive JSON file."""
    study = getattr(module, "study_name", "least_squares") or "least_squares"
    default_name = f"{study}_fit_result.json"
    target_path = _resolve_filepath(filepath, default_name, work_dir=work_dir, module=module)

    rw = getattr(module, "Rw", None)
    rw_val = float(rw) if rw is not None and not np.isnan(rw) else None

    scores = getattr(module, "best_scores", {}) or {}
    bp = getattr(module, "best_params", {}) or {}
    res = getattr(module, "res", None)

    fit_report_str = None
    if res is not None and hasattr(res, "fit_report"):
        try:
            fit_report_str = res.fit_report()
        except Exception:
            pass

    structured_params = {}
    if bp:
        for k, v in bp.items():
            if "/value" in k:
                base = k.replace("/value", "")
                std_key = k.replace("/value", "/std")
                init_key = k.replace("/value", "/init")
                init_val = bp.get(init_key, None)
                structured_params[base] = {
                    "initial_value": float(init_val) if isinstance(init_val, (float, np.floating)) else init_val,
                    "value": float(v) if isinstance(v, (float, np.floating)) else v,
                    "std": float(bp[std_key]) if std_key in bp and bp[std_key] is not None and not np.isnan(bp[std_key]) else None,
                }
            elif "/std" not in k and not k.endswith("_std") and "/init" not in k and k not in structured_params:
                std_k = f"{k}/std" if f"{k}/std" in bp else f"{k}_std"
                std_v = bp.get(std_k, None)
                init_k = f"{k}/init" if f"{k}/init" in bp else f"{k}_init"
                init_v = bp.get(init_k, None)
                structured_params[k] = {
                    "initial_value": float(init_v) if isinstance(init_v, (float, np.floating)) else init_v,
                    "value": float(v) if isinstance(v, (float, np.floating)) else v,
                    "std": float(std_v) if std_v is not None and not np.isnan(std_v) else None,
                }

    simulators_info = []
    sims = getattr(module, "simulators", []) or []
    for s in sims:
        s_info = {
            "name": getattr(s, "name", "Simulator"),
            "scale": getattr(s, "par", {}).get("scale", {}).get("value", None),
            "qdamp": getattr(s, "par", {}).get("qdamp", {}).get("value", None),
            "qbroad": getattr(s, "par", {}).get("qbroad", {}).get("value", None),
            "delta1": getattr(s, "par", {}).get("delta1", {}).get("value", None),
            "delta2": getattr(s, "par", {}).get("delta2", {}).get("value", None),
            "qdepend": getattr(s, "par", {}).get("qdepend", {}).get("value", None),
        }
        if hasattr(s, "phase") and s.phase is not None:
            p = s.phase
            s_info["phase"] = {
                "name": getattr(p, "name", "Phase"),
                "space_group": getattr(p, "space_group", None),
                "lattice": getattr(p, "par", {}).get("lattice", {}).get("value", None),
                "adp": getattr(p, "par", {}).get("adp", {}).get("value", None),
            }
        simulators_info.append(s_info)

    data = {
        "study_name": study,
        "timestamp": datetime.datetime.now().isoformat(),
        "optimizer": getattr(module, "name", module.__class__.__name__),
        "metrics": {
            "Rw": rw_val,
            "Rw_percent": rw_val * 100.0 if rw_val is not None else None,
            "rsquared": float(scores.get("rsquared")) if "rsquared" in scores else None,
            "chisqr": float(scores.get("chisqr")) if "chisqr" in scores else None,
            "redchi": float(scores.get("adj")) if "adj" in scores else (float(scores.get("redchi")) if "redchi" in scores else None),
            "nvarys": getattr(res, "nvarys", None) if res else None,
            "ndata": getattr(res, "ndata", None) if res else (len(module.obsx) if getattr(module, "obsx", None) is not None else None),
            "nfev": getattr(res, "nfev", None) if res else None,
        },
        "fit_interval": {
            "fit_min": getattr(module, "par", {}).get("fit_min", {}).get("value", None),
            "fit_max": getattr(module, "par", {}).get("fit_max", {}).get("value", None),
        },
        "refined_parameters": structured_params,
        "best_params_raw": _json_serializable(bp),
        "best_scores_raw": _json_serializable(scores),
        "simulators": _json_serializable(simulators_info),
        "fit_report": fit_report_str,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(_json_serializable(data), f, indent=2, ensure_ascii=False)

    return target_path


def export_bayes_json(module, filepath=None, work_dir=None):
    """Saves Bayesian optimization summary, trials, and best parameters as JSON."""
    study_name = getattr(module, "study_name", "bayes") or "bayes"
    default_name = f"{study_name}_opt_result.json"
    target_path = _resolve_filepath(filepath, default_name, work_dir=work_dir, module=module)

    study = getattr(module, "study", None)
    best_val = float(study.best_value) if study and hasattr(study, "best_value") else None
    best_trial_num = study.best_trial.number if study and hasattr(study, "best_trial") else None
    best_params = study.best_params if study and hasattr(study, "best_params") else {}

    trials_list = []
    if study and hasattr(study, "trials"):
        for t in study.trials:
            trials_list.append({
                "number": t.number,
                "value": float(t.value) if t.value is not None else None,
                "params": t.params,
                "state": str(t.state),
            })

    data = {
        "study_name": study_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "optimizer": getattr(module, "name", module.__class__.__name__),
        "best_trial": {
            "number": best_trial_num,
            "objective_value": best_val,
            "Rw_percent": best_val * 100.0 if best_val is not None else None,
            "params": best_params,
        },
        "total_trials": len(trials_list),
        "trials": trials_list,
        "fit_interval": {
            "fit_min": getattr(module, "par", {}).get("fit_min", {}).get("value", None),
            "fit_max": getattr(module, "par", {}).get("fit_max", {}).get("value", None),
        },
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(_json_serializable(data), f, indent=2, ensure_ascii=False)

    return target_path


def export_pdfget_json(module, filepath=None, work_dir=None):
    """Saves PDF data reduction parameters and summary as JSON."""
    study_name = getattr(module, "study_name", "pdfget") or "pdfget"
    default_name = f"{study_name}_reduction_result.json"
    target_path = _resolve_filepath(filepath, default_name, work_dir=work_dir, module=module)

    params = {}
    for k, v in getattr(module, "par", {}).items():
        if isinstance(v, dict) and "value" in v:
            params[k] = v["value"]

    data_summary = {}
    mod_data = getattr(module, "data", {}) or {}
    for key in ["q_fq", "fq", "r_gr", "gr", "sq"]:
        if key in mod_data and mod_data[key] is not None and len(mod_data[key]) > 0:
            arr = np.array(mod_data[key])
            data_summary[key] = {
                "points": len(arr),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
            }

    data = {
        "study_name": study_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "module": "PDFget",
        "parameters": _json_serializable(params),
        "data_summary": data_summary,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(_json_serializable(data), f, indent=2, ensure_ascii=False)

    return target_path


def export_pixia_json(module, filepath=None, work_dir=None):
    """Saves Pixia 2D-to-1D integration geometry and summary as JSON."""
    study_name = getattr(module, "study_name", "pixia") or "pixia"
    default_name = f"{study_name}_integration_result.json"
    target_path = _resolve_filepath(filepath, default_name, work_dir=work_dir, module=module)

    params = {}
    for k, v in getattr(module, "par", {}).items():
        if isinstance(v, dict) and "value" in v:
            params[k] = v["value"]

    tt1d = getattr(module, "tt1d", None)
    n_points = len(tt1d) if tt1d is not None else 0

    data = {
        "study_name": study_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "module": "Pixia",
        "sample_file": module["sample_file"] if "sample_file" in getattr(module, "par", {}) else getattr(module, "sample_file", None),
        "background_file": module["background_file"] if "background_file" in getattr(module, "par", {}) else getattr(module, "background_file", None),
        "mask_file": module["mask_file"] if "mask_file" in getattr(module, "par", {}) else getattr(module, "mask_file", None),
        "parameters": _json_serializable(params),
        "integration_summary": {
            "points_count": n_points,
            "ttmin": float(np.min(tt1d)) if tt1d is not None and len(tt1d) > 0 else None,
            "ttmax": float(np.max(tt1d)) if tt1d is not None and len(tt1d) > 0 else None,
        },
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(_json_serializable(data), f, indent=2, ensure_ascii=False)

    return target_path


def export_simulation_json(module, filepath=None, work_dir=None):
    """Saves PDF simulation parameters and simulated curve summary as JSON."""
    study_name = getattr(module, "study_name", "pdfsim") or "pdfsim"
    default_name = f"{study_name}_simulation_result.json"
    target_path = _resolve_filepath(filepath, default_name, work_dir=work_dir, module=module)

    params = {}
    for k, v in getattr(module, "par", {}).items():
        if isinstance(v, dict) and "value" in v:
            params[k] = v["value"]

    r = getattr(module, "r", None)

    data = {
        "study_name": study_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "module": "Simulator",
        "parameters": _json_serializable(params),
        "data_summary": {
            "r_points": len(r) if r is not None else 0,
            "rmin": float(np.min(r)) if r is not None and len(r) > 0 else None,
            "rmax": float(np.max(r)) if r is not None and len(r) > 0 else None,
        },
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(_json_serializable(data), f, indent=2, ensure_ascii=False)

    return target_path


