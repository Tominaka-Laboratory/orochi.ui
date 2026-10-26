import os
import glob
from datetime import datetime
import gradio as gr
from .utils.fit_reporter import LATEX_DELIMITERS


def find_available_logs(work_dir):
    """Finds all available log files in work_dir and nested directories."""
    if not work_dir or not os.path.isdir(work_dir):
        work_dir = os.getcwd()

    found = []
    for f in ["_info.log", "_error.log"]:
        p = os.path.join(work_dir, f)
        if os.path.isfile(p):
            found.append(f)

    for root, _, files in os.walk(work_dir):
        for f in files:
            if f.endswith(".log"):
                rel = os.path.relpath(os.path.join(root, f), work_dir).replace("\\", "/")
                if rel not in found:
                    found.append(rel)

    return found if found else ["_info.log", "_error.log"]


def _read_log_file(work_dir, log_filename, line_count=200, filter_text=""):
    """Reads and filters the tail of a specified log file in work_dir."""
    if not work_dir or not os.path.isdir(work_dir):
        work_dir = os.getcwd()

    log_path = os.path.join(work_dir, log_filename)
    if not os.path.isfile(log_path):
        candidates = glob.glob(os.path.join(work_dir, "**", os.path.basename(log_filename)), recursive=True)
        if candidates:
            log_path = candidates[0]
        else:
            return f"Log file '{log_filename}' not found in:\n{work_dir}\n\n(No optimization or workflow has written to this log file yet.)", "Status: File not found"

    try:
        stat = os.stat(log_path)
        size_kb = stat.st_size / 1024.0
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if filter_text:
            query = filter_text.strip().lower()
            lines = [line for line in lines if query in line.lower()]

        if line_count and line_count > 0 and len(lines) > line_count:
            selected_lines = lines[-line_count:]
        else:
            selected_lines = lines

        content = "".join(selected_lines)
        if not content:
            content = f"Log file '{log_filename}' is empty or no lines matched filter '{filter_text}'."

        info_status = f"File: {log_path} | Size: {size_kb:.1f} KB | Modified: {mtime} | Total Lines: {len(lines)}"
        return content, info_status
    except Exception as e:
        return f"Error reading log file {log_path}: {e}", f"Error: {e}"


def add_panel(
    self,
    title="Execution Log",
    header=None,
    footer=None,
    tips: bool = False,
):
    """Creates a Gradio panel for live inspection of Orochi execution logs (_info.log / _error.log)."""
    is_first = len(self._panels) == 0
    with gr.Column(visible=is_first) as new_panel:
        if header:
            gr.Markdown(header, latex_delimiters=LATEX_DELIMITERS)

        gr.Markdown(
            "## Orochi Execution & Diagnostic Logs\n"
            "View live terminal output, optimization convergence logs, and error traces directly from your `work_dir`.",
            latex_delimiters=LATEX_DELIMITERS,
        )

        wdir = getattr(self, "work_dir", os.getcwd())
        available_logs = find_available_logs(wdir)
        default_log = available_logs[0] if available_logs else "_info.log"

        with gr.Row():
            log_choice = gr.Dropdown(
                label="Log File",
                choices=available_logs,
                value=default_log,
                interactive=True,
                scale=2,
            )
            line_slider = gr.Dropdown(
                label="Show Tail Lines",
                choices=["50", "100", "200", "500", "All"],
                value="200",
                interactive=True,
                scale=1,
            )
            filter_box = gr.Textbox(
                label="Filter Keyword (e.g. 'Rw', 'Error')",
                value="",
                placeholder="Optional filter...",
                interactive=True,
                scale=2,
            )
            refresh_btn = gr.Button("Refresh Log", variant="primary", scale=1)

        def get_log_content(choice, lines_str, filt):
            wdir = getattr(self, "work_dir", os.getcwd())
            n_lines = 0 if lines_str == "All" else int(lines_str)
            return _read_log_file(wdir, choice, line_count=n_lines, filter_text=filt)

        init_content, init_status = get_log_content("_info.log", "200", "")

        log_display = gr.Textbox(
            label="Log Content",
            value=init_content,
            interactive=False,
            lines=22,
            elem_id="execution-log-display",
        )

        status_bar = gr.Markdown(f"*{init_status}*", latex_delimiters=LATEX_DELIMITERS)

        def refresh_action(choice, lines_str, filt):
            content, st = get_log_content(choice, lines_str, filt)
            return content, f"*{st}*"

        refresh_btn.click(
            fn=refresh_action,
            inputs=[log_choice, line_slider, filter_box],
            outputs=[log_display, status_bar],
        )
        log_choice.change(
            fn=refresh_action,
            inputs=[log_choice, line_slider, filter_box],
            outputs=[log_display, status_bar],
        )
        line_slider.change(
            fn=refresh_action,
            inputs=[log_choice, line_slider, filter_box],
            outputs=[log_display, status_bar],
        )
        filter_box.submit(
            fn=refresh_action,
            inputs=[log_choice, line_slider, filter_box],
            outputs=[log_display, status_bar],
        )

        if footer:
            gr.Markdown(footer, latex_delimiters=LATEX_DELIMITERS)
        self._panels[title] = new_panel
