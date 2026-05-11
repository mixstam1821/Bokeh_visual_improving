"""
bokeh_anim.py  

Usage
-----
    from bokeh_anim import anim, anim_pie, anim_scatter

    # --- line / bar / hbar / varea ---
    p = figure(...)
    p.line('x', 'y', source=source)
    anim(p, easing='elasticOut', duration=1000)
    show(p)

    # --- pie ---
    p2, source2 = figure(...), ColumnDataSource(...)
    p2.wedge(...)
    anim_pie(p2, source2, easing='backOut', duration=1200)
    show(p2)

    # --- scatter ---
    p3 = figure(...)
    r = p3.circle('x', 'y', source=src)
    anim_scatter(p3, src, easing='elasticOut', duration=900)
    show(p3)

Available easings
-----------------
    'linearIn'
    'quadIn'    'quadOut'    'quadInOut'
    'cubicIn'   'cubicOut'   'cubicInOut'
    'quartIn'   'quartOut'   'quartInOut'
    'quintIn'   'quintOut'   'quintInOut'
    'sineIn'    'sineOut'    'sineInOut'
    'expoIn'    'expoOut'    'expoInOut'
    'circIn'    'circOut'    'circInOut'
    'backIn'    'backOut'    'backInOut'
    'elasticIn' 'elasticOut' 'elasticInOut'
    'bounceIn'  'bounceOut'  'bounceInOut'
"""

import json
from bokeh.models import CustomJS
from bokeh.io import curdoc

# ---------------------------------------------------------------------------
# Easing library (var so re-declaration across IIFEs is safe)
# ---------------------------------------------------------------------------
_JS_EASINGS = """
    var _E = (function() {
        function linearIn(t)  { return t; }

        function quadIn(t)    { return t*t; }
        function quadOut(t)   { return t*(2-t); }
        function quadInOut(t) { return t<0.5 ? 2*t*t : -1+(4-2*t)*t; }

        function cubicIn(t)    { return t*t*t; }
        function cubicOut(t)   { return (--t)*t*t+1; }
        function cubicInOut(t) { return t<0.5 ? 4*t*t*t : (t-1)*(2*t-2)*(2*t-2)+1; }

        function quartIn(t)    { return t*t*t*t; }
        function quartOut(t)   { return 1-(--t)*t*t*t; }
        function quartInOut(t) { return t<0.5 ? 8*t*t*t*t : 1-8*(--t)*t*t*t; }

        function quintIn(t)    { return t*t*t*t*t; }
        function quintOut(t)   { return 1+(--t)*t*t*t*t; }
        function quintInOut(t) { return t<0.5 ? 16*t*t*t*t*t : 1+16*(--t)*t*t*t*t; }

        function sineIn(t)    { return 1-Math.cos(t*Math.PI/2); }
        function sineOut(t)   { return Math.sin(t*Math.PI/2); }
        function sineInOut(t) { return -(Math.cos(Math.PI*t)-1)/2; }

        function expoIn(t)    { return t===0 ? 0 : Math.pow(2,10*t-10); }
        function expoOut(t)   { return t===1 ? 1 : 1-Math.pow(2,-10*t); }
        function expoInOut(t) {
            if(t===0||t===1) return t;
            return t<0.5 ? Math.pow(2,20*t-10)/2 : (2-Math.pow(2,-20*t+10))/2;
        }

        function circIn(t)    { return 1-Math.sqrt(1-t*t); }
        function circOut(t)   { return Math.sqrt(1-(--t)*t); }
        function circInOut(t) {
            return t<0.5 ? (1-Math.sqrt(1-4*t*t))/2
                         : (Math.sqrt(1-(2*t-2)*(2*t-2))+1)/2;
        }

        var c1=1.70158, c2=c1*1.525, c3=c1+1;
        function backIn(t)    { return c3*t*t*t - c1*t*t; }
        function backOut(t)   { return 1+c3*(--t)*t*t+c1*t*t; }
        function backInOut(t) {
            return t<0.5 ? (Math.pow(2*t,2)*((c2+1)*2*t-c2))/2
                         : (Math.pow(2*t-2,2)*((c2+1)*(2*t-2)+c2)+2)/2;
        }

        var c4=2*Math.PI/3, c5=2*Math.PI/4.5;
        function elasticIn(t) {
            if(t===0||t===1) return t;
            return -Math.pow(2,10*t-10)*Math.sin((t*10-10.75)*c4);
        }
        function elasticOut(t) {
            if(t===0||t===1) return t;
            return Math.pow(2,-10*t)*Math.sin((t*10-0.75)*c4)+1;
        }
        function elasticInOut(t) {
            if(t===0||t===1) return t;
            return t<0.5
                ? -(Math.pow(2,20*t-10)*Math.sin((20*t-11.125)*c5))/2
                : (Math.pow(2,-20*t+10)*Math.sin((20*t-11.125)*c5))/2+1;
        }

        function bounceOut(t) {
            var n1=7.5625,d1=2.75;
            if(t<1/d1)        return n1*t*t;
            else if(t<2/d1)   { t-=1.5/d1;   return n1*t*t+0.75; }
            else if(t<2.5/d1) { t-=2.25/d1;  return n1*t*t+0.9375; }
            else              { t-=2.625/d1; return n1*t*t+0.984375; }
        }
        function bounceIn(t)    { return 1-bounceOut(1-t); }
        function bounceInOut(t) { return t<0.5?(1-bounceOut(1-2*t))/2:(1+bounceOut(2*t-1))/2; }

        return {
            linearIn,
            quadIn,quadOut,quadInOut,
            cubicIn,cubicOut,cubicInOut,
            quartIn,quartOut,quartInOut,
            quintIn,quintOut,quintInOut,
            sineIn,sineOut,sineInOut,
            expoIn,expoOut,expoInOut,
            circIn,circOut,circInOut,
            backIn,backOut,backInOut,
            elasticIn,elasticOut,elasticInOut,
            bounceIn,bounceOut,bounceInOut
        };
    })();
"""

# ---------------------------------------------------------------------------
# Main animation template  (line / bar / hbar / varea)
# ---------------------------------------------------------------------------
_JS_TEMPLATE = """
(function (sources) {
__EASINGS__
    var easeFn   = _E[__EASING__] || _E.bounceOut;
    var DURATION = __DURATION__;
    var renderers = __RENDERERS__;

    function makeAnimator(desc, src) {
        var startTime = null, rafId = null;

        // ── tip-dot element (line only) ──────────────────────────────────
        var tipDot = null;
        if (desc.kind === 'line' && desc.showTip) {
            tipDot = document.getElementById('bk-tip-dot-' + desc.tipId);
            if (!tipDot) {
                tipDot = document.createElement('div');
                tipDot.id = 'bk-tip-dot-' + desc.tipId;
                Object.assign(tipDot.style, {
                    position: 'fixed',
                    width: '10px', height: '10px',
                    borderRadius: '50%',
                    background: desc.tipColor || '#fff',
                    boxShadow: '0 0 0 3px ' + (desc.tipColor || '#3498db') +
                               ', 0 0 10px 4px ' + (desc.tipColor || '#3498db') + '88',
                    pointerEvents: 'none',
                    zIndex: '9998',
                    opacity: '0',
                    transform: 'translate(-50%, -50%)',
                    transition: 'opacity 0.15s ease',
                });
                document.body.appendChild(tipDot);
            }
        }

        function moveTipDot(xVal, yVal) {
            if (!tipDot || !desc.plotRef) return;
            // Use the plot's frame to convert data → screen coords
            var frame = desc.plotRef.inner_width !== undefined ? desc.plotRef : null;
            if (!frame) return;
            var canvas = document.querySelector('canvas.bk-canvas');
            if (!canvas) return;
            var rect = canvas.getBoundingClientRect();
            var sx = desc.plotRef.frame_x + (xVal - desc.xRange[0]) /
                     (desc.xRange[1] - desc.xRange[0]) * desc.plotRef.inner_width;
            var sy = desc.plotRef.frame_y + (1 - (yVal - desc.yRange[0]) /
                     (desc.yRange[1] - desc.yRange[0])) * desc.plotRef.inner_height;
            tipDot.style.left = (rect.left + sx) + 'px';
            tipDot.style.top  = (rect.top  + sy) + 'px';
            tipDot.style.opacity = '1';
        }

        function update(progress) {
            var data = src.data;
            if (desc.kind === 'line') {
                var total = desc.fullX.length;
                // Continuous fractional index — e.g. 2.73 means show points 0-2
                // plus a lerped point 73% of the way toward point 3.
                var frac = progress * total;
                var n    = Math.floor(frac);          // whole points already passed
                var rem  = frac - n;                  // 0..1 fraction into next segment
                n = Math.min(n, total - 1);           // clamp so n+1 is always valid

                var xs = desc.fullX.slice(0, n + 1);
                var ys = desc.fullY.slice(0, n + 1);

                // Append the interpolated wavefront point (skip at very last frame)
                if (progress < 1.0 && n + 1 < total) {
                    xs.push(desc.fullX[n] + rem * (desc.fullX[n+1] - desc.fullX[n]));
                    ys.push(desc.fullY[n] + rem * (desc.fullY[n+1] - desc.fullY[n]));
                }

                data[desc.xField] = xs;
                data[desc.yField] = ys;

                // move glow tip to current wavefront
                if (tipDot && xs.length > 0) {
                    moveTipDot(xs[xs.length-1], ys[ys.length-1]);
                }
            } else if (desc.kind === 'varea') {
                data[desc.topField]    = desc.fullTop.map(function(v){ return v * progress; });
                data[desc.bottomField] = desc.fullBottom.map(function(v){ return v * progress; });
            } else {
                // bar / hbar
                data[desc.topField] = desc.fullTop.map(function(v){ return v * progress; });
            }
            src.change.emit();
        }

        function step(ts) {
            if (startTime === null) startTime = ts;
            var raw = Math.min((ts - startTime) / DURATION, 1.0);
            update(easeFn(raw));
            if (raw < 1.0) {
                rafId = requestAnimationFrame(step);
            } else {
                // animation done — fade out tip dot
                if (tipDot) { tipDot.style.opacity = '0'; }
            }
        }

        function start() {
            if (rafId !== null) cancelAnimationFrame(rafId);
            startTime = null;
            var data = src.data;
            if (desc.kind === 'line') {
                data[desc.xField] = [];
                data[desc.yField] = [];
                if (tipDot) { tipDot.style.opacity = '0'; }
            } else if (desc.kind === 'varea') {
                data[desc.topField]    = desc.fullTop.map(function(){ return 0; });
                data[desc.bottomField] = desc.fullBottom.map(function(){ return 0; });
            } else {
                data[desc.topField] = desc.fullTop.map(function(){ return 0; });
            }
            src.change.emit();
            requestAnimationFrame(step);
        }
        return { desc: desc, start: start };
    }

    if (!window.__bk_anim_handles__) window.__bk_anim_handles__ = {};

    renderers.forEach(function(desc, i) {
        var handle = makeAnimator(desc, sources[i]);
        if (desc.handleId) window.__bk_anim_handles__[desc.handleId] = handle;
        setTimeout(handle.start, desc.delay);
    });

})([__SOURCES_ARRAY__]);
"""

# Legend-toggle callback
_JS_LEGEND_CB = """
    if (!cb_obj.visible) return;
__EASINGS__
    var easeFn   = _E[__EASING__] || _E.bounceOut;
    var DURATION = __DURATION__;
    // Read desc LIVE from window handle so dropdown-swapped fullTop is used.
    // Falls back to the frozen desc if the handle isn't registered yet.
    var _handleId   = __HANDLE_ID__;
    var _liveHandle = (window.__bk_anim_handles__ || {})[_handleId];
    var desc        = _liveHandle ? _liveHandle.desc : __DESC__;
    var startTime   = null;

    function update(progress) {
        var data = src.data;
        if (desc.kind === 'line') {
            var total = desc.fullX.length;
            var frac  = progress * total;
            var n     = Math.floor(frac);
            var rem   = frac - n;
            n = Math.min(n, total - 1);
            var xs = desc.fullX.slice(0, n + 1);
            var ys = desc.fullY.slice(0, n + 1);
            if (progress < 1.0 && n + 1 < total) {
                xs.push(desc.fullX[n] + rem * (desc.fullX[n+1] - desc.fullX[n]));
                ys.push(desc.fullY[n] + rem * (desc.fullY[n+1] - desc.fullY[n]));
            }
            data[desc.xField] = xs;
            data[desc.yField] = ys;
        } else if (desc.kind === 'varea') {
            data[desc.topField]    = desc.fullTop.map(function(v){ return v * progress; });
            data[desc.bottomField] = desc.fullBottom.map(function(v){ return v * progress; });
        } else {
            data[desc.topField] = desc.fullTop.map(function(v){ return v * progress; });
        }
        src.change.emit();
    }

    var d = src.data;
    if (desc.kind === 'line') { d[desc.xField] = []; d[desc.yField] = []; }
    else if (desc.kind === 'varea') {
        d[desc.topField]    = desc.fullTop.map(function(){ return 0; });
        d[desc.bottomField] = desc.fullBottom.map(function(){ return 0; });
    }
    else { d[desc.topField] = desc.fullTop.map(function(){ return 0; }); }
    src.change.emit();

    function step(ts) {
        if (startTime === null) startTime = ts;
        var raw = Math.min((ts - startTime) / DURATION, 1.0);
        update(easeFn(raw));
        if (raw < 1.0) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
"""

# ---------------------------------------------------------------------------
# Pie animation template
# ---------------------------------------------------------------------------
_JS_PIE = """
(function(src, handleId) {
__EASINGS__
    var easeFn   = _E[__EASING__] || _E.backOut;
    var DURATION = __DURATION__;
    var stagger  = __STAGGER__;

    // timers/rafs so a retrigger can cancel any in-progress animation
    var _timers = [];
    var _rafs   = [];

    function runAnim(starts, ends) {
        _timers.forEach(function(t) { clearTimeout(t); });
        _rafs.forEach(function(r)   { cancelAnimationFrame(r); });
        _timers = []; _rafs = [];

        src.data['end_angle'] = starts.slice();
        src.change.emit();

        starts.forEach(function(startA, i) {
            var endA = ends[i];
            var t = setTimeout(function() {
                var t0 = null;
                function step(ts) {
                    if (t0 === null) t0 = ts;
                    var raw = Math.min((ts - t0) / DURATION, 1.0);
                    var p   = easeFn(raw);
                    var angles = src.data['end_angle'].slice();
                    angles[i] = startA + (endA - startA) * p;
                    src.data['end_angle'] = angles;
                    src.change.emit();
                    if (raw < 1.0) { _rafs.push(requestAnimationFrame(step)); }
                }
                _rafs.push(requestAnimationFrame(step));
            }, i * stagger);
            _timers.push(t);
        });
    }

    var fullStarts = src.data['start_angle'].slice();
    var fullEnds   = src.data['end_angle'].slice();
    runAnim(fullStarts, fullEnds);

    if (!window.__bk_pie_handles__) window.__bk_pie_handles__ = {};
    window.__bk_pie_handles__[handleId] = {
        // retrigger(d) — d must have: starts, ends, colors, labels, label_legend
        // Atomically updates all source columns THEN collapses+animates,
        // so there is never a flash of wrong colors or angles.
        retrigger: function(d) {
            // 1. Write new non-angle columns while end_angle still shows old state
            src.data['color']        = d.colors.slice();
            src.data['label']        = d.labels.slice();
            src.data['label_legend'] = d.label_legend.slice();
            src.data['start_angle']  = d.starts.slice();
            // 2. runAnim immediately collapses end_angle → starts, then sweeps
            runAnim(d.starts, d.ends);
        }
    };
})(src, __HANDLE_ID__);
"""

# ---------------------------------------------------------------------------
# Scatter pop-in template
# ---------------------------------------------------------------------------
_JS_SCATTER = """
(function(src) {
__EASINGS__
    var easeFn    = _E[__EASING__] || _E.elasticOut;
    var DURATION  = __DURATION__;
    var stagger   = __STAGGER__;
    var sizeField = __SIZE_FIELD__;
    var handleId  = __HANDLE_ID__;

    // Store the true target sizes permanently so retrigger() always
    // has access to them even after sizes are zeroed during animation.
    var fullSize = src.data[sizeField].slice();

    // Active RAF ids and timer ids — cancelled before each retrigger so
    // a fast double-click never leaves ghost animations running.
    var _rafs   = [];
    var _timers = [];

    function cancelAll() {
        _rafs.forEach(function(id)   { cancelAnimationFrame(id); });
        _timers.forEach(function(id) { clearTimeout(id); });
        _rafs   = [];
        _timers = [];
    }

    function runAnim() {
        cancelAll();
        var n = fullSize.length;
        // collapse to zero first so re-entry always starts from invisible
        src.data[sizeField] = fullSize.map(function() { return 0; });
        src.change.emit();

        for (var i = 0; i < n; i++) {
            (function(idx) {
                var target = fullSize[idx];
                var t = setTimeout(function() {
                    var t0 = null;
                    function step(ts) {
                        if (t0 === null) t0 = ts;
                        var raw   = Math.min((ts - t0) / DURATION, 1.0);
                        var sizes = src.data[sizeField].slice();
                        sizes[idx] = target * easeFn(raw);
                        src.data[sizeField] = sizes;
                        src.change.emit();
                        if (raw < 1.0) {
                            _rafs.push(requestAnimationFrame(step));
                        }
                    }
                    _rafs.push(requestAnimationFrame(step));
                }, idx * stagger);
                _timers.push(t);
            })(i);
        }
    }

    // Initial entrance animation
    runAnim();

    // Expose handle so checkboxes, legend callbacks, and dropdowns can
    // call retrigger() to replay the entrance animation on demand.
    if (!window.__bk_scatter_handles__) window.__bk_scatter_handles__ = {};
    window.__bk_scatter_handles__[handleId] = {
        retrigger: runAnim,
        src:       src,
        sizeField: sizeField,
    };
})(src);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_field(spec):
    if isinstance(spec, str):
        return spec
    if hasattr(spec, "field"):
        return spec.field
    if hasattr(spec, "get"):
        return spec.get("field", str(spec))
    return str(spec)


def _renderer_kind(renderer):
    t = type(renderer.glyph).__name__
    if t == "Line":   return "line"
    if t == "VBar":   return "bar"
    if t == "HBar":   return "hbar"
    if t == "Quad":   return "bar"
    if t == "VArea":  return "varea"
    return "unknown"


def _fill_template(template, easing, duration, **kwargs):
    code = template.replace("__EASINGS__",  _JS_EASINGS)
    code = code.replace("__EASING__",       repr(easing))
    code = code.replace("__DURATION__",     str(duration))
    for k, v in kwargs.items():
        code = code.replace(f"__{k.upper()}__", v)
    return code


# ---------------------------------------------------------------------------
# Public: EASINGS list
# ---------------------------------------------------------------------------
EASINGS = [
    "linearIn",
    "quadIn",    "quadOut",    "quadInOut",
    "cubicIn",   "cubicOut",   "cubicInOut",
    "quartIn",   "quartOut",   "quartInOut",
    "quintIn",   "quintOut",   "quintInOut",
    "sineIn",    "sineOut",    "sineInOut",
    "expoIn",    "expoOut",    "expoInOut",
    "circIn",    "circOut",    "circInOut",
    "backIn",    "backOut",    "backInOut",
    "elasticIn", "elasticOut", "elasticInOut",
    "bounceIn",  "bounceOut",  "bounceInOut",
]


# ---------------------------------------------------------------------------
# Public: anim()  — line / bar / hbar / varea
# ---------------------------------------------------------------------------

def anim(p, easing="bounceOut", duration=900, delay=0,
         line_tip=True, line_tip_color=None, handle_id=None):
    """
    Attach entrance + legend-retrigger animation to a Bokeh figure.

    Parameters
    ----------
    p               : bokeh Figure
    easing          : one of bokeh_anim.EASINGS  (default 'bounceOut')
    duration        : total animation duration in ms  (default 900)
    delay           : ms before first renderer starts (default 0)
    line_tip        : show glowing dot at line wavefront (default True)
    line_tip_color  : CSS colour for the tip dot (default: auto from line colour)
    handle_id       : optional string prefix for window.__bk_anim_handles__ keys.
                      Each renderer gets key  "{handle_id}_{renderer_index}".
                      Pass the same prefix to the dropdown CustomJS so it can
                      call  window.__bk_anim_handles__['myplot_0'].retrigger(newVals)
                      to swap data + re-animate without duplicating easing code.
                      If None, handles are still registered using the figure id.
    """
    doc = curdoc()

    renderers = [r for r in p.renderers if hasattr(r, "glyph")]
    if not renderers:
        return

    # Use caller-supplied prefix or fall back to the figure's id
    _hid_prefix = handle_id if handle_id is not None else p.id

    stagger = {"line": 80, "bar": 60, "varea": 50}
    descs   = []
    cb_args = {}
    tip_id  = 0

    for i, r in enumerate(renderers):
        kind = _renderer_kind(r)
        if kind == "unknown":
            continue

        src = r.data_source
        cb_args[f"s{i}"] = src

        if kind == "line":
            xf, yf = _get_field(r.glyph.x), _get_field(r.glyph.y)
            full_x, full_y = list(src.data[xf]), list(src.data[yf])
            src.data[xf] = []
            src.data[yf] = []
            # pick tip colour
            col = line_tip_color
            if col is None:
                lc = r.glyph.line_color
                col = lc if isinstance(lc, str) else "#3498db"
            descs.append({
                "kind": "line", "xField": xf, "yField": yf,
                "topField": None, "bottomField": None,
                "fullX": full_x, "fullY": full_y, "fullTop": [], "fullBottom": [],
                "delay": delay + len(descs) * stagger["line"],
                "showTip": line_tip, "tipId": tip_id, "tipColor": col,
                # plot geometry placeholders — filled client-side via plotRef
                "plotRef": None, "xRange": [0, 1], "yRange": [0, 1],
                "handleId": f"{_hid_prefix}_{len(descs)}",
            })
            tip_id += 1

        elif kind == "hbar":
            tf = _get_field(r.glyph.right)
            full_top = list(src.data[tf])
            src.data[tf] = [0.0] * len(full_top)
            descs.append({
                "kind": "bar", "xField": None, "yField": None,
                "topField": tf, "bottomField": None,
                "fullX": [], "fullY": [], "fullTop": full_top, "fullBottom": [],
                "delay": delay + len(descs) * stagger["bar"],
                "showTip": False, "tipId": -1, "tipColor": "",
                "plotRef": None, "xRange": [0,1], "yRange": [0,1],
                "handleId": f"{_hid_prefix}_{len(descs)}",
            })

        elif kind == "varea":
            tf  = _get_field(r.glyph.y2)   # top
            bf  = _get_field(r.glyph.y1)   # bottom
            xf  = _get_field(r.glyph.x)
            full_top    = list(src.data[tf])
            full_bottom = list(src.data[bf])
            src.data[tf] = [0.0] * len(full_top)
            src.data[bf] = [0.0] * len(full_bottom)
            descs.append({
                "kind": "varea", "xField": xf, "yField": None,
                "topField": tf, "bottomField": bf,
                "fullX": [], "fullY": [], "fullTop": full_top, "fullBottom": full_bottom,
                "delay": delay + len(descs) * stagger["varea"],
                "showTip": False, "tipId": -1, "tipColor": "",
                "plotRef": None, "xRange": [0,1], "yRange": [0,1],
                "handleId": f"{_hid_prefix}_{len(descs)}",
            })

        else:  # bar (vbar / quad)
            tf = _get_field(r.glyph.top)
            full_top = list(src.data[tf])
            src.data[tf] = [0.0] * len(full_top)
            descs.append({
                "kind": "bar", "xField": None, "yField": None,
                "topField": tf, "bottomField": None,
                "fullX": [], "fullY": [], "fullTop": full_top, "fullBottom": [],
                "delay": delay + len(descs) * stagger["bar"],
                "showTip": False, "tipId": -1, "tipColor": "",
                "plotRef": None, "xRange": [0,1], "yRange": [0,1],
                "handleId": f"{_hid_prefix}_{len(descs)}",
            })

    if not descs:
        return {}

    sources_array = ", ".join(f"s{i}" for i in range(len(descs)))
    code = _fill_template(_JS_TEMPLATE, easing, duration,
                          renderers=json.dumps(descs),
                          sources_array=sources_array)
    doc.js_on_event("document_ready", CustomJS(args=cb_args, code=code))

    # legend re-trigger — reads desc live from window handle (so swapped fullTop is used)
    anim_renderers = [r for r in p.renderers
                      if hasattr(r, "glyph") and _renderer_kind(r) != "unknown"]
    for idx, r in enumerate(anim_renderers):
        if idx >= len(descs):
            break
        src = cb_args[f"s{idx}"]
        hid = descs[idx]["handleId"]
        cb_code = _fill_template(_JS_LEGEND_CB, easing, duration,
                                 desc=json.dumps(descs[idx]),
                                 handle_id=repr(hid))
        r.js_on_change("visible", CustomJS(args={"src": src}, code=cb_code))

    # Return a dict of handleId → renderer_index so callers know the keys
    return {desc["handleId"]: i for i, desc in enumerate(descs)}


# ---------------------------------------------------------------------------
# Public: anim_pie()
# ---------------------------------------------------------------------------

def anim_pie(p, source, easing="backOut", duration=600, stagger=120, handle_id=None):
    """
    Animate a pie / donut chart: each wedge sweeps in one after another.

    Parameters
    ----------
    p         : bokeh Figure containing the wedge renderer
    source    : ColumnDataSource with start_angle / end_angle
    easing    : easing name (default 'backOut')
    duration  : per-wedge sweep duration in ms (default 600)
    stagger   : ms between wedge starts (default 120)
    handle_id : key for window.__bk_pie_handles__ — call .retrigger(starts, ends)
                from a dropdown CustomJS to re-animate with new data.
    """
    doc = curdoc()
    hid = handle_id if handle_id is not None else p.id
    code = (_JS_PIE
            .replace("__EASINGS__",   _JS_EASINGS)
            .replace("__EASING__",    repr(easing))
            .replace("__DURATION__",  str(duration))
            .replace("__STAGGER__",   str(stagger))
            .replace("__HANDLE_ID__", repr(hid)))
    doc.js_on_event("document_ready", CustomJS(args={"src": source}, code=code))


# ---------------------------------------------------------------------------
# Public: anim_scatter()
# ---------------------------------------------------------------------------

def anim_scatter(p, source, size_field="size", easing="elasticOut",
                 duration=500, stagger=40, handle_id=None):
    """
    Animate scatter points: each pops in with a scale-up animation.

    Parameters
    ----------
    p          : bokeh Figure
    source     : ColumnDataSource
    size_field : column name used for glyph size (default 'size')
    easing     : easing name (default 'elasticOut')
    duration   : per-point animation duration in ms (default 500)
    stagger    : ms between successive point starts (default 40)
    handle_id  : key for window.__bk_scatter_handles__ — call
                 .retrigger() from a checkbox / legend CustomJS to
                 replay the entrance animation when a cluster is
                 toggled back on. Falls back to a unique string
                 derived from the figure id if not supplied.
    """
    doc = curdoc()
    hid = handle_id if handle_id is not None else f"{p.id}_scatter_{id(source)}"
    code = (_JS_SCATTER
            .replace("__EASINGS__",    _JS_EASINGS)
            .replace("__EASING__",     repr(easing))
            .replace("__DURATION__",   str(duration))
            .replace("__STAGGER__",    str(stagger))
            .replace("__SIZE_FIELD__", repr(size_field))
            .replace("__HANDLE_ID__",  repr(hid)))
    doc.js_on_event("document_ready", CustomJS(args={"src": source}, code=code))
    return hid
