"""Incrementally install Phase 3D connection transitions into v04.

Run in the TouchDesigner Textport while TD_visual_prototype_v04.toe is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\phase3d_builder.py', encoding='utf-8').read())

The builder preserves the Phase 3C renderer, adds bounded visual edge state,
reuses its frame driver, and never saves the project.
"""

ROOT = "/project1/mutual_illumination"
CONTROLS = ROOT + "/visual_controls"
VISUAL_PARAMS = CONTROLS + "/visual_params"
VISUAL_PARAMS_OUT = CONTROLS + "/visual_params_out"
NODE_DATA = ROOT + "/data/node_data"
EDGE_DATA = ROOT + "/graph/edge_data"
GRAPH_EXECUTE = ROOT + "/graph/phase2_graph_execute"
CONNECTION_CALLBACKS = ROOT + "/render_connections/phase2_connection_callbacks"
CONNECTION_RENDERER = ROOT + "/render_connections/phase2_connection_renderer"
TRANSITION_MANAGER = ROOT + "/render_connections/phase3d_transition_manager"
FRAME_EXECUTE = ROOT + "/render_connections/phase3c_frame_execute"
NODE_RENDERER = ROOT + "/render_nodes/phase1a_node_renderer"
PHASE1A_OUT = ROOT + "/output/phase1a_out"
COMPOSITE = ROOT + "/output/phase2_composite"
FINAL_OUT = ROOT + "/output/FINAL_OUT"

P2_KEY, P2_VALUE = "mutual_illumination_phase2", "dynamic_mst_v01"
P3A_KEY, P3A_VALUE = "mutual_illumination_phase3a", "visual_controls_v01"
P3B_KEY, P3B_VALUE = "mutual_illumination_phase3b", "node_glow_breathing_v01"
P3C_KEY, P3C_VALUE = "mutual_illumination_phase3c", "mycelium_connections_v01"
P3D_KEY, P3D_VALUE = "mutual_illumination_phase3d", "connection_transitions_v01"
EXPECTED_PROJECT = "TD_visual_prototype_v04.toe"
WIDTH, HEIGHT = 1280, 720
EDGE_SCHEMA = ("edge_id", "a_id", "b_id", "ax", "ay", "bx", "by",
               "distance", "trunk")
OVERRIDE_MARKER = "\n# === Phase 3D transition overrides ===\n"


# kind, page, name, label, default, min, max
TRANSITION_PARAMETERS = (
    ("toggle", "Transitions", "Enabletransitions", "Enable Transitions", True, 0, 1),
    ("float", "Transitions", "Growthduration", "Growth Duration", 0.72, 0.05, 5.0),
    ("float", "Transitions", "Fadeduration", "Fade Duration", 0.42, 0.05, 3.0),
    ("float", "Transitions", "Growthease", "Growth Ease", 2.2, 0.5, 5.0),
)


TRANSITION_MANAGER_CODE = '''"""Bounded visual state for Phase 3D edge transitions."""
import math

NODE_DATA = "/project1/mutual_illumination/data/node_data"
EDGE_DATA = "/project1/mutual_illumination/graph/edge_data"

_states = {}
_last_time = None
_MAX_STATES = 64

def _pair(a_id, b_id):
    return (min(int(a_id), int(b_id)), max(int(a_id), int(b_id)))

def _current_edges():
    result, table = {}, op(EDGE_DATA)
    if table is None:
        return result
    for row in range(1, table.numRows):
        try:
            a_id, b_id = int(table[row, "a_id"].val), int(table[row, "b_id"].val)
            ax, ay = float(table[row, "ax"].val), float(table[row, "ay"].val)
            bx, by = float(table[row, "bx"].val), float(table[row, "by"].val)
            trunk = bool(int(table[row, "trunk"].val))
            if a_id > b_id:
                a_id, b_id, ax, ay, bx, by = b_id, a_id, bx, by, ax, ay
            distance = math.hypot(bx-ax, by-ay)
            result[(a_id, b_id)] = (a_id, b_id, ax, ay, bx, by,
                                    distance, trunk)
        except (TypeError, ValueError, AttributeError):
            pass
    return result

def _node_positions():
    result, table = {}, op(NODE_DATA)
    if table is None:
        return result
    for row in range(1, table.numRows):
        try:
            result[int(table[row, "id"].val)] = (
                float(table[row, "x"].val), float(table[row, "y"].val))
        except (TypeError, ValueError, AttributeError):
            pass
    return result

def _node_table_empty():
    table = op(NODE_DATA)
    return table is None or table.numRows <= 1

def _state(data, growth=1.0, opacity=1.0, active=True):
    return {"data": data, "growth": float(growth),
            "opacity": float(opacity), "active": bool(active)}

def _follow_nodes(state, positions):
    data = state["data"]
    a_id, b_id, ax, ay, bx, by, distance, trunk = data
    if a_id in positions:
        ax, ay = positions[a_id]
    if b_id in positions:
        bx, by = positions[b_id]
    state["data"] = (a_id, b_id, ax, ay, bx, by,
                     math.hypot(bx-ax, by-ay), trunk)

def clear():
    global _last_time
    _states.clear()
    _last_time = None

def seed_existing(now=None):
    global _last_time
    _states.clear()
    for pair, data in _current_edges().items():
        _states[pair] = _state(data)
    _last_time = float(absTime.seconds if now is None else now)

def needs_cook():
    if _last_time is None:
        return True
    return any((not state["active"] or state["growth"] < 0.9999 or
                state["opacity"] < 0.9999) for state in _states.values())

def state_count():
    return len(_states)

def sync(now, enabled, growth_duration, fade_duration, growth_ease):
    global _last_time
    now = float(now)
    current = _current_edges()

    # Reset is intentionally immediate, even if edge_data has not cooked empty yet.
    if _node_table_empty():
        _states.clear()
        _last_time = now
        return []

    if _last_time is None:
        for pair, data in current.items():
            _states[pair] = _state(data)
        _last_time = now
        return _render_rows(growth_ease)

    dt = max(0.0, now-_last_time)
    _last_time = now
    growth_duration = max(0.001, float(growth_duration))
    fade_duration = max(0.001, float(fade_duration))

    if not enabled:
        _states.clear()
        for pair, data in current.items():
            _states[pair] = _state(data)
        return _render_rows(growth_ease)

    # Advance existing transitions using elapsed time, independent of frame rate.
    for state in _states.values():
        if state["active"]:
            state["growth"] = min(1.0, state["growth"] + dt/growth_duration)
            state["opacity"] = min(1.0, state["opacity"] + dt/fade_duration)
        else:
            state["opacity"] = max(0.0, state["opacity"] - dt/fade_duration)

    # A stable unordered pair never restarts while it remains selected.
    for pair, data in current.items():
        state = _states.get(pair)
        if state is None:
            _states[pair] = _state(data, growth=0.0, opacity=1.0, active=True)
        else:
            state["data"] = data
            state["active"] = True

    current_pairs = set(current)
    for pair, state in _states.items():
        if pair not in current_pairs:
            state["active"] = False

    # Fading geometry follows surviving node IDs, but is never written to edge_data.
    positions = _node_positions()
    for pair, state in _states.items():
        if pair not in current_pairs:
            _follow_nodes(state, positions)

    expired = [pair for pair, state in _states.items()
               if not state["active"] and state["opacity"] <= 0.0001]
    for pair in expired:
        del _states[pair]
    if len(_states) > _MAX_STATES:
        fading = sorted((state["opacity"], pair) for pair, state in _states.items()
                        if not state["active"])
        for opacity, pair in fading[:max(0, len(_states)-_MAX_STATES)]:
            del _states[pair]
    return _render_rows(growth_ease)

def _render_rows(growth_ease):
    power = max(0.01, float(growth_ease))
    result = []
    for pair in sorted(_states):
        state = _states[pair]
        linear = min(1.0, max(0.0, state["growth"]))
        extent = 1.0-(1.0-linear)**power
        result.append(state["data"] +
                      (extent, min(1.0, max(0.0, state["opacity"]))))
    return result
'''


RENDER_OVERRIDES = '''# Phase 3D is appended to the verified Phase 3C callback module.
TRANSITION_MANAGER = "/project1/mutual_illumination/render_connections/phase3d_transition_manager"
_phase3c_visuals = _visuals
_phase3c_draw_curve = _draw_curve
_phase3c_draw_energy = _draw_energy

def _visuals():
    visual = _phase3c_visuals()
    control = op(CONTROLS)
    visual.update({
        "transitions": bool(control.par.Enabletransitions.eval()),
        "growth_duration": max(0.001, float(control.par.Growthduration.eval())),
        "fade_duration": max(0.001, float(control.par.Fadeduration.eval())),
        "growth_ease": max(0.01, float(control.par.Growthease.eval())),
    })
    return visual

def _transition_edges(now, visual):
    manager = op(TRANSITION_MANAGER)
    if manager is None:
        raise RuntimeError("Missing Phase 3D transition manager")
    return manager.module.sync(now, visual["transitions"],
                               visual["growth_duration"],
                               visual["fade_duration"],
                               visual["growth_ease"])

def _draw_curve(image, points, color, alpha, visual, fade_radius,
                branch_detail=False, visible_progress=1.0):
    visible_progress = min(1.0, max(0.0, float(visible_progress)))
    if visible_progress <= 0.0 or alpha <= 0.0:
        return
    if visible_progress >= 0.9999:
        return _phase3c_draw_curve(image, points, color, alpha, visual,
                                   fade_radius, branch_detail=branch_detail)
    chord = math.hypot(points[-1][0]-points[0][0],
                       points[-1][1]-points[0][1])
    sample_count = min(64, max(8, int(chord/18.0)+2))
    samples = _sample_bezier(points, sample_count)
    patterns = ((0.0, 0.42, 0.55),) if branch_detail else _filaments(
        visual["filament_count"])
    spread = 0.0 if branch_detail else visual["filament_spread"]
    sheath_radius = (visual["line_weight"]*
                      (3.4 if branch_detail else visual["sheath_width"])*0.5)
    max_offset = max(abs(item[0]) for item in patterns)*spread
    max_line_radius = max(item[2] for item in patterns)*visual["line_weight"]*0.5
    margin = max(sheath_radius, max_offset+max_line_radius)+AA+2.0
    segment_count = len(samples)-1
    visible_segments = visible_progress*segment_count
    draw_count = min(segment_count, int(math.ceil(visible_segments)))

    for index in range(draw_count):
        fraction = min(1.0, visible_segments-index)
        if fraction <= 0.0:
            continue
        ax, ay = float(samples[index, 0]), float(samples[index, 1])
        full_bx, full_by = float(samples[index+1, 0]), float(samples[index+1, 1])
        bx, by = ax+(full_bx-ax)*fraction, ay+(full_by-ay)*fraction
        dx, dy = bx-ax, by-ay
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            continue
        tx, ty, nx, ny = dx/length, dy/length, -dy/length, dx/length
        x0 = max(0, int(math.floor(min(ax, bx)-margin)))
        x1 = min(WIDTH, int(math.ceil(max(ax, bx)+margin))+1)
        y0 = max(0, int(math.floor(min(ay, by)-margin)))
        y1 = min(HEIGHT, int(math.ceil(max(ay, by)+margin))+1)
        if x0 >= x1 or y0 >= y1:
            continue
        yy, xx = numpy.ogrid[y0:y1, x0:x1]
        along = (xx-ax)*tx+(yy-ay)*ty
        along_out = numpy.maximum(-along, 0.0)+numpy.maximum(along-length, 0.0)
        perpendicular = (xx-ax)*nx+(yy-ay)*ny

        local_t = numpy.clip(along/length, 0.0, 1.0)
        global_t = (index+local_t*fraction)/float(segment_count)
        start_fade = min(0.22, max(0.015, fade_radius/max(chord, 1.0)))
        tip_fade = min(0.035, max(0.012, start_fade*0.65))
        endpoint = numpy.clip(global_t/start_fade, 0.0, 1.0)
        endpoint *= numpy.clip((visible_progress-global_t)/tip_fade, 0.0, 1.0)
        endpoint = endpoint*endpoint*(3.0-2.0*endpoint)

        center_distance = numpy.sqrt(along_out*along_out+perpendicular*perpendicular)
        intensity = (_coverage(center_distance, sheath_radius)*
                     visual["sheath_brightness"])
        for offset, strength, weight in patterns:
            distance = numpy.sqrt(along_out*along_out+
                                  (perpendicular-offset*spread)**2)
            radius = max(0.05, visual["line_weight"]*weight*0.5)
            intensity += _coverage(distance, radius)*strength
        intensity *= endpoint*alpha
        patch = image[y0:y1, x0:x1, :]
        numpy.maximum(patch, intensity[:, :, None]*color, out=patch)

def _draw_side_branch(image, edge, points, alpha, visual, visible_progress):
    a_id, b_id = edge[0], edge[1]
    seed = (a_id*31+b_id*17)%100
    if seed/100.0 > visual["side_branch_amount"]:
        return
    t = 0.34+(seed%25)/100.0
    if visible_progress <= t:
        return
    x, y = _bezier_position(points, t)
    tx, ty = _bezier_tangent(points, t)
    side = -1.0 if seed%2 else 1.0
    nx, ny = -ty*side, tx*side
    length = 20.0+seed%24
    end = (x+tx*length*0.34+nx*length,
           y+ty*length*0.34+ny*length)
    c1 = (x+tx*length*0.18+nx*length*0.18,
          y+ty*length*0.18+ny*length*0.18)
    c2 = (end[0]-tx*length*0.18, end[1]-ty*length*0.18)
    branch_progress = min(1.0, (visible_progress-t)/0.18)
    _draw_curve(image, ((x, y), c1, c2, end), visual["line_color"],
                alpha*0.72, visual, 2.0, branch_detail=True,
                visible_progress=branch_progress)

def _draw_energy(image, edge, points, alpha, now, visual, visible_progress):
    if visual["energy_amount"] <= 0.0 or visual["energy_speed"] <= 0.0:
        return
    if visible_progress >= 0.9999:
        return _phase3c_draw_energy(image, edge, points, alpha, now, visual)
    travel = ((now*visual["energy_speed"]+edge[0]*0.137)%1.18)-0.09
    if travel < 0.0 or travel > visible_progress:
        return
    x, y = _bezier_position(points, travel)
    halo_radius = visual["line_weight"]*2.4+2.0
    margin = int(math.ceil(halo_radius+AA+1.0))
    x0, x1 = max(0, int(x)-margin), min(WIDTH, int(x)+margin+1)
    y0, y1 = max(0, int(y)-margin), min(HEIGHT, int(y)+margin+1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = numpy.ogrid[y0:y1, x0:x1]
    distance = numpy.sqrt((xx-x)**2+(yy-y)**2)
    amount = alpha*visual["energy_amount"]
    intensity = (_coverage(distance, halo_radius)*amount*0.22+
                 _coverage(distance, max(0.5, visual["line_weight"]*0.55))*amount*0.72)
    patch = image[y0:y1, x0:x1, :]
    numpy.maximum(patch, intensity[:, :, None]*visual["core_color"], out=patch)

def onCook(scriptOp):
    visual = _visuals()
    image = numpy.zeros((HEIGHT, WIDTH, 3), dtype=numpy.float32)
    now = float(absTime.seconds)
    for edge in _transition_edges(now, visual):
        a_id, b_id, ax, ay, bx, by, stored_distance, trunk, extent, opacity = edge
        if opacity <= 0.0 or extent <= 0.0:
            continue
        distance = math.hypot(bx-ax, by-ay)
        proximity = max(0.0, 1.0-distance/390.0)
        hierarchy = 1.0 if trunk else visual["branch_brightness"]
        alpha = ((105.0/255.0)*visual["line_brightness"]*hierarchy*
                 (0.5+proximity*0.5)*opacity)
        points = _bezier_points(edge[:8], now, visual)
        _draw_curve(image, points, visual["line_color"], alpha, visual,
                    visual["node_radius"]*1.15, visible_progress=extent)
        if trunk:
            _draw_side_branch(image, edge, points, alpha, visual, extent)
        _draw_energy(image, edge, points, alpha, now, visual, extent)
    numpy.clip(image, 0.0, 1.0, out=image)
    scriptOp.copyNumpyArray(image)
'''


FRAME_EXECUTE_CODE = '''"""Single Phase 3C/3D connection animation driver."""
CONTROLS = "/project1/mutual_illumination/visual_controls"
RENDERER = "/project1/mutual_illumination/render_connections/phase2_connection_renderer"
MANAGER = "/project1/mutual_illumination/render_connections/phase3d_transition_manager"

def onFrameStart(frame):
    controls, renderer, manager = op(CONTROLS), op(RENDERER), op(MANAGER)
    if controls is None or renderer is None or manager is None:
        return
    curve_moves = (float(controls.par.Curveamount.eval()) > 0.0 and
                   float(controls.par.Curvemotion.eval()) > 0.0)
    energy_moves = (float(controls.par.Energyamount.eval()) > 0.0 and
                    float(controls.par.Energyspeed.eval()) > 0.0)
    transition_moves = (bool(controls.par.Enabletransitions.eval()) and
                        manager.module.needs_cook())
    if curve_moves or energy_moves or transition_moves:
        renderer.cook(force=True)

def onStart(): return
def onCreate(): return
def onExit(): return
def onFrameEnd(frame): return
def onPlayStateChange(state): return
def onDeviceChange(): return
'''


def _require(path):
    operator = op(path)
    if operator is None:
        raise RuntimeError("Missing operator: " + path)
    return operator


def _par(operator, name, value):
    parameter = getattr(operator.par, name, None)
    if parameter is None:
        raise RuntimeError("Missing parameter {} on {}".format(name, operator.path))
    parameter.val = value


def _path_from_par(parameter):
    value = parameter.eval()
    return value.path if hasattr(value, "path") else str(value)


def _page(component, name):
    for page in component.customPages:
        if page.name == name:
            return page
    return component.appendCustomPage(name)


def _configure_new(parameters, default, minimum, maximum):
    values = default if isinstance(default, tuple) else (default,)
    for index, parameter in enumerate(parameters):
        value = values[index] if index < len(values) else values[0]
        parameter.default = value
        parameter.val = value
        parameter.min = minimum
        parameter.max = maximum
        parameter.normMin = minimum
        parameter.normMax = maximum
        parameter.clampMin = True
        parameter.clampMax = True


def _ensure_parameter(component, spec):
    kind, page_name, name, label, default, minimum, maximum = spec
    existing = getattr(component.par, name, None)
    if existing is not None:
        return False
    page = _page(component, page_name)
    method = {"float": page.appendFloat, "toggle": page.appendToggle}[kind]
    group = method(name, label=label, replace=False)
    _configure_new(list(group), default, minimum, maximum)
    return True


def _owned(parent, name, kind, initialize=True):
    existing = parent.op(name)
    if existing is not None:
        if existing.fetch(P3D_KEY, None, search=False) != P3D_VALUE:
            raise RuntimeError("Refusing unowned operator: " + existing.path)
        return existing
    created = (parent.create(kind, name) if initialize
               else parent.create(kind, name, initialize=False))
    created.store(P3D_KEY, P3D_VALUE)
    return created


def _validate_v04():
    if project.name != EXPECTED_PROJECT:
        raise RuntimeError(
            "Phase 3D may only run in {}; current project is {}".format(
                EXPECTED_PROJECT, project.name))

    controls = _require(CONTROLS)
    edge_data = _require(EDGE_DATA)
    callbacks = _require(CONNECTION_CALLBACKS)
    renderer = _require(CONNECTION_RENDERER)
    frame_execute = _require(FRAME_EXECUTE)
    graph_execute = _require(GRAPH_EXECUTE)
    node_renderer = _require(NODE_RENDERER)
    composite = _require(COMPOSITE)

    for key, value, operator, label in (
            (P3A_KEY, P3A_VALUE, controls, "Phase 3A controls"),
            (P3B_KEY, P3B_VALUE, controls, "Phase 3B controls"),
            (P3C_KEY, P3C_VALUE, controls, "Phase 3C controls"),
            (P3B_KEY, P3B_VALUE, node_renderer, "Phase 3B node renderer")):
        if operator.fetch(key, None, search=False) != value:
            raise RuntimeError(label + " ownership is missing")
    for operator in (callbacks, renderer, frame_execute):
        if operator.fetch(P3C_KEY, None, search=False) != P3C_VALUE:
            raise RuntimeError("Phase 3C ownership missing on " + operator.path)
    for operator in (callbacks, renderer, graph_execute, composite):
        if operator.fetch(P2_KEY, None, search=False) != P2_VALUE:
            raise RuntimeError("Phase 2 ownership missing on " + operator.path)
    if "Phase 3C local Bezier mycelium connection renderer" not in callbacks.text:
        raise RuntimeError("Connection callbacks are not the verified Phase 3C code")

    headers = tuple(cell.val for cell in edge_data.row(0))
    if headers != EDGE_SCHEMA:
        raise RuntimeError("edge_data schema changed: " + repr(headers))
    if not bool(graph_execute.par.active.eval()):
        raise RuntimeError("Phase 2 graph Execute DAT is not active")
    if list(composite.inputs) != [_require(PHASE1A_OUT)]:
        raise RuntimeError("Protected Composite wire is not phase1a_out")
    if _path_from_par(composite.par.top) != renderer.path:
        raise RuntimeError("Protected Composite TOP parameter is incorrect")
    if str(composite.par.operand.eval()).lower() != "add":
        raise RuntimeError("Protected Composite operation is not Add")
    composite.cook(force=True)
    if (int(composite.width), int(composite.height)) != (WIDTH, HEIGHT):
        raise RuntimeError("Protected Composite is not 1280x720")
    if list(composite.errors()):
        raise RuntimeError("Protected Composite has errors: " + repr(composite.errors()))
    return controls, callbacks, renderer, frame_execute


def build_phase3d():
    controls, callbacks, renderer, frame_execute = _validate_v04()
    manager = _owned(renderer.parent(), "phase3d_transition_manager", textDAT)
    manager.nodeX, manager.nodeY = 690, -100
    manager.color = (0.48, 0.24, 0.12)
    manager.comment = "Phase 3D bounded edge transition state"

    old_callbacks = callbacks.text
    old_frame_code = frame_execute.text
    old_frame_active = bool(frame_execute.par.active.eval())
    _par(frame_execute, "active", False)
    try:
        created_count = 0
        for spec in TRANSITION_PARAMETERS:
            if _ensure_parameter(controls, spec):
                created_count += 1

        manager.text = TRANSITION_MANAGER_CODE
        base_callbacks = callbacks.text.split(OVERRIDE_MARKER, 1)[0]
        callbacks.text = base_callbacks + OVERRIDE_MARKER + RENDER_OVERRIDES
        frame_execute.text = FRAME_EXECUTE_CODE
        _par(frame_execute, "framestart", True)
        for name in ("start", "create", "exit", "frameend", "playstatechange",
                     "devicechange"):
            parameter = getattr(frame_execute.par, name, None)
            if parameter is not None:
                parameter.val = False

        params = _require(VISUAL_PARAMS)
        params_out = _require(VISUAL_PARAMS_OUT)
        params.cook(force=True)
        params_out.cook(force=True)
        manager.cook(force=True)
        manager.module.seed_existing(float(absTime.seconds))
        renderer.cook(force=True)
        final_out = _require(FINAL_OUT)
        final_out.cook(force=True)

        for operator in (renderer, final_out):
            if list(operator.errors()):
                raise RuntimeError("Renderer error on {}: {}".format(
                    operator.path, operator.errors()))
        if (int(renderer.width), int(renderer.height)) != (WIDTH, HEIGHT):
            raise RuntimeError("Connection renderer resolution changed during Phase 3D")
        if (int(final_out.width), int(final_out.height)) != (WIDTH, HEIGHT):
            raise RuntimeError("FINAL_OUT resolution changed during Phase 3D")

        callbacks.store(P3D_KEY, P3D_VALUE)
        renderer.store(P3D_KEY, P3D_VALUE)
        frame_execute.store(P3D_KEY, P3D_VALUE)
        controls.store(P3D_KEY, P3D_VALUE)
        _par(frame_execute, "active", True)
    except Exception:
        callbacks.text = old_callbacks
        frame_execute.text = old_frame_code
        _par(frame_execute, "active", old_frame_active)
        raise

    print("[Phase 3D] Connection transitions installed; TOE was NOT saved.")
    print("[Phase 3D] Existing visual-control values preserved.")
    print("[Phase 3D] New Transitions parameters added:", created_count)
    print("[Phase 3D] Reused frame driver:", frame_execute.path)
    print("[Phase 3D] State manager:", manager.path)
    print("[Phase 3D] MST and edge_data were not modified.")
    return manager


PHASE3D_RESULT = build_phase3d()
