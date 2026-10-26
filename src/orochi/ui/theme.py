"""Custom Gradio themes for the Orochi scientific GUI framework.

Provides high-contrast, clean, scientific blue themes that overcome
the washed-out, borderless rendering of 'Soft' while replacing the
amber/orange palette of 'Citrus' with a modern, elegant sapphire/slate aesthetic.
"""

import gradio as gr
from gradio.themes.utils import colors, fonts, sizes


def create_orochi_theme(
    primary_hue=colors.blue,
    secondary_hue=colors.cyan,
    neutral_hue=colors.slate,
    font_family=None,
    font_mono=None,
):
    """Constructs a custom Orochi Gradio theme with crisp borders and high-contrast typography.

    Parameters
    ----------
    primary_hue : colors.Color, optional
        Primary color palette for action buttons, highlights, focus rings, and sliders.
        Defaults to colors.blue.
    secondary_hue : colors.Color, optional
        Secondary accent color. Defaults to colors.cyan.
    neutral_hue : colors.Color, optional
        Neutral palette for backgrounds, cards, and text. Defaults to colors.slate.
    font_family : list, optional
        Font family list. Defaults to GoogleFont('Inter') and system sans-serif.
    font_mono : list, optional
        Monospace font family list. Defaults to GoogleFont('JetBrains Mono') and ui-monospace.

    Returns
    -------
    gr.themes.ThemeClass
        Configured Gradio theme instance.
    """
    if font_family is None:
        font_family = [
            fonts.GoogleFont("Inter"),
            "system-ui",
            "-apple-system",
            "BlinkMacSystemFont",
            "Segoe UI",
            "Roboto",
            "sans-serif",
        ]

    if font_mono is None:
        font_mono = [
            fonts.GoogleFont("JetBrains Mono"),
            "ui-monospace",
            "SFMono-Regular",
            "Menlo",
            "Monaco",
            "Consolas",
            "monospace",
        ]

    theme = gr.themes.Default(
        primary_hue=primary_hue,
        secondary_hue=secondary_hue,
        neutral_hue=neutral_hue,
        font=font_family,
        font_mono=font_mono,
        radius_size=sizes.radius_md,
        spacing_size=sizes.spacing_md,
        text_size=sizes.text_md,
    )

    theme = theme.set(
        # Page body
        body_background_fill="*neutral_50",
        body_background_fill_dark="*neutral_950",
        body_text_color="*neutral_900",
        body_text_color_dark="*neutral_100",
        # Blocks & Cards (Crisp 1px border like Citrus, but sleek and clean)
        block_background_fill="white",
        block_background_fill_dark="*neutral_900",
        block_border_width="1px",
        block_border_width_dark="1px",
        block_border_color="*neutral_200",
        block_border_color_dark="*neutral_800",
        block_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.03)",
        block_shadow_dark="0 1px 3px 0 rgba(0, 0, 0, 0.3)",
        block_label_text_color="*neutral_700",
        block_label_text_color_dark="*neutral_300",
        block_label_text_weight="600",
        block_title_text_color="*neutral_900",
        block_title_text_color_dark="*neutral_100",
        # Input Controls (Clearly delineated with bright surface and blue focus ring)
        input_background_fill="white",
        input_background_fill_dark="*neutral_900",
        input_border_width="1px",
        input_border_color="*neutral_300",
        input_border_color_dark="*neutral_700",
        input_border_color_focus="*primary_500",
        input_border_color_focus_dark="*primary_400",
        input_shadow_focus="0 0 0 3px rgba(37, 99, 235, 0.18)",
        # Primary Action Buttons (Vibrant sapphire blue with crisp white text)
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_500",
        button_primary_background_fill_dark="*primary_600",
        button_primary_background_fill_hover_dark="*primary_500",
        button_primary_text_color="white",
        button_primary_text_color_dark="white",
        button_primary_border_color="transparent",
        # Secondary Buttons
        button_secondary_background_fill="*neutral_100",
        button_secondary_background_fill_dark="*neutral_800",
        button_secondary_background_fill_hover="*neutral_200",
        button_secondary_background_fill_hover_dark="*neutral_700",
        button_secondary_text_color="*neutral_800",
        button_secondary_text_color_dark="*neutral_100",
        button_secondary_border_color="*neutral_200",
        button_secondary_border_color_dark="*neutral_700",
        # Data Tables
        table_border_color="*neutral_200",
        table_border_color_dark="*neutral_800",
        table_even_background_fill="*neutral_50",
        table_even_background_fill_dark="*neutral_900",
        table_row_focus="*primary_50",
        table_row_focus_dark="*primary_950",
        # Checkboxes and Sliders
        checkbox_background_color_selected="*primary_600",
        checkbox_background_color_selected_dark="*primary_500",
        checkbox_border_color_selected="*primary_600",
        checkbox_border_color_selected_dark="*primary_500",
        slider_color="*primary_600",
        slider_color_dark="*primary_500",
        # Accordion
        accordion_text_color="*neutral_800",
        accordion_text_color_dark="*neutral_200",
    )

    return theme


# Pre-configured theme variants
OrochiTheme = create_orochi_theme(
    primary_hue=colors.blue,
    secondary_hue=colors.cyan,
    neutral_hue=colors.slate,
)

OrochiOceanTheme = create_orochi_theme(
    primary_hue=colors.sky,
    secondary_hue=colors.teal,
    neutral_hue=colors.slate,
)

OrochiIndigoTheme = create_orochi_theme(
    primary_hue=colors.indigo,
    secondary_hue=colors.blue,
    neutral_hue=colors.slate,
)

THEMES = {
    "orochi": OrochiTheme,
    "orochiblue": OrochiTheme,
    "orochiocean": OrochiOceanTheme,
    "orochiindigo": OrochiIndigoTheme,
}


def get_theme(theme_name: str | gr.themes.ThemeClass | None = "Orochi"):
    """Resolves a theme by name or instance.

    Supports:
    - Custom Orochi themes: 'Orochi', 'OrochiBlue', 'OrochiOcean', 'OrochiIndigo'
    - Built-in Gradio themes: 'Citrus', 'Soft', 'Default', 'Monochrome', 'Ocean', 'Glass'
    - Custom ThemeClass instances passed directly.
    """
    if theme_name is None:
        return OrochiTheme

    if isinstance(theme_name, gr.themes.ThemeClass):
        return theme_name

    if isinstance(theme_name, str):
        key = theme_name.strip().lower()
        if key in THEMES:
            return THEMES[key]

        # Check Gradio built-in themes
        if hasattr(gr.themes, theme_name):
            try:
                return getattr(gr.themes, theme_name)()
            except Exception:
                pass

        # Try case-insensitive matching in gr.themes
        for attr in dir(gr.themes):
            if attr.lower() == key:
                try:
                    return getattr(gr.themes, attr)()
                except Exception:
                    pass

    return OrochiTheme
