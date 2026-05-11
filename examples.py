
import math, sys
import numpy as np
from bokeh.plotting import figure, show, output_file
from bokeh.models   import ColumnDataSource, HoverTool, Select, CustomJS, Div, GlobalInlineStyleSheet,Span,CrosshairTool
from bokeh.layouts  import column, row

sys.path.insert(0, ".")
from bokeh_anim import anim, anim_pie, anim_scatter
from smooth_tip  import smooth_tip,smooth_tip_multi_varea, smooth_tip_multi,smooth_tip_multi_line
from helpers import *
output_file("bokeh_anim_examples.html", title="bokeh_anim examples")

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
show(row(p1,rmfocus(p1), stylesheets=[get_gstyle()]))


# ── 1. VERTICAL BAR — single series ─────────────────────────────────────────
dates = [f"Jun {i:02d}" for i in range(1, 15)]
temps = [22.1, 23.3, 21.9, 24.0, 25.5, 26.2, 27.1, 25.8, 24.4, 23.9, 22.2, 21.5, 23.0, 22.8]
rain  = [1.2, 0.0, 2.1, 0.5, 0.0, 0.3, 0.0, 1.8, 2.5, 0.0, 0.7, 1.3, 0.0, 0.2]
xv    = list(range(len(dates)))

src1 = ColumnDataSource(dict(
    x=xv,
    y=temps,          # anim() will zero this; temps is the initial dataset
    temps=temps,      # permanent copy — never zeroed by anim()
    rain=rain,        # permanent copy — never zeroed by anim()
    color=["#4e8cff"] * len(temps),
    label=[f"<b>{d}</b><br>🌡️ Temp: {t}°C<br>🌧️ Rain: {r}mm"
           for d, t, r in zip(dates, temps, rain)]
))

p1 = figure(title="1. Vertical Bar — Temperature", width=900, height=380,
            background_fill_color="#f8f9fb",
            x_range=(min(xv) - 0.5, max(xv) + 0.5))

r1 = p1.vbar(x='x', top='y', width=0.6, source=src1,
             color="color",
             hover_fill_color="#2563eb", hover_line_color="#2563eb",
             legend_label="Temp °C")

p1.xaxis.ticker = xv
p1.xaxis.major_label_overrides = {i: d for i, d in enumerate(dates)}
p1.xaxis.major_label_orientation = 0.6
# p1.y_range.start = 0
# p1.y_range.end   = max(temps) * 1.18
from bokeh.models import Range1d
p1.y_range = Range1d(start=0, end=max(temps) * 1.18)
p1.xgrid.visible = False
p1.legend.click_policy = "hide"
p1.toolbar.autohide = True
p1.add_tools(HoverTool(tooltips=None, renderers=[r1]))
smooth_tip(p1, src1, mode="bar")

anim(p1, easing="backOut", duration=800, handle_id="p1")

mystyle(p1)

# ── Dropdown ─────────────────────────────────────────────────────────────────
select = Select(title="Dataset:", value="Temperature",
                options=["Temperature", "Rain"], width=160)

callback = CustomJS(
    args=dict(src=src1, yr=p1.y_range, select=select,
              r1=r1,
              legend_item=p1.legend[0].items[0]  # p1.legend[0] is the Legend, .items[0] is the LegendItem
    ),
    code="""
    const choice  = select.value;
    const is_temp = choice === 'Temperature';
    const newVals = is_temp ? src.data['temps'].slice()
                            : src.data['rain'].slice();
    const color   = is_temp ? '#4e8cff' : '#34d399';
    const hcolor  = is_temp ? '#2563eb' : '#059669';

    src.data['color'] = Array(newVals.length).fill(color);
    src.change.emit();

    yr.start = 0;
    yr.end   = Math.max(...newVals) * 1.18;

    legend_item.label = { value: is_temp ? 'Temp °C' : 'Rain mm' };

    r1.hover_glyph.fill_color = hcolor;
    r1.hover_glyph.line_color = hcolor;

    const handle = (window.__bk_anim_handles__ || {})['p1_0'];
    if (handle) {
        handle.desc.fullTop = newVals;
        handle.start();
    }
"""
)
select.js_on_change("value", callback)
show(row(column(select, row(p1,rmfocus(p1))), stylesheets=[get_gstyle()]))




#==========
import json
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Select, CustomJS, Range1d
from bokeh.layouts import column
from bokeh.io import show
from bokeh_anim import anim
from smooth_tip import smooth_tip

# ── Data ─────────────────────────────────────────────────────────────────────
dates = [f"Jun {i:02d}" for i in range(1, 15)]
temps = [22.1, 23.3, 21.9, 24.0, 25.5, 26.2, 27.1, 25.8, 24.4, 23.9, 22.2, 21.5, 23.0, 22.8]
rain  = [1.2, 0.0, 2.1, 0.5, 0.0, 0.3, 0.0, 1.8, 2.5, 0.0, 0.7, 1.3, 0.0, 0.2]
xv    = list(range(len(dates)))

# ── Dataset registry — only place to edit when adding new data ───────────────
datasets = {
    "Temperature": {"values": temps, "color": "#4e8cff", "hcolor": "#2563eb", "label": "Temp °C"},
    "Rain":        {"values": rain,  "color": "#34d399", "hcolor": "#059669", "label": "Rain mm"},
}

init_key  = "Temperature"
init_meta = datasets[init_key]

# ── Source ───────────────────────────────────────────────────────────────────
# label column: one tooltip string per bar, rebuilt per dataset
def make_labels(key):
    vals = datasets[key]["values"]
    unit = datasets[key]["label"]
    return [f"<b>{d}</b><br>{unit}: {v}" for d, v in zip(dates, vals)]

src1 = ColumnDataSource(dict(
    x=xv,
    y=init_meta["values"],
    color=[init_meta["color"]] * len(xv),
    label=make_labels(init_key),                              # length 14 ✓
    **{name: meta["values"] for name, meta in datasets.items()},  # one col per dataset
    **{f"label_{name}": make_labels(name) for name in datasets},  # one label col per dataset
))

# ── Figure ───────────────────────────────────────────────────────────────────
p1 = figure(title=f"1. Vertical Bar — {init_key}", width=900, height=380,
            background_fill_color="#f8f9fb",
            x_range=(min(xv) - 0.5, max(xv) + 0.5))

p1.y_range = Range1d(start=0, end=max(init_meta["values"]) * 1.18)

r1 = p1.vbar(x='x', top='y', width=0.6, source=src1,
             color="color",
             hover_fill_color=init_meta["hcolor"],
             hover_line_color=init_meta["hcolor"],
             legend_label=init_meta["label"])

p1.xaxis.ticker = xv
p1.xaxis.major_label_overrides = {i: d for i, d in enumerate(dates)}
p1.xaxis.major_label_orientation = 0.6
p1.xgrid.visible = False
p1.legend.click_policy = "hide"
p1.toolbar.autohide = True
p1.add_tools(HoverTool(tooltips=None, renderers=[r1]))
smooth_tip(p1, src1, mode="bar")
anim(p1, easing="backOut", duration=800, handle_id="p1")
mystyle(p1)

# ── Dropdown ─────────────────────────────────────────────────────────────────
select = Select(value=init_key, options=list(datasets.keys()), width=160)

ds_meta = {name: {k: v for k, v in meta.items() if k != "values"}
           for name, meta in datasets.items()}

callback = CustomJS(
    args=dict(src=src1, yr=p1.y_range, select=select,
              r1=r1, legend_item=p1.legend[0].items[0],
              ds_meta=ds_meta),
    code="""
    const choice  = select.value;
    const meta    = ds_meta[choice];
    const newVals = src.data[choice].slice();

    src.data['y']     = newVals;
    src.data['color'] = Array(newVals.length).fill(meta.color);
    src.data['label'] = src.data['label_' + choice].slice();
    src.change.emit();

    yr.start = 0;
    yr.end   = Math.max(...newVals) * 1.18;

    legend_item.label         = { value: meta.label };
    r1.hover_glyph.fill_color = meta.hcolor;
    r1.hover_glyph.line_color = meta.hcolor;

    const handle = (window.__bk_anim_handles__ || {})['p1_0'];
    if (handle) {
        handle.desc.fullTop = newVals;
        handle.start();
    }
"""
)

select.js_on_change("value", callback)

show(row(column(select, row(p1,rmfocus(p1))), stylesheets=[get_gstyle()]))


#===========


# ── 2. GROUPED VERTICAL BARS ──────────────────────────────────────────────────
months  = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
revenue = [300, 420, 390, 510, 480, 560]
cost    = [210, 290, 260, 340, 300, 380]

src2r = ColumnDataSource(dict(
    x=[i - 0.2 for i in range(6)], y=revenue,
    label=[f"<b>{m}</b><br>💰 Revenue: ${v}k" for m, v in zip(months, revenue)]
))
src2c = ColumnDataSource(dict(
    x=[i + 0.2 for i in range(6)], y=cost,
    label=[f"<b>{m}</b><br>💸 Cost: ${v}k" for m, v in zip(months, cost)]
))
p2 = figure(title="2. Grouped Bars — Revenue vs Cost", width=900, height=380,
            background_fill_color="#f8f9fb", x_range=(-0.6, 5.6))
r11=p2.vbar(x='x', top='y', width=0.35, source=src2r, color="#2ecc71", legend_label="Revenue")
r21=p2.vbar(x='x', top='y', width=0.35, source=src2c, color="#e74c3c", legend_label="Cost")
p2.xaxis.ticker = list(range(6))
p2.xaxis.major_label_overrides = dict(enumerate(months))
p2.y_range.start, p2.y_range.end = 0, 650
p2.xgrid.visible = False
p2.legend.click_policy = "hide"
p2.toolbar.autohide = True
p2.add_tools(HoverTool(tooltips=None, renderers=[r11, r21]))
# merged source just for the tooltip — glyphs are untouched
src2_tip = ColumnDataSource(dict(
    x=[i - 0.2 for i in range(6)] + [i + 0.2 for i in range(6)],
    label=[f"<b>{m}</b><br>💰 Revenue: ${v}k" for m, v in zip(months, revenue)] +
          [f"<b>{m}</b><br>💸 Cost: ${v}k"    for m, v in zip(months, cost)],
    color=["#2ecc71"]*6 + ["#e74c3c"]*6,
))
smooth_tip(p2, src2_tip, mode="bar", hit_x=0.25)
anim(p2, easing="cubicOut", duration=700)
# show(p2)
mystyle(p2)
show(row(row(p2,rmfocus(p2)), stylesheets=[get_gstyle()]))

# ── 3. HORIZONTAL BARS ───────────────────────────────────────────────────────
langs  = ["Python", "JavaScript", "Rust", "Go", "C++", "TypeScript"]
scores = [95, 88, 76, 70, 65, 84]

src3 = ColumnDataSource(dict(
    x=scores, y=list(range(len(langs))),
    label=[f"<b>{l}</b><br>⭐ Score: {s}/100" for l, s in zip(langs, scores)]
))
p3 = figure(title="3. Horizontal Bar — Language Popularity", width=900, height=800,
            background_fill_color="#f8f9fb", y_range=(-0.6, len(langs) - 0.4))
p3.hbar(y='y', right='x', height=0.55, source=src3,
        color="#9b59b6", hover_fill_color="#7d3c98")
p3.yaxis.ticker = list(range(len(langs)))
p3.yaxis.major_label_overrides = dict(enumerate(langs))
p3.x_range.start, p3.x_range.end = 0, 112
p3.ygrid.visible = False
p3.toolbar.autohide = True
p3.add_tools(HoverTool(tooltips=None))
smooth_tip(p3, src3, mode="hbar", hit_y=0.5)
anim(p3, easing="cubicOut", duration=700)

mystyle(p3)
show(row(row(p3,rmfocus(p3)), stylesheets=[get_gstyle()]))






# ── 4. LINE — glowing wavefront dot ──────────────────────────────────────────
n4 = 40
x4 = list(range(n4))
y4 = [20 + 5 * math.sin(i * 0.35) + i * 0.08 for i in x4]

src4 = ColumnDataSource(dict(
    x=x4, y=y4,
    label=[f"<b>Day {i}</b><br>🌡️ Temp: {v:.1f}°C" for i, v in zip(x4, y4)]
))
p4 = figure(title="4. Line — Temperature Trend", width=900, height=380,
            background_fill_color="#f8f9fb", x_range=(-1, n4 + 1))
p4.line('x', 'y', source=src4, line_width=2.5, color="#e67e22", legend_label="Temp")
p4.y_range.start, p4.y_range.end = min(y4) - 2, max(y4) + 2
p4.legend.click_policy = "hide"
p4.toolbar.autohide = True
p4.add_tools(HoverTool(tooltips=None))
smooth_tip(p4, src4, mode="line")
anim(p4, easing="cubicInOut", duration=1400, line_tip=True, line_tip_color="#e67e22")
mystyle(p4, cross = True)
show(row(row(p4,rmfocus(p4)), stylesheets=[get_gstyle()]))






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
p5 = figure(title="5. Multi-line — click legend to re-animate", width=900, height=380,
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
show(row(row(p5,rmfocus(p5)), stylesheets=[get_gstyle()]))




# ---line dropdown
#+==========
import json
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Select, CustomJS, Range1d
from bokeh.layouts import column
from bokeh.io import show
from bokeh_anim import anim
from smooth_tip import smooth_tip

# ── Data ─────────────────────────────────────────────────────────────────────
dates = [f"Jun {i:02d}" for i in range(1, 15)]
temps = [22.1, 23.3, 21.9, 24.0, 25.5, 26.2, 27.1, 25.8, 24.4, 23.9, 22.2, 21.5, 23.0, 22.8]
rain  = [1.2, 0.0, 2.1, 0.5, 0.0, 0.3, 0.0, 1.8, 2.5, 0.0, 0.7, 1.3, 0.0, 0.2]
xv    = list(range(len(dates)))

# ── Dataset registry ──────────────────────────────────────────────────────────
datasets = {
    "Temperature": {"values": temps, "color": "#4e8cff", "label": "Temp °C"},
    "Rain":        {"values": rain,  "color": "#34d399", "label": "Rain mm"},
}

init_key  = "Temperature"
init_meta = datasets[init_key]

# ── Source ────────────────────────────────────────────────────────────────────
def make_labels(key):
    vals = datasets[key]["values"]
    unit = datasets[key]["label"]
    return [f"<b>{d}</b><br>{unit}: {v}" for d, v in zip(dates, vals)]

src1 = ColumnDataSource(dict(
    x=xv,
    y=init_meta["values"],
    **{name: meta["values"] for name, meta in datasets.items()},
    **{f"label_{name}": make_labels(name) for name in datasets},
    label=make_labels(init_key),
))

# ── Figure ────────────────────────────────────────────────────────────────────
p1 = figure(title=f"Line Chart — {init_key}", width=900, height=380,
            background_fill_color="#f8f9fb",
            x_range=(min(xv) - 0.5, max(xv) + 0.5))

p1.y_range = Range1d(
    start=min(init_meta["values"]) * 0.85,
    end=max(init_meta["values"]) * 1.18,
)

r1 = p1.line(
    x='x', y='y', source=src1,
    line_color=init_meta["color"],
    line_width=2.5,
    legend_label=init_meta["label"],
)

# # Circle markers on top of the line
# c1 = p1.circle(
#     x='x', y='y', source=src1,
#     size=7,
#     fill_color=init_meta["color"],
#     line_color="white",
#     line_width=1.5,
# )

p1.xaxis.ticker = xv
p1.xaxis.major_label_overrides = {i: d for i, d in enumerate(dates)}
p1.xaxis.major_label_orientation = 0.6
p1.xgrid.visible = False
p1.legend.click_policy = "hide"
p1.toolbar.autohide = True
p1.add_tools(HoverTool(tooltips=None, renderers=[r1]))

smooth_tip(p1, src1, mode="line", hit_x=0.6)
anim(p1, easing="cubicInOut",  handle_id="p1")
mystyle(p1)
# ── Dropdown ──────────────────────────────────────────────────────────────────
select = Select(value=init_key, options=list(datasets.keys()), width=160)

ds_meta = {name: {k: v for k, v in meta.items() if k != "values"}
           for name, meta in datasets.items()}

callback = CustomJS(
    args=dict(
        src=src1,
        yr=p1.y_range,
        select=select,
        r1=r1, #c1=c1,
        legend_item=p1.legend[0].items[0],
        ds_meta=ds_meta,
    ),
    code="""
    const choice  = select.value;
    const meta    = ds_meta[choice];
    const newVals = src.data[choice].slice();

    src.data['y']     = newVals;
    src.data['label'] = src.data['label_' + choice].slice();
    src.change.emit();

    const minV = Math.min(...newVals);
    const maxV = Math.max(...newVals);
    yr.start = minV * 0.85;
    yr.end   = maxV * 1.18;

    // Update line and circle colours
    r1.glyph.line_color = meta.color;
    //c1.glyph.fill_color = meta.color;

    legend_item.label = { value: meta.label };

    // Re-trigger entrance animation
    const handle = (window.__bk_anim_handles__ || {})['p1_0'];
    if (handle) {
        handle.desc.fullY = newVals;
        handle.start();
    }
""",
)

select.js_on_change("value", callback)

show(row(column(select, row(p1,rmfocus(p1))), stylesheets=[get_gstyle()]))


# ── 6. VAREA — two bands, any field names ────────────────────────────────────
n6  = 50
x6  = list(range(n6))
hi6 = [30 + 8 * math.sin(i * 0.25) + i * 0.12 for i in x6]
lo6 = [10 + 4 * math.sin(i * 0.25) + i * 0.06 for i in x6]
hi6b = [v - 3 for v in lo6]
lo6b = [2.0] * n6

src6a = ColumnDataSource(dict(
    x=x6, upper=hi6, lower=lo6,
    label=[f"<b>Day {i}</b><br>📈 High: {h:.1f}<br>📉 Low: {l:.1f}"
           for i, h, l in zip(x6, hi6, lo6)]
))
src6b = ColumnDataSource(dict(
    x=x6, upper=hi6b, lower=lo6b,
    label=[f"<b>Day {i}</b><br>📊 Band B top: {h:.1f}" for i, h in zip(x6, hi6b)]
))
p6 = figure(title="6. VArea — two bands, generic field names", width=900, height=380,
            background_fill_color="#f8f9fb", x_range=(-1, n6 + 1))
r61=p6.varea(x='x', y1='lower', y2='upper', source=src6a,
         fill_color="#3498db", fill_alpha=0.35, legend_label="Band A")
r62=p6.varea(x='x', y1='lower', y2='upper', source=src6b,
         fill_color="#e74c3c", fill_alpha=0.30, legend_label="Band B")
p6.y_range.start, p6.y_range.end = 0, max(hi6) * 1.18
p6.legend.click_policy = "hide"
p6.toolbar.autohide = True
p6.add_tools(HoverTool(tooltips=None, renderers=[r61, r62]))

smooth_tip_multi_varea(
    p6,
    sources=[src6a, src6b],
    colors=["#3498db", "#e74c3c"],
    hit_x=1.5,
)
anim(p6, easing="sineInOut", duration=1100)

mystyle(p6,cross=True)
show(row(row(p6,rmfocus(p6)), stylesheets=[get_gstyle()]))

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

smooth_tip(p7, src7, mode="pie", pie_inner_radius=0.0, pie_outer_radius=1.15)
anim_pie(p7, src7, easing="backOut", duration=900, stagger=100)
mystyle(p7)
show(row(row(p7,rmfocus(p7)), stylesheets=[get_gstyle()]))

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
smooth_tip(p7d, src7d, mode="pie", pie_inner_radius=0.55, pie_outer_radius=1.15)
anim_pie(p7d, src7d, easing="backOut", duration=900, stagger=90)

mystyle(p7d)
show(row(row(p7d,rmfocus(p7d)), stylesheets=[get_gstyle()]))




#===========
import math
from bokeh.plotting import figure
from bokeh.models import (ColumnDataSource, HoverTool, Select, CustomJS,
                          Legend, LegendItem)
from bokeh.layouts import column, row
from bokeh.io import show
from bokeh_anim import anim_pie
from smooth_tip import smooth_tip

# ── Dataset registry ──────────────────────────────────────────────────────────
DATASETS = {
    "Languages": {
        "categories": ["Python",   "JS",      "Rust",    "Go",      "Other"  ],
        "values":     [40,          25,         15,        12,         8      ],
        "colors":     ["#3498db", "#f39c12", "#e74c3c", "#2ecc71", "#9b59b6" ],
    },
    "Browsers": {
        "categories": ["Chrome",   "Safari",  "Firefox", "Edge",    "Other"  ],
        "values":     [65,          19,         4,          4,         8      ],
        "colors":     ["#4285f4", "#34a853",  "#ff6611", "#0078d7", "#aaaaaa"],
    },
    "OS Share": {
        "categories": ["Windows",  "macOS",   "Linux",   "Android", "iOS"    ],
        "values":     [35,          15,         3,         28,        19      ],
        "colors":     ["#0078d7", "#888888",  "#dd4814", "#3ddc84", "#555555"],
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def compute_angles(values):
    total  = sum(values)
    angles = [v / total * 2 * math.pi for v in values]
    starts = [sum(angles[:i])   for i in range(len(angles))]
    ends   = [sum(angles[:i+1]) for i in range(len(angles))]
    return starts, ends

def make_labels(key):
    ds    = DATASETS[key]
    total = sum(ds["values"])
    return [
        f"<b>{c}</b><br>Share: {v}&nbsp;&nbsp;({v/total*100:.1f}%)"
        for c, v in zip(ds["categories"], ds["values"])
    ]

# Pre-compute JS-side lookup dict
js_datasets = {}
for k, ds in DATASETS.items():
    starts, ends = compute_angles(ds["values"])
    js_datasets[k] = {
        "starts":       starts,
        "ends":         ends,
        "colors":       ds["colors"],
        "labels":       make_labels(k),
        "label_legend": ds["categories"],
    }

init_key = "Languages"
init     = js_datasets[init_key]
N        = len(init["starts"])   # number of sectors (same for all datasets here)

# ── Sources ───────────────────────────────────────────────────────────────────
def make_source(d):
    return ColumnDataSource(dict(
        start_angle  = d["starts"][:],
        end_angle    = d["ends"][:],
        color        = d["colors"][:],
        label        = d["labels"][:],
    ))

src_pie   = make_source(init)
src_donut = make_source(init)

# ── Figures ───────────────────────────────────────────────────────────────────
def base_fig(title):
    p = figure(title=title, width=500, height=460,
               background_fill_color="#f8f9fb",
               x_range=(-1.4, 1.4), y_range=(-1.4, 1.4),
               toolbar_location=None)
    p.axis.visible = False
    p.grid.visible = False
    return p

# ── Pie ───────────────────────────────────────────────────────────────────────
p_pie = base_fig(f"Pie — {init_key}")
r_pie = p_pie.wedge(
    x=0, y=0, radius=1.1,
    start_angle='start_angle', end_angle='end_angle',
    fill_color='color', fill_alpha=0.85,
    line_color='color', line_width=2,
    source=src_pie,
    hover_fill_alpha=1, hover_line_color='black',
)

# Build legend manually — one LegendItem per sector with its own square glyph
# This is the only way to get per-item colors that update reliably in JS.
from bokeh.models import Rect
pie_legend_items = []
pie_swatches     = []   # Rect glyphs we'll recolour in JS
for i, (cat, col) in enumerate(zip(init["label_legend"], init["colors"])):
    swatch = p_pie.rect(x=[0], y=[0], width=0.001, height=0.001,
                        fill_color=col, line_color=col, visible=False)
    pie_swatches.append(swatch)
    pie_legend_items.append(LegendItem(label=cat, renderers=[swatch]))

pie_legend = Legend(items=pie_legend_items, location='center')
p_pie.add_layout(pie_legend, 'right')
p_pie.add_tools(HoverTool(tooltips=None))
smooth_tip(p_pie, src_pie, mode='pie', pie_inner_radius=0.0, pie_outer_radius=1.15)
anim_pie(p_pie, src_pie, easing='backOut', duration=900, stagger=100, handle_id='pie')

# ── Donut ─────────────────────────────────────────────────────────────────────
p_donut = base_fig(f"Donut — {init_key}")
r_donut = p_donut.annular_wedge(
    x=0, y=0, inner_radius=0.55, outer_radius=1.1,
    start_angle='start_angle', end_angle='end_angle',
    fill_color='color', fill_alpha=0.85,
    line_color='color', line_width=2,
    source=src_donut,
    hover_fill_alpha=1, hover_line_color='black',
)

donut_legend_items = []
donut_swatches     = []
for i, (cat, col) in enumerate(zip(init["label_legend"], init["colors"])):
    swatch = p_donut.rect(x=[0], y=[0], width=0.001, height=0.001,
                          fill_color=col, line_color=col, visible=False)
    donut_swatches.append(swatch)
    donut_legend_items.append(LegendItem(label=cat, renderers=[swatch]))

donut_legend = Legend(items=donut_legend_items, location='center')
p_donut.add_layout(donut_legend, 'right')
p_donut.add_tools(HoverTool(tooltips=None))
smooth_tip(p_donut, src_donut, mode='pie', pie_inner_radius=0.55, pie_outer_radius=1.15)
anim_pie(p_donut, src_donut, easing='backOut', duration=900, stagger=90, handle_id='donut')

# ── Dropdown ──────────────────────────────────────────────────────────────────
select = Select(value=init_key, options=list(DATASETS.keys()), width=180)

callback = CustomJS(
    args=dict(
        select          = select,
        js_datasets     = js_datasets,
        pie_title       = p_pie.title,
        donut_title     = p_donut.title,
        pie_leg_items   = pie_legend_items,
        donut_leg_items = donut_legend_items,
        pie_swatches    = pie_swatches,
        donut_swatches  = donut_swatches,
    ),
    code="""
    const choice = select.value;
    const d      = js_datasets[choice];

    // Titles
    pie_title.text   = 'Pie — '   + choice;
    donut_title.text = 'Donut — ' + choice;

    // Legend: update label text and swatch color for each item
    for (let i = 0; i < d.label_legend.length; i++) {
        const label = d.label_legend[i];
        const color = d.colors[i];

        pie_leg_items[i].label   = label;
        donut_leg_items[i].label = label;

        pie_swatches[i].glyph.fill_color   = color;
        pie_swatches[i].glyph.line_color   = color;
        donut_swatches[i].glyph.fill_color = color;
        donut_swatches[i].glyph.line_color = color;
    }

    // Hand full payload to retrigger — it sets colors+labels on the source
    // then collapses+re-animates. Never touch sources here directly.
    const ph = window.__bk_pie_handles__ || {};
    if (ph['pie'])   ph['pie'].retrigger(d);
    if (ph['donut']) ph['donut'].retrigger(d);
""",
)

select.js_on_change("value", callback)

show(column(select, row(p_pie, p_donut)))

###-============



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
p8 = figure(title="8. Bubble — staggered pop-in", width=900, height=420,
            background_fill_color="#f8f9fb", x_range=(-5, 105), y_range=(-5, 105))
p8.scatter('x', 'y', size='size', source=src8,
           fill_color="#16a085", fill_alpha=0.65, hover_fill_alpha=1.0, hover_line_width = 4,
           line_color="#0e6655", line_width=1.5)
p8.toolbar.autohide = True
p8.add_tools(HoverTool(tooltips=None))
smooth_tip(p8, src8, mode="scatter", hit_radius=6)
anim_scatter(p8, src8, size_field="size", easing="elasticOut", duration=500, stagger=45)

mystyle(p8)
show(row(row(p8,rmfocus(p8)), stylesheets=[get_gstyle()]))




# ── 8. SCATTER / BUBBLE ──────────────────────────────────────────────────────
np.random.seed(42)

# ── Dataset definitions ───────────────────────────────────────────────────────
_scatter_datasets = {
    "Random":    dict(
        x=np.random.uniform(0, 100, 30).tolist(),
        y=np.random.uniform(0, 100, 30).tolist(),
        sz=np.random.uniform(12, 38, 30).tolist(),
        fill="#16a085", line="#0e6655",
        label_prefix="Item",
    ),
    "Clustered": dict(
        x=np.concatenate([
            np.random.normal(25, 8, 10),
            np.random.normal(65, 8, 10),
            np.random.normal(45, 6, 10),
        ]).tolist(),
        y=np.concatenate([
            np.random.normal(30, 8, 10),
            np.random.normal(70, 8, 10),
            np.random.normal(50, 6, 10),
        ]).tolist(),
        sz=np.random.uniform(14, 34, 30).tolist(),
        fill="#7F77DD", line="#534AB7",
        label_prefix="Node",
    ),
    "Diagonal":  dict(
        x=np.linspace(5, 95, 30).tolist(),
        y=(np.linspace(5, 95, 30) + np.random.normal(0, 8, 30)).tolist(),
        sz=np.linspace(10, 40, 30).tolist(),
        fill="#D85A30", line="#993C1D",
        label_prefix="Pt",
    ),
}

def _make_scatter_labels(ds):
    return [
        f"<b>{ds['label_prefix']} {i+1}</b><br>X: {x:.1f}<br>Y: {y:.1f}<br>Size: {s:.0f}"
        for i, (x, y, s) in enumerate(zip(ds["x"], ds["y"], ds["sz"]))
    ]

_init_key8 = "Random"
_ds8       = _scatter_datasets[_init_key8]
n8         = len(_ds8["x"])

# src8 carries every dataset's x/y/sz/label columns so the JS callback
# can swap them without a round-trip to Python.
src8 = ColumnDataSource(dict(
    x    = _ds8["x"],
    y    = _ds8["y"],
    size = _ds8["sz"],
    label= _make_scatter_labels(_ds8),
    **{f"x_{k}":     v["x"]                    for k, v in _scatter_datasets.items()},
    **{f"y_{k}":     v["y"]                    for k, v in _scatter_datasets.items()},
    **{f"sz_{k}":    v["sz"]                   for k, v in _scatter_datasets.items()},
    **{f"label_{k}": _make_scatter_labels(v)   for k, v in _scatter_datasets.items()},
))

# Serialise palette info so the JS callback can update fill/line colors too.
_palette8 = {k: {"fill": v["fill"], "line": v["line"]}
             for k, v in _scatter_datasets.items()}

p8 = figure(
    title=f"8. Bubble — {_init_key8}",
    width=900, height=420,
    background_fill_color="#f8f9fb",
    x_range=(-5, 105), y_range=(-5, 105),
)

r8 = p8.scatter(
    "x", "y", size="size", source=src8,
    fill_color=_ds8["fill"], fill_alpha=0.65,
    hover_fill_alpha=1.0, hover_line_width=4,
    line_color=_ds8["line"], line_width=1.5,
)

p8.toolbar.autohide = True
p8.add_tools(HoverTool(tooltips=None))
smooth_tip(p8, src8, mode="scatter", hit_radius=6)
anim_scatter(p8, src8, size_field="size", easing="elasticOut", duration=500, stagger=45)
mystyle(p8)

# ── Dropdown ──────────────────────────────────────────────────────────────────
select8 = Select(
    value=_init_key8,
    options=list(_scatter_datasets.keys()),
    width=160,
)

# The callback:
#   1. Swaps x / y / size / label from the pre-stored columns.
#   2. Updates glyph fill_color / line_color on both the normal and hover glyph.
#   3. Re-runs the staggered pop-in animation inline (mirrors _JS_SCATTER logic).
#   4. Updates the figure title.
_scatter_cb = CustomJS(
    args=dict(src=src8, r=r8, title_obj=p8.title,
              palette=_palette8, select=select8),
    code="""
    const key   = select.value;
    const pal   = palette[key];
    const n     = src.data['x_' + key].length;

    // 1 · swap visible columns (zero size so pop-in starts from invisible)
    src.data['x']     = src.data['x_'     + key].slice();
    src.data['y']     = src.data['y_'     + key].slice();
    src.data['label'] = src.data['label_' + key].slice();
    src.data['size']  = new Array(n).fill(0);
    src.change.emit();

    // 2 · update glyph colors
    r.glyph.fill_color      = pal.fill;
    r.glyph.line_color      = pal.line;
    r.hover_glyph.fill_color = pal.fill;
    r.hover_glyph.line_color = pal.line;

    // 3 · update title
    title_obj.text = '8. Bubble \u2014 ' + key;

    // 4 · staggered pop-in  (inline, mirrors bokeh_anim _JS_SCATTER)
    const fullSize = src.data['sz_' + key].slice();
    const DURATION = 500;
    const stagger  = 45;
    // elasticOut easing
    function easeFn(t) {
        if (t === 0 || t === 1) return t;
        return Math.pow(2, -10 * t) * Math.sin((t - 0.075) * (2 * Math.PI) / 0.3) + 1;
    }
    for (let i = 0; i < n; i++) {
        (function(idx) {
            const target = fullSize[idx];
            setTimeout(function() {
                let t0 = null;
                function step(ts) {
                    if (t0 === null) t0 = ts;
                    const raw   = Math.min((ts - t0) / DURATION, 1.0);
                    const sizes = src.data['size'].slice();
                    sizes[idx]  = target * easeFn(raw);
                    src.data['size'] = sizes;
                    src.change.emit();
                    if (raw < 1.0) requestAnimationFrame(step);
                }
                requestAnimationFrame(step);
            }, idx * stagger);
        })(i);
    }
""",
)

select8.js_on_change("value", _scatter_cb)

# ── Layout (drop-in — replace your old p8 show/column call) ──────────────────
show(row(column(select8, row(p8,rmfocus(p8))), stylesheets=[get_gstyle()]))

# =============

# ── 8. SCATTER / BUBBLE — three clusters, checkbox + legend re-animation ─────
np.random.seed(42)

# ── Cluster definitions ───────────────────────────────────────────────────────
_clusters = [
    dict(name="Cluster A", cx=25, cy=70, n=12,
         fill="#E24B4A", line="#A32D2D", sz_lo=14, sz_hi=36),   # red
    dict(name="Cluster B", cx=65, cy=30, n=12,
         fill="#1D9E75", line="#085041", sz_lo=12, sz_hi=30),   # green
    dict(name="Cluster C", cx=50, cy=65, n=11,
         fill="#D4537E", line="#72243E", sz_lo=16, sz_hi=34),   # pink
]

def _cluster_source(c):
    xs  = np.random.normal(c["cx"], 9, c["n"]).tolist()
    ys  = np.random.normal(c["cy"], 9, c["n"]).tolist()
    szs = np.random.uniform(c["sz_lo"], c["sz_hi"], c["n"]).tolist()
    labels = [
        f"<b>{c['name']} — {i+1}</b><br>X: {x:.1f}<br>Y: {y:.1f}<br>Size: {s:.0f}"
        for i, (x, y, s) in enumerate(zip(xs, ys, szs))
    ]
    return ColumnDataSource(dict(x=xs, y=ys, size=szs, label=labels))

sources8    = [_cluster_source(c) for c in _clusters]
handle_ids8 = [f"scatter8_{i}" for i in range(len(_clusters))]

# ── Figure ────────────────────────────────────────────────────────────────────
p8 = figure(
    title="8. Bubble — three clusters",
    width=900, height=420,
    background_fill_color="#f8f9fb",
    x_range=(-5, 105), y_range=(-5, 105),
)

renderers8 = []
for c, src in zip(_clusters, sources8):
    r = p8.scatter(
        "x", "y", size="size", source=src,
        fill_color=c["fill"], fill_alpha=0.65,
        hover_fill_alpha=1.0, hover_line_width=4,
        line_color=c["line"], line_width=1.5,
        legend_label=c["name"],
    )
    renderers8.append(r)

p8.legend.location     = "top_left"
p8.legend.click_policy = "hide"
p8.toolbar.autohide    = True
p8.add_tools(HoverTool(tooltips=None))
mystyle(p8)

# ── Tooltip — single callback across all sources ──────────────────────────────
# smooth_tip_multi() registers ONE mousemove that searches every source at once
# and picks the globally nearest point with the correct per-cluster color.
# Never call smooth_tip() per-source for multi-cluster plots.
smooth_tip_multi(p8, sources8, renderers=renderers8, hit_radius=6)

# ── Animation — staggered pop-in per cluster ──────────────────────────────────
for src, hid in zip(sources8, handle_ids8):
    anim_scatter(p8, src, size_field="size",
                 easing="elasticOut", duration=500, stagger=45,
                 handle_id=hid)

# ── Legend re-animation ───────────────────────────────────────────────────────
for r, hid in zip(renderers8, handle_ids8):
    r.js_on_change("visible", CustomJS(
        args=dict(handle_id=hid),
        code="""
        if (!cb_obj.visible) return;
        const h = (window.__bk_scatter_handles__ || {})[handle_id];
        if (h) h.retrigger();
    """))

# ── CheckboxGroup — visibility + retrigger ────────────────────────────────────
from bokeh.models import CheckboxGroup

checkbox8 = CheckboxGroup(
    labels=[c["name"] for c in _clusters],
    active=list(range(len(_clusters))),
    width=160,
)

checkbox8.js_on_change("active", CustomJS(
    args=dict(renderers=renderers8, handle_ids=handle_ids8),
    code="""
    renderers.forEach(function(r, i) {
        const wasVisible = r.visible;
        const nowVisible = cb_obj.active.includes(i);
        r.visible = nowVisible;
        if (!wasVisible && nowVisible) {
            const h = (window.__bk_scatter_handles__ || {})[handle_ids[i]];
            if (h) h.retrigger();
        }
    });
"""))

# ── Layout ────────────────────────────────────────────────────────────────────

show(row(column(checkbox8, row(p8,rmfocus(p8))), stylesheets=[get_gstyle()]))






