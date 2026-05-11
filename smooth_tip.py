

from bokeh.models import CustomJS

# ---------------------------------------------------------------------------
# Shared init — creates the single tooltip div + lerp animation loop.
# ---------------------------------------------------------------------------
_TIP_INIT = """
    let tip = document.getElementById('echarts-tip');
    if (!tip) {
        tip = document.createElement('div');
        tip.id = 'echarts-tip';
        Object.assign(tip.style, {
            position:      'fixed',
            padding:       '8px 12px',
            background:    'rgba(255,255,255,0.97)',
            color:         '#333',
            border:        '1px solid #e0e0e0',
            borderRadius:  '6px',
            pointerEvents: 'none',
            fontFamily:    'system-ui, sans-serif',
            fontSize:      '13px',
            lineHeight:    '1.7',
            zIndex:        '9999',
            boxShadow:     '0 4px 18px rgba(0,0,0,0.13)',
            opacity:       '0',
            transition:    'opacity 0.15s ease',
            willChange:    'transform',
            maxWidth:      '260px',
            display:       'none',
        });
        document.body.appendChild(tip);
        tip._cx = 0; tip._cy = 0;
        tip._tx = 0; tip._ty = 0;
        tip._visible  = false;
        tip._hideTimer = null;
        const lag = LAG_VALUE;
        function _lerp(a, b, t) { return a + (b - a) * t; }
        (function _animate() {
            tip._cx = _lerp(tip._cx, tip._tx, lag);
            tip._cy = _lerp(tip._cy, tip._ty, lag);
            tip.style.left = tip._cx + 'px';
            tip.style.top  = tip._cy + 'px';
            requestAnimationFrame(_animate);
        })();
    }
"""

_TIP_HIDE = """
    tip.style.opacity = '0';
    tip._visible = false;
    if (tip._hideTimer) clearTimeout(tip._hideTimer);
    tip._hideTimer = setTimeout(() => { tip.style.display = 'none'; }, 200);
"""

# ---------------------------------------------------------------------------
# Coordinate computation — THE fix vs the old version.
#
# OLD (broken): cb_obj.origin.el  — origin is a MODEL, models have no .el
#               → always undefined → rect falls back to {left:0,top:0}
#               → tooltip always at top-left of viewport
#
# NEW (correct): cb_context.index.query_one(v => v.model.id === cb_obj.origin.id)
#               → recursively searches all views including nested layout children
#               → returns the PlotVIEW which has .el
#               → .el.querySelector('.bk-events') gives the hit-area element
#               → getBoundingClientRect() gives the true viewport position
#
# clientX = rect.left + cb_obj.sx   (scroll cancels in Bokeh's offset_bbox math)
# Works with position:fixed tooltip since clientX/Y are viewport-relative.
# ---------------------------------------------------------------------------
_GET_COORDS = """
    const _plotView = cb_context.index.query_one(
        v => v.model && v.model.id === cb_obj.origin.id
    );
    console.log(_plotView);
    const _evEl = _plotView
        ? _plotView.el.querySelector('.bk-canvas-events') || _plotView.el
        : null;
    const _rect = _evEl ? _evEl.getBoundingClientRect() : {left: 0, top: 0};

    const _vx = _rect.left + cb_obj.sx;
    const _vy = _rect.top  + cb_obj.sy;
    console.log(_vx, _vy);
    console.log(cb_obj.sx, cb_obj.sx);

"""

_TIP_SHOW = """
    function showTip(label, tx, ty, borderColor) {
        tip.style.borderColor = borderColor || '#e0e0e0';
        tip.innerHTML = label;
        tip.style.display = 'block';
        const tipW = tip.offsetWidth  || 200;
        const tipH = tip.offsetHeight || 80;
        const vw = window.innerWidth, vh = window.innerHeight;
        if (tx + tipW + 22 > vw) tx = tx - tipW - 22;
        if (ty + tipH + 10 > vh) ty = ty - tipH - 10;
        if (ty < 6) ty = 6;
        if (!tip._visible) {
            tip._cx = tx; tip._cy = ty;
            if (tip._hideTimer) { clearTimeout(tip._hideTimer); tip._hideTimer = null; }
            requestAnimationFrame(() => { tip.style.opacity = '1'; });
            tip._visible = true;
        }
        tip._tx = tx; tip._ty = ty;
    }
"""

_LABEL_STYLE = """
    function styledLabel(raw, keyColor) {
        const kc = keyColor || 'deepskyblue';
        let out = raw.replace(
            /<b>(.*?)<\\/b>/g,
            '<b style="color:' + kc + '">$1</b>'
        );
        out = out.replace(
            /((?:^|<br\\s*\\/?>)\\s*)([^<:]+?)(\\s*:)/gi,
            '$1<span style="color:' + kc + ';font-weight:600">$2$3</span>'
        );
        return out;
    }
"""

_GET_GLYPH_COLOR = """
    function glyphColor(renderers, idx) {
        const r = (renderers && renderers[idx != null ? idx : 0]) || null;
        if (!r || !r.glyph) return 'deepskyblue';
        const g = r.glyph;
        for (const attr of ['fill_color', 'line_color']) {
            const c = g[attr];
            if (!c) continue;
            if (typeof c === 'string' && c !== 'none') return c;
            if (c.value && typeof c.value === 'string' && c.value !== 'none') return c.value;
        }
        return 'deepskyblue';
    }
"""

# ---------------------------------------------------------------------------
# Mode: bar / line  — snap to nearest X
# ---------------------------------------------------------------------------
_BAR_LINE_JS = """
    const data   = source.data;
    const xvals  = data[X_FIELD];
    const labels = data['label'];
    const hitX   = HIT_X;

""" + _TIP_INIT + _GET_COORDS + _LABEL_STYLE + _GET_GLYPH_COLOR + _TIP_SHOW + """
    let bestIdx = -1, bestDist = Infinity;
    for (let i = 0; i < xvals.length; i++) {
        const d = Math.abs(xvals[i] - cb_obj.x);
        if (d < bestDist) { bestDist = d; bestIdx = i; }
    }
    if (bestIdx < 0 || bestDist > hitX) {
""" + _TIP_HIDE + """
        return;
    }
    const _cdsColor = (source.data['color'] || [])[bestIdx];
    const _color    = _cdsColor || glyphColor(renderers, 0);
    showTip(styledLabel(labels[bestIdx], _color), _vx + 18, _vy - 10, _color);
"""

# ---------------------------------------------------------------------------
# Mode: hbar  — snap to nearest Y row, only inside the bar
# ---------------------------------------------------------------------------
_HBAR_JS = """
    const data   = source.data;
    const xvals  = data['x'];
    const yvals  = data['y'];
    const labels = data['label'];
    const hitY   = HIT_Y;

""" + _TIP_INIT + _GET_COORDS + _LABEL_STYLE + _GET_GLYPH_COLOR + _TIP_SHOW + """
    let bestIdx = -1, bestDist = Infinity;
    for (let i = 0; i < yvals.length; i++) {
        const d = Math.abs(yvals[i] - cb_obj.y);
        if (d < bestDist) { bestDist = d; bestIdx = i; }
    }
    if (bestIdx < 0 || bestDist > hitY || cb_obj.x < 0 || cb_obj.x > xvals[bestIdx] * 1.05) {
""" + _TIP_HIDE + """
        return;
    }
    const _cdsColor = (source.data['color'] || [])[bestIdx];
    const _color    = _cdsColor || glyphColor(renderers, 0);
    showTip(styledLabel(labels[bestIdx], _color), _vx + 18, _vy - 10, _color);
"""

# ---------------------------------------------------------------------------
# Mode: scatter  — nearest point within hit_radius in data space
# ---------------------------------------------------------------------------
_SCATTER_JS = """
    const data      = source.data;
    const xvals     = data['x'];
    const yvals     = data['y'];
    const labels    = data['label'];
    const hitRadius = HIT_RADIUS;

""" + _TIP_INIT + _GET_COORDS + _LABEL_STYLE + _GET_GLYPH_COLOR + _TIP_SHOW + """
    let bestIdx = -1, bestDist = Infinity;
    for (let i = 0; i < xvals.length; i++) {
        const dx = xvals[i] - cb_obj.x;
        const dy = yvals[i] - cb_obj.y;
        const d  = Math.sqrt(dx*dx + dy*dy);
        if (d < bestDist) { bestDist = d; bestIdx = i; }
    }
    if (bestIdx < 0 || bestDist > hitRadius) {
""" + _TIP_HIDE + """
        return;
    }
    const _cdsColor = (source.data['color'] || [])[bestIdx];
    const _color    = _cdsColor || glyphColor(renderers, 0);
    showTip(styledLabel(labels[bestIdx], _color), _vx + 18, _vy - 10, _color);
"""

# ---------------------------------------------------------------------------
# Mode: pie  — match wedge by angle + radius in data space
# ---------------------------------------------------------------------------
_PIE_JS = """
    const data   = source.data;
    const labels = data['label'];

""" + _TIP_INIT + _GET_COORDS + _LABEL_STYLE + _GET_GLYPH_COLOR + _TIP_SHOW + """
    const cx = cb_obj.x, cy = cb_obj.y;
    const r  = Math.sqrt(cx*cx + cy*cy);
    if (r < INNER_RADIUS || r > OUTER_RADIUS) {
""" + _TIP_HIDE + """
        return;
    }
    let angle = Math.atan2(cy, cx);
    if (angle < 0) angle += 2 * Math.PI;
    const starts = data['start_angle'], ends = data['end_angle'];
    let bestIdx = -1;
    for (let i = 0; i < starts.length; i++) {
        if (angle >= starts[i] && angle <= ends[i]) { bestIdx = i; break; }
    }
    if (bestIdx < 0) {
""" + _TIP_HIDE + """
        return;
    }
    const _color = (source.data['color'] || [])[bestIdx] || glyphColor(renderers, 0);
    showTip(styledLabel(labels[bestIdx], _color), _vx + 18, _vy - 10, _color);
"""

_HIDE_JS = """
    const tip = document.getElementById('echarts-tip');
    if (!tip) return;
    tip.style.opacity = '0';
    tip._visible = false;
    if (tip._hideTimer) clearTimeout(tip._hideTimer);
    tip._hideTimer = setTimeout(() => { tip.style.display = 'none'; }, 200);
"""


def smooth_tip(p, source, mode="bar", lag=0.18, hit_radius=0.5,
               hit_x=0.6, hit_y=0.55,
               pie_inner_radius=0.0, pie_outer_radius=1.0,
               x_field="x"):
    """
    Attach an ECharts-style lerp tooltip to any Bokeh figure.

    Works correctly in dashboards with multiple plots — the tooltip always
    appears next to the cursor on whichever plot is being hovered.

    Parameters
    ----------
    p                : Bokeh figure
    source           : ColumnDataSource with a 'label' column (HTML strings)
    mode             : 'bar' | 'line' | 'hbar' | 'scatter' | 'pie'
    lag              : lerp smoothing (lower = more drag, default 0.18)
    hit_radius       : data-space radius for scatter (default 0.5)
    hit_x            : data-space x-snap threshold for bar/line (default 0.6)
    hit_y            : data-space y-snap threshold for hbar rows (default 0.55)
    pie_inner_radius : inner radius for donut charts (default 0)
    pie_outer_radius : outer radius for pie/donut (default 1.0)
    x_field          : column name for x values (default 'x'; change for varea)
    """
    lag_s     = str(lag)
    renderers = p.renderers

    if mode in ("bar", "line"):
        js = (_BAR_LINE_JS
              .replace("LAG_VALUE", lag_s)
              .replace("HIT_X",     str(hit_x))
              .replace("X_FIELD",   repr(x_field)))
    elif mode == "hbar":
        js = (_HBAR_JS
              .replace("LAG_VALUE", lag_s)
              .replace("HIT_Y",     str(hit_y)))
    elif mode == "scatter":
        js = (_SCATTER_JS
              .replace("LAG_VALUE",  lag_s)
              .replace("HIT_RADIUS", str(hit_radius)))
    elif mode == "pie":
        js = (_PIE_JS
              .replace("LAG_VALUE",    lag_s)
              .replace("INNER_RADIUS", str(pie_inner_radius))
              .replace("OUTER_RADIUS", str(pie_outer_radius)))
    else:
        raise ValueError(f"smooth_tip: unknown mode '{mode}'. "
                         f"Choose bar | line | hbar | scatter | pie")

    p.js_on_event("mousemove",  CustomJS(
        args=dict(source=source, renderers=renderers), code=js))
    p.js_on_event("mouseleave", CustomJS(code=_HIDE_JS))

# ---------------------------------------------------------------------------
# Multi-source scatter tooltip — one callback, global nearest-point search
# ---------------------------------------------------------------------------
# The problem with calling smooth_tip() once per source:
#   • N mousemove callbacks fire in registration order on every mouse move.
#   • Each independently decides "hit" or "miss" and calls showTip/hide.
#   • The LAST callback always wins — if it's a miss it hides the tip even
#     though an earlier source had a perfectly valid hit.
#   • glyphColor(renderers, 0) always reads renderer[0] of the figure, so
#     every cluster gets cluster-A's color.
#
# The fix — smooth_tip_multi():
#   • ONE mousemove callback receives ALL sources + their per-source colors.
#   • Iterates every source, tracks the globally closest point across all.
#   • Only hides if nothing is within hit_radius across ANY source.
#   • Color is read from the winning source's renderer directly.
# ---------------------------------------------------------------------------

_SCATTER_MULTI_JS = """
(function() {
    const allSources  = sources;     // JS array of CDS objects
    const allColors   = colors;      // JS array of hex strings, one per source
    const hitRadius   = HIT_RADIUS;

""" + _TIP_INIT + _GET_COORDS + _LABEL_STYLE + _TIP_SHOW + """

    let bestDist  = Infinity;
    let bestLabel = null;
    let bestColor = null;

    for (let s = 0; s < allSources.length; s++) {
        const data   = allSources[s].data;
        const xvals  = data['x'];
        const yvals  = data['y'];
        const labels = data['label'];
        const color  = allColors[s];

        for (let i = 0; i < xvals.length; i++) {
            const dx = xvals[i] - cb_obj.x;
            const dy = yvals[i] - cb_obj.y;
            const d  = Math.sqrt(dx * dx + dy * dy);
            if (d < bestDist) {
                bestDist  = d;
                bestLabel = labels[i];
                bestColor = color;
            }
        }
    }

    if (bestLabel === null || bestDist > hitRadius) {
""" + _TIP_HIDE + """
        return;
    }

    showTip(styledLabel(bestLabel, bestColor), _vx + 18, _vy - 10, bestColor);
})();
"""


def _renderer_fill_color(r):
    """Extract a CSS color string from a GlyphRenderer."""
    if not r or not r.glyph:
        return "deepskyblue"
    g = r.glyph
    for attr in ("fill_color", "line_color"):
        c = getattr(g, attr, None)
        if not c:
            continue
        if isinstance(c, str) and c != "none":
            return c
        if hasattr(c, "value") and isinstance(c.value, str) and c.value != "none":
            return c.value
    return "deepskyblue"


def smooth_tip_multi_line(p, sources, colors=None, renderers=None,
                          lag=0.18, hit_x=0.6, x_field="x",
                          title=None):
    """
    Combined vertical-crosshair tooltip for multi-line charts.

    On hover, snaps to the nearest X and shows ONE tooltip containing
    a row for every series at that X index — exactly like ECharts'
    "axis pointer" tooltip mode.

    Parameters
    ----------
    p          : Bokeh figure
    sources    : list of ColumnDataSource — each must have x, y, label columns.
                 'label' is used as the per-row text (can contain HTML).
    colors     : list of CSS colour strings, one per source.
                 If None, colours are extracted from p.renderers automatically.
    renderers  : list of GlyphRenderer parallel to sources (used only when
                 colors=None to auto-extract colours).  Defaults to
                 p.renderers[:len(sources)].
    lag        : lerp smoothing (default 0.18)
    hit_x      : data-space x-snap threshold (default 0.6)
    x_field    : column name for x values (default 'x')
    title      : optional HTML string shown as tooltip header, e.g. "X: {x}".
                 Use the literal placeholder ``{x}`` to insert the hovered
                 x value.  If None, no header is added.
    """
    if renderers is None:
        renderers = p.renderers[: len(sources)]
    if colors is None:
        colors = [_renderer_fill_color(r) for r in renderers]

    # Build a JS literal for colors
    colors_json = "[" + ", ".join(f'"{c}"' for c in colors) + "]"

    # title_js: either a template string or empty string
    title_template = title if title is not None else ""

    _MULTI_LINE_JS = ("""
(function() {
    const allSources = SOURCES_ARRAY;
    const allColors  = COLORS_ARRAY;
    const hitX       = HIT_X_VALUE;
    const xField     = X_FIELD_VALUE;
    const titleTpl   = TITLE_TPL;

""" + _TIP_INIT + _GET_COORDS + _LABEL_STYLE + _TIP_SHOW + """

    // ── 1. find the nearest X index (shared across all series) ──────────
    const refData = allSources[0].data;
    const refX    = refData[xField];
    let bestIdx = -1, bestDist = Infinity;
    for (let i = 0; i < refX.length; i++) {
        const d = Math.abs(refX[i] - cb_obj.x);
        if (d < bestDist) { bestDist = d; bestIdx = i; }
    }

    if (bestIdx < 0 || bestDist > hitX) {
""" + _TIP_HIDE + """
        return;
    }

    // ── 2. build one combined tooltip ───────────────────────────────────
    let html = '';
    if (titleTpl) {
        const xVal = refX[bestIdx];
        const header = titleTpl.replace('{x}', xVal);
        html += '<div style="font-weight:700;margin-bottom:4px;color:#555">'
                + header + '</div>';
    }

    for (let s = 0; s < allSources.length; s++) {
        const data   = allSources[s].data;
        const labels = data['label'];
        const color  = allColors[s];
        if (bestIdx >= labels.length) continue;

        // colour swatch + label row
        html += '<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
              + '<span style="display:inline-block;width:9px;height:9px;'
              + 'border-radius:50%;background:' + color + ';flex-shrink:0"></span>'
              + '<span>' + styledLabel(labels[bestIdx], color) + '</span>'
              + '</div>';
    }

    // border colour = first series colour
    const borderColor = allColors[0] || '#e0e0e0';
    showTip(html, _vx + 18, _vy - 10, borderColor);
})();
""")

    lag_s = str(lag)

    # Build JS source array from named args s0, s1, …
    sources_js = "[" + ", ".join(f"s{i}" for i in range(len(sources))) + "]"

    js = (_MULTI_LINE_JS
          .replace("LAG_VALUE",    lag_s)
          .replace("SOURCES_ARRAY", sources_js)
          .replace("COLORS_ARRAY",  colors_json)
          .replace("HIT_X_VALUE",   str(hit_x))
          .replace("X_FIELD_VALUE", repr(x_field))
          .replace("TITLE_TPL",     repr(title_template)))

    args = {f"s{i}": src for i, src in enumerate(sources)}

    p.js_on_event("mousemove",  CustomJS(args=args, code=js))
    p.js_on_event("mouseleave", CustomJS(code=_HIDE_JS))


def smooth_tip_multi_varea(p, sources, colors=None, renderers=None,
                           lag=0.18, hit_x=1.0,
                           x_field="x", upper_field="upper", lower_field="lower",
                           title=None):
    """
    Combined vertical-crosshair tooltip for varea charts with multiple bands.

    Works like smooth_tip_multi_line but reads upper/lower fields instead of y.
    Shows ONE tooltip at the hovered X with a row per band showing both edges.

    Parameters
    ----------
    p            : Bokeh figure
    sources      : list of ColumnDataSource — each must have x, upper, lower, label.
    colors       : list of CSS colour strings, one per source. Auto-detected if None.
    renderers    : list of GlyphRenderer parallel to sources (for color auto-detect).
    lag          : lerp smoothing (default 0.18)
    hit_x        : data-space x-snap threshold (default 1.0)
    x_field      : x column name (default 'x')
    upper_field  : upper boundary column name (default 'upper')
    lower_field  : lower boundary column name (default 'lower')
    title        : optional header template, e.g. "Day {x}". Use {x} as placeholder.
    """
    if renderers is None:
        renderers = p.renderers[: len(sources)]
    if colors is None:
        colors = [_renderer_fill_color(r) for r in renderers]

    colors_json    = "[" + ", ".join(f'"{c}"' for c in colors) + "]"
    title_template = title if title is not None else ""

    _VAREA_MULTI_JS = ("""
(function() {
    const allSources  = SOURCES_ARRAY;
    const allColors   = COLORS_ARRAY;
    const hitX        = HIT_X_VALUE;
    const xField      = X_FIELD_VALUE;
    const upperField  = UPPER_FIELD_VALUE;
    const lowerField  = LOWER_FIELD_VALUE;
    const titleTpl    = TITLE_TPL;

""" + _TIP_INIT + _GET_COORDS + _LABEL_STYLE + _TIP_SHOW + """

    // ── 1. snap to nearest X (use first source as reference) ────────────
    const refX = allSources[0].data[xField];
    let bestIdx = -1, bestDist = Infinity;
    for (let i = 0; i < refX.length; i++) {
        const d = Math.abs(refX[i] - cb_obj.x);
        if (d < bestDist) { bestDist = d; bestIdx = i; }
    }

    if (bestIdx < 0 || bestDist > hitX) {
""" + _TIP_HIDE + """
        return;
    }

    // ── 2. check hovered Y is inside at least one band ──────────────────
    let anyHit = false;
    for (let s = 0; s < allSources.length; s++) {
        const d = allSources[s].data;
        // generous check — show tooltip anywhere near the chart vertically
        if (cb_obj.y >= (d[lowerField][bestIdx] || 0) - 4 &&
            cb_obj.y <= (d[upperField][bestIdx] || 0) + 4) {
            anyHit = true; break;
        }
    }
    // if cursor is clearly outside every band, still show — varea charts
    // often have large empty areas, so we rely on x-snap only
    // (remove the anyHit guard entirely for full vline behaviour)

    // ── 3. build combined tooltip ────────────────────────────────────────
    let html = '';
    if (titleTpl) {
        const header = titleTpl.replace('{x}', refX[bestIdx]);
        html += '<div style="font-weight:700;margin-bottom:5px;color:#555">'
              + header + '</div>';
    }

    for (let s = 0; s < allSources.length; s++) {
        const data   = allSources[s].data;
        const labels = data['label'];
        const color  = allColors[s];
        if (bestIdx >= labels.length) continue;
        html += '<div style="display:flex;align-items:flex-start;gap:6px;margin:2px 0">'
              + '<span style="display:inline-block;width:9px;height:9px;margin-top:3px;'
              + 'border-radius:3px;background:' + color + ';opacity:0.75;flex-shrink:0"></span>'
              + '<span>' + styledLabel(labels[bestIdx], color) + '</span>'
              + '</div>';
    }

    const borderColor = allColors[0] || '#e0e0e0';
    showTip(html, _vx + 18, _vy - 10, borderColor);
})();
""")

    sources_js = "[" + ", ".join(f"s{i}" for i in range(len(sources))) + "]"

    js = (_VAREA_MULTI_JS
          .replace("LAG_VALUE",         str(lag))
          .replace("SOURCES_ARRAY",     sources_js)
          .replace("COLORS_ARRAY",      colors_json)
          .replace("HIT_X_VALUE",       str(hit_x))
          .replace("X_FIELD_VALUE",     repr(x_field))
          .replace("UPPER_FIELD_VALUE", repr(upper_field))
          .replace("LOWER_FIELD_VALUE", repr(lower_field))
          .replace("TITLE_TPL",         repr(title_template)))

    args = {f"s{i}": src for i, src in enumerate(sources)}

    p.js_on_event("mousemove",  CustomJS(args=args, code=js))
    p.js_on_event("mouseleave", CustomJS(code=_HIDE_JS))


def smooth_tip_multi(p, sources, renderers=None, lag=0.18, hit_radius=6):
    """
    Single-callback multi-source scatter tooltip.

    Registers ONE mousemove on `p` that searches all sources simultaneously
    and shows the tooltip for the globally nearest point, with the correct
    per-source color.  Use this instead of calling smooth_tip() once per
    source — the per-call approach causes last-callback-wins flickering and
    always shows the first renderer's color.

    Parameters
    ----------
    p          : Bokeh figure
    sources    : list of ColumnDataSource — each must have x, y, label columns
    renderers  : list of GlyphRenderer parallel to sources (used for color).
                 If None, p.renderers[:len(sources)] is used.
    lag        : lerp smoothing factor (default 0.18)
    hit_radius : data-space hit radius (default 6)
    """
    if renderers is None:
        renderers = p.renderers[: len(sources)]

    colors = [_renderer_fill_color(r) for r in renderers]

    js = (_SCATTER_MULTI_JS
          .replace("LAG_VALUE",  str(lag))
          .replace("HIT_RADIUS", str(hit_radius)))

    args = {f"s{i}": src for i, src in enumerate(sources)}
    args["colors"] = colors

    # Build the JS array literal for sources from the named args
    sources_js = "[" + ", ".join(f"s{i}" for i in range(len(sources))) + "]"
    js = "const sources = " + sources_js + ";\n" + js

    p.js_on_event("mousemove",  CustomJS(args=args, code=js))
    p.js_on_event("mouseleave", CustomJS(code=_HIDE_JS))
