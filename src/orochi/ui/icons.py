import base64
import os

_icon_path = os.path.join(os.path.dirname(__file__), "orochi_icon.png")
if os.path.exists(_icon_path):
    with open(_icon_path, "rb") as _f:
        ICON_BASE64 = base64.b64encode(_f.read()).decode("utf-8")
    logo_svg = f'<img src="data:image/png;base64,{ICON_BASE64}" class="sidebar-logo-icon" alt="Orochi Logo" />'
else:
    ICON_BASE64 = ""
    logo_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="sidebar-logo-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path>
        <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path>
    </svg>"""
