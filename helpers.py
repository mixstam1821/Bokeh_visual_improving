# HELPERS


import math, sys
import numpy as np
from bokeh.plotting import figure, show, output_file
from bokeh.models   import ColumnDataSource, HoverTool, Select, CustomJS, Div, GlobalInlineStyleSheet,Span,CrosshairTool
from bokeh.layouts  import column, row

sys.path.insert(0, ".")
from bokeh_anim import anim, anim_pie, anim_scatter
from smooth_tip  import smooth_tip, smooth_tip_multi,smooth_tip_multi_line

output_file("bokeh_anim_examples.html", title="bokeh_anim examples")

def get_gstyle():
	gstyle = GlobalInlineStyleSheet(css=""" html, body, .bk, .bk-root {background-color: #FAE7D3;} """)
	return gstyle

def mystyle(p, cross=False, leg_out = False):
    p.min_border_bottom=60+10; p.min_border_right=60; p.min_border_left=60; p.min_border_top=60
    p.styles = {'margin-top': '20px','margin-left': '20px','border-radius': '10px',
                'box-shadow': '0 3px 7px #7E7E7E','padding': '5px',
                'background-color': 'white','border': '1px solid rgb(194, 192, 192)'}

    p.legend.click_policy = "hide"

    p.toolbar.autohide = True
    p.toolbar_location= "left"
    p.xaxis.minor_tick_line_color = None
    p.yaxis.minor_tick_line_color = None
    p.yaxis.major_tick_line_color = None

    p.xgrid.grid_line_color = None
    p.yaxis.axis_line_color = "white"
    p.outline_line_color = "white"

    # Axis tick labels
    p.xaxis.major_label_text_font_size = "12pt"
    p.yaxis.major_label_text_font_size = "12pt"

    # Axis titles
    p.xaxis.axis_label_text_font_size = "14pt"
    p.yaxis.axis_label_text_font_size = "14pt"

    # Plot title
    p.title.text_font_size = "20pt"
    FONT = "Comic Sans MS"
    CTEXT = "#4F5764"

    p.title.text_font = FONT
    p.title.text_color = CTEXT
    p.axis.axis_label_text_font = FONT
    p.axis.major_label_text_font = FONT
    p.axis.major_label_text_color = CTEXT
    p.axis.axis_label_text_color = CTEXT
    p.legend.label_text_font = FONT
    p.legend.label_text_color = CTEXT
    
    if leg_out:
        p.add_layout(p.legend[0], "right")
        p.legend[0].location="center"
    # Crosshair tool
    if cross:
        span_height = Span(
            dimension="height", line_dash="dashed", line_width=2, line_color="#878787"
        )
        crosshair_tool = CrosshairTool(overlay=span_height)
        p.add_tools(crosshair_tool)


def rmfocus(p, dx=10):
    rmfocusdiv = Div(
        text="",
        width=p.width - dx,
        height=p.height - dx,
        styles={
            "padding": "0px",
            "position": "absolute",
            "top": "20px",
            "left": "20px",
            "border": "2px solid white",
            "background-color": "transparent",
            "pointer-events": "none",
        },
    )
    return rmfocusdiv














# kpi_cards.py
from bokeh.models import Div


def _delta_html(delta: str | None, direction: str) -> str:
    """direction: 'up' | 'down' | 'neutral'"""
    if not delta:
        return ""
    icons = {"up": "▲", "down": "▼", "neutral": "●"}
    colors = {"up": "#3a9e6f", "down": "#c0392b", "neutral": "#888"}
    icon = icons.get(direction, "●")
    color = colors.get(direction, "#888")
    return (
        f'<div style="font-size:11px;color:{color};margin-top:3px">'
        f'{icon} {delta}</div>'
    )


def kpi_title_card(
    title: str,
    subtitle: str = "",
    meta: str = "",
    width: int = 220,
) -> Div:
    import uuid
    uid = "title_" + uuid.uuid4().hex[:8]

    sub_html = (
        f'<div style="font-size:12px;color:#777;margin-top:3px">{subtitle}</div>'
        if subtitle else ""
    )

    meta_html = (
        f'<div style="font-size:11px;color:#aaa;margin-top:10px;border-top:1px solid #eee;'
        f'padding-top:8px">{meta}</div>'
        if meta else ""
    )

    return Div(text=f"""
<style>
.{uid} {{
    background:#f5f6fa;
    border:1px solid #e5e7ef;
    border-radius:14px;
    padding:1.3em 1.4em;
    min-width:{width}px;
    box-sizing:border-box;
    transition: border-color 0.22s ease, box-shadow 0.22s ease;
}}

.{uid}:hover {{
    border-color: #845EC2;
    box-shadow: 0 4px 18px #845EC222;
}}
</style>

<div class="{uid}">
    <div style="font-size:15px;font-weight:700;color:#1a1d2e">{title}</div>
    {sub_html}
    {meta_html}
</div>
""")


def kpi_metric_card(
    label: str,
    value: str,
    delta: str = "",
    direction: str = "neutral",
    accent_color: str = "",
    badge_text: str = "",
    badge_color: str = "#845EC2",
    width: int = 200,
) -> Div:
    import uuid
    uid = "kpi_" + uuid.uuid4().hex[:8]          # unique class per card
    left_border = (
        f"border-left:4px solid {accent_color};border-radius:0 10px 10px 0;"
        if accent_color else "border-radius:12px;"
    )
    label_color = accent_color if accent_color else "#555"
    hover_color = accent_color if accent_color else "#845EC2"

    if badge_text:
        bottom_html = (
            f'<span style="font-size:11px;background:{badge_color}22;color:{badge_color};'
            f'border-radius:6px;padding:2px 8px;font-weight:600">{badge_text}</span>'
        )
    else:
        bottom_html = _delta_html(delta, direction)

    return Div(text=f"""
<style>
.{uid} {{
    background:#fff;
    border:1px solid #e5e7ef;
    {left_border}
    padding:1.3em 1.4em;
    min-width:{width}px;
    box-sizing:border-box;
    transition: border-color 0.22s ease, box-shadow 0.22s ease;
    cursor: default;
}}
.{uid}:hover {{
    border-color: {hover_color};
    box-shadow: 0 4px 18px {hover_color}22;
}}
</style>
<div class="{uid}">
    <div style="font-size:11px;color:{label_color};letter-spacing:0.05em;
                font-weight:600;text-transform:uppercase">{label}</div>
    <div style="font-size:26px;font-weight:800;color:#1a1d2e;
                margin:6px 0 4px;line-height:1.1">{value}</div>
    {bottom_html}
</div>
""")


def kpi_row(*cards, spacing: int = 16) -> "Row":
    """Wrap any number of kpi_* cards into a Bokeh row with consistent spacing."""
    from bokeh.layouts import row
    return row(*cards, spacing=spacing)

