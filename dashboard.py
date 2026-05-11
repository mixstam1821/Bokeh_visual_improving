
import math, sys
import numpy as np
from bokeh.plotting import figure, show, output_file
from bokeh.models   import ColumnDataSource, HoverTool, Select, CustomJS, Div, GlobalInlineStyleSheet,Span,CrosshairTool
from bokeh.layouts  import column, row

sys.path.insert(0, ".")
from bokeh_anim import anim, anim_pie, anim_scatter
from smooth_tip  import smooth_tip, smooth_tip_multi,smooth_tip_multi_line
from helpers import *
output_file("bokeh_anim_examples.html", title="bokeh_anim examples")



# from kpi_cards import kpi_title_card, kpi_metric_card, kpi_row
from bokeh.plotting import show
from bokeh.layouts import column

card1 = kpi_title_card(
    title="Sales Dashboard",
    subtitle="Q2 2025 · Europe region",
    meta="Updated 5 min ago",
)
card2 = kpi_metric_card(
    label="Active Users",
    value="1,023",
    delta="+5.2% this month",
    direction="up",
)
card3 = kpi_metric_card(
    label="Revenue",
    value="$9,150",
    delta="+12% vs last month",
    direction="up",
    accent_color="#845EC2",
)
card4 = kpi_metric_card(
    label="System Health",
    value="72%",
    badge_text="Degraded",
    badge_color="#e67e22",
)
card5 = kpi_metric_card(
    label="System Health",
    value="72%",
    badge_text="Degraded",
    badge_color="#e67e22",
)
card6 = kpi_metric_card(
    label="Revenue",
    value="$9,150",
    delta="+12% vs last month",
    direction="up",
    accent_color="#845EC2",
)
card7 = kpi_metric_card(
    label="Active Users",
    value="1,023",
    delta="+5.2% this month",
    direction="up",
)


# ── 1. VERTICAL BAR — single series ─────────────────────────────────────────
dates = [f"Jun {i:02d}" for i in range(1, 15)]
temps = [22.1, 23.3, 21.9, 24.0, 25.5, 26.2, 27.1, 25.8, 24.4, 23.9, 22.2, 21.5, 23.0, 22.8]
rain  = [1.2, 0.0, 2.1, 0.5, 0.0, 0.3, 0.0, 1.8, 2.5, 0.0, 0.7, 1.3, 0.0, 0.2]
xv    = list(range(len(dates)))

src1 = ColumnDataSource(dict(
    x=xv, y=temps,color=["#4e8cff"] * len(temps),
    label=[f"<b>{d}</b><br>🌡️ Temp: {t}°C<br>🌧️ Rain: {r}mm"
           for d, t, r in zip(dates, temps, rain)]
))
p1 = figure(title="1. Vertical Bar — Temperature", width=900, height=380,
            background_fill_color="#f8f9fb",
            x_range=(min(xv) - 0.5, max(xv) + 0.5))
r1 = p1.vbar(x='x', top='y', width=0.8, source=src1, color="#4e8cff", border_radius=5,
             hover_fill_color="#2563eb", hover_line_color="#2563eb",
             legend_label="Temp °C")

p1.xaxis.ticker = xv
p1.xaxis.major_label_overrides = {i: d for i, d in enumerate(dates)}
p1.xaxis.major_label_orientation = 0.6
p1.y_range.start, p1.y_range.end = 0, max(temps) * 1.18
p1.add_tools(HoverTool(tooltips=None, renderers=[r1]))
smooth_tip(p1, src1, mode="bar");   anim(p1, easing="backOut", duration=800);   mystyle(p1)



# ── 5. MULTI-LINE — legend click re-animates ─────────────────────────────────
from bokeh.models import Span, CrosshairTool
span_height = Span(
    dimension="height", line_dash="dashed", line_width=2, line_color="#878787"
)
crosshair_tool = CrosshairTool(overlay=span_height)

n5 = 40
x5 = list(range(n5))
src5a = ColumnDataSource(dict(
    x=x5, y=[math.sin(i * 0.3) * 10 + 50 for i in x5],
    label=[f"<b>Series A</b><br>Value: {math.sin(i*0.3)*10+50:.1f}" for i in x5]
))
src5b = ColumnDataSource(dict(
    x=x5, y=[math.cos(i * 0.3) * 8 + 45 for i in x5],
    label=[f"<b>Series B</b><br>Value: {math.cos(i*0.3)*8+45:.1f}" for i in x5]
))
p5 = figure(title="5. Multi-line — click legend to re-animate", width=800, height=380,
            background_fill_color="white", x_range=(-1, n5 + 1))
r5a = p5.line('x', 'y', source=src5a, line_width=2.5, color="#FFC115", legend_label="Series A")
r5b = p5.line('x', 'y', source=src5b, line_width=2.5, color="#FF4CE7", legend_label="Series B")

p5.y_range.start, p5.y_range.end = 25, 70
p5.add_tools(HoverTool(tooltips=None, renderers=[r5a, r5b]))
# One combined tooltip for both
smooth_tip_multi_line(
    p5,
    sources=[src5a, src5b],
    title="X: {x}", 
)
anim(p5, easing="cubicInOut", duration=1400, line_tip=True, line_tip_color="#3498db")
mystyle(p5, cross = True)

# ── 7. PIE ───────────────────────────────────────────────────────────────────
categories = ["Python", "JS", "Rust", "Go", "Other"]
values7    = [40, 25, 15, 12, 8]
total7     = sum(values7)
angles7    = [v / total7 * 2 * math.pi for v in values7]
starts7    = [sum(angles7[:i]) for i in range(len(angles7))]
ends7      = [sum(angles7[:i+1]) for i in range(len(angles7))]
colors7    = ["#3498db", "#f39c12", "#e74c3c", "#2ecc71", "#9b59b6"]

src7 = ColumnDataSource(dict(
    start_angle=starts7, end_angle=ends7, color=colors7,
    label=[f"<b>{c}</b><br>Share: {v}%" for c, v in zip(categories, values7)],
    label_legend = [c for c in categories]
))
p7 = figure(title="7. Pie — sector sweep", width=500, height=460,
            background_fill_color="#f8f9fb",
            x_range=(-1.4, 1.4), y_range=(-1.4, 1.4), toolbar_location=None)
p7.wedge(x=0, y=0, radius=1.1, start_angle='start_angle', end_angle='end_angle',
         fill_color='color', fill_alpha = 0.8, line_color="color", line_width=2,
         source=src7, legend_field="label_legend", hover_fill_alpha=1,hover_line_color="black",)
p7.axis.visible = False
p7.grid.visible = False
p7.add_layout(p7.legend[0], "right")
p7.add_tools(HoverTool(tooltips=None))

# p7.min_border_bottom = 0
smooth_tip(p7, src7, mode="pie", pie_inner_radius=0.0, pie_outer_radius=1.15)
anim_pie(p7, src7, easing="backOut", duration=900, stagger=100);    mystyle(p7)
p7.toolbar_location = None
# ── 7b. DONUT ────────────────────────────────────────────────────────────────
src7d = ColumnDataSource(dict(
    start_angle=starts7, end_angle=ends7, color=colors7,
    label=[f"<b>{c}</b><br>Share: {v}%" for c, v in zip(categories, values7)],
    label_legend = [c for c in categories]
))
p7d = figure(title="7b. Donut — hollow center", width=500, height=460,
             background_fill_color="#f8f9fb",
             x_range=(-1.4, 1.4), y_range=(-1.4, 1.4), toolbar_location=None)
p7d.annular_wedge(x=0, y=0, inner_radius=0.55, outer_radius=1.1,
                  start_angle='start_angle', end_angle='end_angle',
                  fill_color='color',fill_alpha = 0.8, line_color="color", line_width=2, legend_field="label_legend",
                  source=src7d, hover_fill_alpha=1,hover_line_color="black")
p7d.axis.visible = False
p7d.grid.visible = False
p7d.add_layout(p7d.legend[0], "right")
p7d.add_tools(HoverTool(tooltips=None))
smooth_tip(p7d, src7d, mode="pie", pie_inner_radius=0.55, pie_outer_radius=1.15);   
anim_pie(p7d, src7d, easing="backOut");   mystyle(p7d)
p7d.toolbar_location = None


# ── 8. SCATTER / BUBBLE ──────────────────────────────────────────────────────
np.random.seed(42)
n8   = 30
x8   = np.random.uniform(0, 100, n8).tolist()
y8   = np.random.uniform(0, 100, n8).tolist()
sz8  = np.random.uniform(12, 38, n8).tolist()

src8 = ColumnDataSource(dict(
    x=x8, y=y8, size=sz8,
    label=[f"<b>Item {i+1}</b><br>X: {x:.1f}<br>Y: {y:.1f}<br>Size: {s:.0f}"
           for i, (x, y, s) in enumerate(zip(x8, y8, sz8))]
))
p8 = figure(title="8. Bubble — staggered pop-in", width=900, height=380,
            background_fill_color="#f8f9fb", x_range=(-5, 105), y_range=(-5, 105))
p8.scatter('x', 'y', size='size', source=src8,
           fill_color="#16a085", fill_alpha=0.65, hover_fill_alpha=1.0, hover_line_width = 4,
           line_color="#0e6655", line_width=1.5)
p8.add_tools(HoverTool(tooltips=None))
smooth_tip(p8, src8, mode="scatter", hit_radius=6); anim_scatter(p8, src8, size_field="size", easing="elasticOut");     mystyle(p8)

show(column(
            row(card1, card2, card3, card4, card5, card6, card7), 
            row(p1,p8), 
            row(p7d,p7,p5),
            stylesheets=[get_gstyle()]))


