CSS = """
/* ------------------------------------------------
   1. Color Palette (Light / Dark Auto-Switching)
   ------------------------------------------------ */
/* Light mode (default) */
:root {
    --sidebar-width: 250px;
    --sidebar-bg-start: #f8fafc;
    --sidebar-bg-end: #e2e8f0;
    --sidebar-text: #1e293b;
    --sidebar-icon: #475569;
    --sidebar-border: rgba(0, 0, 0, 0.1);
    --brand-accent: #0284c7; /* Light mode accent (blue) */
    --brand-glow: rgba(2, 132, 199, 0.2);
    --font-family-serif: 'Times New Roman', Times, serif;
    --font-family-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Dark mode */
.dark {
    --sidebar-bg-start: #1a1e3a;
    --sidebar-bg-end: #3b206f;
    --sidebar-text: #f0f0f0;
    --sidebar-icon: #ffffff;
    --sidebar-border: rgba(255, 255, 255, 0.1);
    --brand-accent: #00e0ff; /* Dark mode accent (cyan) */
    --brand-glow: rgba(59, 32, 111, 0.5);
}

/* ------------------------------------------------
   2. Utilities & Layout Adjustments
   ------------------------------------------------ */
/* Vertical alignment for login message */
.login-text {
    display: flex;
    align-items: center;
    height: 100%;
    margin: 0 !important;
}

/* Multi-line header support for Dataframes */
.gradio-container table thead th span {
    white-space: pre-line !important;
    line-height: 1.2;
}

.no-gap {
    gap: 0px !important; 
    margin-top: -5px !important;
}

/* ------------------------------------------------
   3. Sidebar Styling
   ------------------------------------------------ */
/* Sidebar container */
#my-sidebar {
    background: linear-gradient(to bottom, var(--sidebar-bg-start), var(--sidebar-bg-end)) !important;
    border-right: 1px solid var(--sidebar-border) !important;
    color: var(--sidebar-text);
    transition: background 0.3s, color 0.3s;
}

/* Make inner Gradio wrapper backgrounds transparent */
#my-sidebar > div,
#my-sidebar .gradio-container,
#my-sidebar .contain {
    background-color: transparent !important;
    background: transparent !important;
}

/* ------------------------------------------------
   4. Logo, Header, and Icons
   ------------------------------------------------ */
.sidebar-logo {
    display: flex;
    align-items: center;
    padding: 0 20px 20px 20px;
    border-bottom: 1px solid var(--sidebar-border);
    margin-bottom: 20px;
}
.sidebar-logo-text {
    font-family: var(--font-family-serif);
    font-size: 1.6rem;
    font-weight: bold;
    color: var(--sidebar-text);
}
.sidebar-logo-nexus {
    font-family: var(--font-family-sans);
    font-size: 1.4rem;
    color: var(--sidebar-text);
    opacity: 0.8;
    margin-left: 5px;
}
.sidebar-logo-icon {
    margin-right: 10px;
    width: 32px;
    height: 32px;
    object-fit: contain;
    vertical-align: middle;
    border-radius: 4px;
}

.section-header-row {
    display: flex;
    justify-content: flex-start; 
    align-items: center;
    cursor: default;             
    user-select: none;          
    border-bottom: 1px solid var(--sidebar-border);
    margin-top: 10px;
    padding: 0 0 5px 0;
}
.section-header-title {
    display: flex;
    align-items: center;
    font-size: 1.2rem;
    font-weight: bold;
    color: var(--sidebar-text);
    padding: 5px 15px;
}
.section-header-title-icon {
    margin-right: 10px;
    width: 20px;
    height: 20px;
    fill: var(--sidebar-icon);
}
.section-header-details-icon {
    width: 24px;
    height: 24px;
    opacity: 0.7;
    margin-right: 15px;
    fill: var(--sidebar-icon);
}

/* ------------------------------------------------
   5. Button Styling
   ------------------------------------------------ */
#my-sidebar button {
    font-family: var(--font-family-sans);
    border-radius: 6px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 8px 15px !important;
    padding-left: 42px !important;
    margin: 1px 0 !important;
    font-size: 1rem;
    transition: background 0.3s, box-shadow 0.3s, color 0.3s;
    box-shadow: none !important;
}

/* Secondary button (unselected menu item) */
#my-sidebar button.secondary {
    background-color: transparent !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: var(--sidebar-text) !important;
}
#my-sidebar button.secondary:hover {
    background-color: rgba(128, 128, 128, 0.1) !important;
}

/* Primary button (selected menu item) */
#my-sidebar button.primary {
    background: linear-gradient(45deg, var(--sidebar-bg-end), var(--sidebar-bg-start)) !important;
    border: 1px solid var(--sidebar-border) !important;
    color: var(--sidebar-text) !important;
    box-shadow: 0 0 10px var(--brand-glow) !important;
}
#my-sidebar button.primary .gr-button-icon-container {
    color: var(--brand-accent) !important; 
    filter: drop-shadow(0 0 3px var(--brand-accent)) !important; 
}

/* Sidebar Divider & Section Header for Auxiliary / Reference Panels */
.sidebar-divider {
    border-top: 1px solid var(--sidebar-border);
    margin: 18px 12px 10px 12px;
    opacity: 0.6;
}
.sidebar-section-title {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 700;
    color: #64748b;
    padding: 2px 16px 6px 16px;
    user-select: none;
}
.dark .sidebar-section-title {
    color: #94a3b8;
}

/* Auxiliary menu buttons (Lesson Note, Execution Log) */
#my-sidebar button.sidebar-aux-btn {
    font-size: 0.92rem !important;
    padding-left: 38px !important;
    opacity: 0.88;
}
#my-sidebar button.sidebar-aux-btn.secondary {
    color: #64748b !important;
    background-color: transparent !important;
}
.dark #my-sidebar button.sidebar-aux-btn.secondary {
    color: #94a3b8 !important;
}
#my-sidebar button.sidebar-aux-btn.secondary:hover {
    color: var(--sidebar-text) !important;
    background-color: rgba(100, 116, 139, 0.12) !important;
    opacity: 1.0;
}
#my-sidebar button.sidebar-aux-btn.primary {
    border-left: 3px solid #64748b !important;
    color: var(--sidebar-text) !important;
    opacity: 1.0;
}

/* ------------------------------------------------
   6. Scientific UI Polish & Readability Enhancements
   ------------------------------------------------ */
/* Prominent primary buttons (Fit, Integrate, Simulate, Refresh) */
.gradio-container button.primary {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: none !important;
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.25) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.2s ease !important;
}
.gradio-container button.primary:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35) !important;
    transform: translateY(-1px);
}
.gradio-container button.primary:active {
    transform: translateY(0);
}

/* Monospaced metric inputs (Rw, R^2, chi^2) for high scientific readability */
.gradio-container .gr-textbox input[readonly] {
    font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace !important;
    font-weight: 600 !important;
    color: #1e293b !important;
    background-color: #f8fafc !important;
}
.dark .gradio-container .gr-textbox input[readonly] {
    color: #f1f5f9 !important;
    background-color: #0f172a !important;
}

/* Polished markdown tables for parameters and results */
.gradio-container table {
    border-collapse: separate !important;
    border-spacing: 0 !important;
    width: 100% !important;
    margin: 12px 0 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}
.dark .gradio-container table {
    border-color: #334155 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}
.gradio-container table th {
    background: #f1f5f9 !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid #cbd5e1 !important;
    text-align: left !important;
}
.dark .gradio-container table th {
    background: #1e293b !important;
    color: #f8fafc !important;
    border-bottom: 1px solid #334155 !important;
}
.gradio-container table td {
    padding: 9px 14px !important;
    font-size: 0.9rem !important;
    border-bottom: 1px solid #f1f5f9 !important;
}
.dark .gradio-container table td {
    border-bottom: 1px solid #1e293b !important;
}
.gradio-container table tr:last-child td {
    border-bottom: none !important;
}
.gradio-container table tr:hover td {
    background: #f8fafc !important;
}
.dark .gradio-container table tr:hover td {
    background: rgba(30, 41, 59, 0.5) !important;
}

/* Polished Accordions */
.gradio-container .gr-accordion {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
.dark .gradio-container .gr-accordion {
    border-color: #334155 !important;
}

/* ------------------------------------------------
   7. Typography & KaTeX Math in Headings
   ------------------------------------------------ */
/* Prevent KaTeX math expressions inside Markdown headings from shrinking to body text size */
.gradio-container h1 .katex,
.gradio-container h1 span.katex,
.gradio-container .prose h1 .katex,
.gradio-container .md h1 .katex {
    font-size: 1em !important;
}
.gradio-container h2 .katex,
.gradio-container h2 span.katex,
.gradio-container .prose h2 .katex,
.gradio-container .md h2 .katex {
    font-size: 1em !important;
}
.gradio-container h3 .katex,
.gradio-container h3 span.katex,
.gradio-container .prose h3 .katex,
.gradio-container .md h3 .katex {
    font-size: 1em !important;
}
.gradio-container h4 .katex,
.gradio-container h4 span.katex,
.gradio-container .prose h4 .katex,
.gradio-container .md h4 .katex {
    font-size: 1em !important;
}
.gradio-container h1 .katex .mathnormal,
.gradio-container h1 .katex .mathrm,
.gradio-container h2 .katex .mathnormal,
.gradio-container h2 .katex .mathrm,
.gradio-container h3 .katex .mathnormal,
.gradio-container h3 .katex .mathrm {
    font-weight: 700 !important;
}

/* ------------------------------------------------
   8. Compact File Upload Boxes (Half-Height)
   ------------------------------------------------ */
.gradio-container .compact-file,
.gradio-container .compact-file .file-upload,
.gradio-container .compact-file [data-testid="file-upload"] {
    min-height: 70px !important;
    max-height: 105px !important;
    padding: 6px 12px !important;
}
.gradio-container .compact-file .upload-container,
.gradio-container .compact-file .file-preview-holder {
    min-height: 55px !important;
    max-height: 90px !important;
    padding: 4px 8px !important;
}
.gradio-container .compact-file svg {
    width: 22px !important;
    height: 22px !important;
}
.gradio-container .compact-file .file-name {
    font-size: 0.85rem !important;
}

/* ------------------------------------------------
   9. Fullscreen Plot Viewer
   ------------------------------------------------ */
.orochi-fullscreen-btn {
    position: absolute;
    top: 8px;
    right: 12px;
    z-index: 50;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 11px;
    font-size: 0.8rem;
    font-weight: 600;
    font-family: var(--font-family-sans, sans-serif);
    color: #334155;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(6px);
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    user-select: none;
}

.orochi-fullscreen-btn:hover {
    color: #0284c7;
    background: #ffffff;
    border-color: #0284c7;
    box-shadow: 0 3px 8px rgba(2, 132, 199, 0.25);
    transform: translateY(-1px);
}

.dark .orochi-fullscreen-btn {
    color: #e2e8f0;
    background: rgba(30, 41, 59, 0.92);
    border-color: #475569;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.dark .orochi-fullscreen-btn:hover {
    color: #38bdf8;
    background: #1e293b;
    border-color: #38bdf8;
    box-shadow: 0 3px 8px rgba(56, 189, 248, 0.35);
}

.orochi-fullscreen-btn.active {
    background: #ef4444 !important;
    color: #ffffff !important;
    border-color: #dc2626 !important;
    box-shadow: 0 2px 10px rgba(239, 68, 68, 0.45) !important;
}

.orochi-fullscreen-btn.active:hover {
    background: #dc2626 !important;
}

/* Position Plotly modebar palette neatly UNDER the Fullscreen button */
.block .modebar-container,
.gradio-plot .modebar-container {
    top: 42px !important;
    right: 14px !important;
    z-index: 45 !important;
}

.block .modebar,
.gradio-plot .modebar {
    display: flex !important;
    flex-direction: column !important;
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(4px) !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 6px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    padding: 2px !important;
}

.dark .block .modebar,
.dark .gradio-plot .modebar {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: #475569 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
}

.block .modebar-group,
.gradio-plot .modebar-group {
    display: flex !important;
    flex-direction: column !important;
    padding: 1px 0 !important;
    margin: 0 !important;
    background: transparent !important;
}

.block .modebar-btn,
.gradio-plot .modebar-btn {
    margin: 1px 0 !important;
    padding: 3px !important;
    border-radius: 4px !important;
}

.block .modebar-btn:hover,
.gradio-plot .modebar-btn:hover {
    background-color: rgba(2, 132, 199, 0.12) !important;
}

.dark .block .modebar-btn:hover,
.dark .gradio-plot .modebar-btn:hover {
    background-color: rgba(56, 189, 248, 0.2) !important;
}

/* Fullscreen Active Container Styling (Native & Fallback) */
:fullscreen.block,
:fullscreen.gradio-plot,
.block.orochi-fs-active,
.gradio-plot.orochi-fs-active {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    max-width: 100vw !important;
    max-height: 100vh !important;
    z-index: 999999 !important;
    background: #ffffff !important;
    padding: 14px 20px 20px 20px !important;
    box-sizing: border-box !important;
    border-radius: 0 !important;
    margin: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}

.dark :fullscreen.block,
.dark :fullscreen.gradio-plot,
.dark .block.orochi-fs-active,
.dark .gradio-plot.orochi-fs-active {
    background: #0b0f19 !important;
}

:fullscreen .orochi-fullscreen-btn,
.orochi-fs-active .orochi-fullscreen-btn {
    top: 14px;
    right: 22px;
    z-index: 1000000;
}

:fullscreen .modebar-container,
.orochi-fs-active .modebar-container {
    right: 24px !important;
    top: 50px !important;
    z-index: 1000000 !important;
}

:fullscreen .js-plotly-plot,
:fullscreen [data-testid="plotly"],
.orochi-fs-active .js-plotly-plot,
.orochi-fs-active [data-testid="plotly"] {
    width: 100% !important;
    height: calc(100vh - 35px) !important;
    flex: 1 1 auto !important;
}
"""