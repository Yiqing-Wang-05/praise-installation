"""Incrementally install Phase 3C mycelium connection visuals into v02.

Run in the TouchDesigner Textport while TD_visual_prototype_v03.toe is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\phase3c_builder.py', encoding='utf-8').read())

The builder replaces only the existing connection renderer callbacks, adds a
small per-frame animation driver, preserves all existing control values, and
never saves the project.
"""

ROOT = "/project1/mutual_illumination"
CONTROLS = ROOT + "/visual_controls"
VISUAL_PARAMS = CONTROLS + "/visual_params"
VISUAL_PARAMS_OUT = CONTROLS + "/visual_params_out"
EDGE_DATA = ROOT + "/graph/edge_data"
GRAPH_EXECUTE = ROOT + "/graph/phase2_graph_execute"
CONNECTION_CALLBACKS = ROOT + "/render_connections/phase2_connection_callbacks"
CONNECTION_RENDERER = ROOT + "/render_connections/phase2_connection_renderer"
FRAME_EXECUTE = ROOT + "/render_connections/phase3c_frame_execute"
NODE_RENDERER = ROOT + "/render_nodes/phase1a_node_renderer"
PHASE1A_OUT = ROOT + "/output/phase1a_out"
COMPOSITE = ROOT + "/output/phase2_composite"
FINAL_OUT = ROOT + "/output/FINAL_OUT"

P2_KEY, P2_VALUE = "mutual_illumination_phase2", "dynamic_mst_v01"
P3A_KEY, P3A_VALUE = "mutual_illumination_phase3a", "visual_controls_v01"
P3B_KEY, P3B_VALUE = "mutual_illumination_phase3b", "node_glow_breathing_v01"
P3C_KEY, P3C_VALUE = "mutual_illumination_phase3c", "mycelium_connections_v01"
EXPECTED_PROJECT = "TD_visual_prototype_v03.toe"
WIDTH, HEIGHT = 1280, 720
EDGE_SCHEMA = ("edge_id", "a_id", "b_id", "ax", "ay", "bx", "by",
               "distance", "trunk")


# kind, page, name, label, default, min, max
NEW_PARAMETERS = (
    ("int", "Mycelium", "Filamentcount", "Filament Count", 3, 2, 4),
    ("float", "Mycelium", "Sheathbrightness", "Sheath Brightness", 0.12, 0.0, 0.6),
    ("float", "Mycelium", "Sheathwidth", "Sheath Width", 7.0, 1.0, 16.0),
    ("float", "Mycelium", "Energyamount", "Energy Amount", 0.18, 0.0, 1.0),
)

ACTIVE_LABELS = {
    "Curveamount": "Curve Amount",
    "Curvemotion": "Curve Motion",
    "Filamentspread": "Filament Spread",
    "Sidebranchamount": "Side Branch Amount",
    "Energyspeed": "Energy Speed",
}


CONNECTION_RENDER_CODE = '''"""Phase 3C local Bezier mycelium connection renderer."""
import math
import numpy

EDGE_DATA = "/project1/mutual_illumination/graph/edge_data"
CONTROLS = "/project1/mutual_illumination/visual_controls"
WIDTH, HEIGHT = 1280, 720
AA = 1.0

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _rgb(control, name):
    return numpy.array((getattr(control.par, name + "r").eval(),
                        getattr(control.par, name + "g").eval(),
                        getattr(control.par, name + "b").eval()),
                       dtype=numpy.float32)

def _visuals():
    control = op(CONTROLS)
    if control is None:
        raise RuntimeError("Missing visual_controls")
    return {
        "line_color": _rgb(control, "Linecolor"),
        "line_weight": max(0.05, float(control.par.Lineweight.eval())),
        "line_brightness": max(0.0, float(control.par.Linebrightness.eval())),
        "branch_brightness": max(0.0, float(control.par.Branchbrightness.eval())),
        "curve_amount": max(0.0, float(control.par.Curveamount.eval())),
        "curve_motion": max(0.0, float(control.par.Curvemotion.eval())),
        "filament_spread": max(0.0, float(control.par.Filamentspread.eval())),
        "filament_count": min(4, max(2, int(control.par.Filamentcount.eval()))),
        "side_branch_amount": min(1.0, max(0.0, float(control.par.Sidebranchamount.eval()))),
        "energy_speed": max(0.0, float(control.par.Energyspeed.eval())),
        "energy_amount": max(0.0, float(control.par.Energyamount.eval())),
        "sheath_brightness": max(0.0, float(control.par.Sheathbrightness.eval())),
        "sheath_width": max(1.0, float(control.par.Sheathwidth.eval())),
        "node_radius": max(0.0, float(control.par.Nodesize.eval())),
        "core_color": _rgb(control, "Corecolor"),
    }

def _edges():
    result, table = [], op(EDGE_DATA)
    if table is None:
        return result
    for row in range(1, table.numRows):
        try:
            a_id, b_id = int(table[row, "a_id"].val), int(table[row, "b_id"].val)
            ax, ay = float(table[row, "ax"].val), float(table[row, "ay"].val)
            bx, by = float(table[row, "bx"].val), float(table[row, "by"].val)
            distance = float(table[row, "distance"].val)
            trunk = bool(int(table[row, "trunk"].val))
            # Always orient an unordered edge from its lower ID to its higher ID.
            # This keeps the normal and bend direction stable across graph cooks.
            if a_id > b_id:
                a_id, b_id, ax, ay, bx, by = b_id, a_id, bx, by, ax, ay
            result.append((a_id, b_id, ax, ay, bx, by, distance, trunk))
        except (TypeError, ValueError, AttributeError):
            pass
    return result

def _bezier_points(edge, now, visual):
    a_id, b_id, ax, ay, bx, by, stored_distance, trunk = edge
    dx, dy = bx - ax, by - ay
    length = max(math.hypot(dx, dy), 1.0)
    nx, ny = -dy / length, dx / length
    pair_phase = a_id * 1.73 + b_id * 2.31
    living_shift = math.sin(pair_phase + now * visual["curve_motion"]) * 0.18 + 0.82
    bend = length * visual["curve_amount"] * math.sin(pair_phase) * living_shift
    if not trunk:
        bend *= 1.35
    return ((ax, ay),
            (ax + dx * 0.31 + nx * bend, ay + dy * 0.31 + ny * bend),
            (ax + dx * 0.69 - nx * bend * 0.48,
             ay + dy * 0.69 - ny * bend * 0.48),
            (bx, by))

def _bezier_position(points, t):
    p0, p1, p2, p3 = points
    u = 1.0 - t
    weights = (u*u*u, 3.0*u*u*t, 3.0*u*t*t, t*t*t)
    return tuple(sum(point[axis] * weight for point, weight in zip(points, weights))
                 for axis in (0, 1))

def _bezier_tangent(points, t):
    p0, p1, p2, p3 = points
    u = 1.0 - t
    dx = (3*u*u*(p1[0]-p0[0]) + 6*u*t*(p2[0]-p1[0]) +
          3*t*t*(p3[0]-p2[0]))
    dy = (3*u*u*(p1[1]-p0[1]) + 6*u*t*(p2[1]-p1[1]) +
          3*t*t*(p3[1]-p2[1]))
    length = max(math.hypot(dx, dy), 1.0)
    return dx / length, dy / length

def _sample_bezier(points, sample_count):
    p0, p1, p2, p3 = points
    t = numpy.linspace(0.0, 1.0, sample_count, dtype=numpy.float32)
    u = 1.0 - t
    x = (u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0])
    y = (u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1])
    return numpy.column_stack((x, y))

def _coverage(distance, radius):
    value = numpy.clip((radius + AA - distance) / (2.0 * AA), 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)

def _filaments(count):
    if count == 2:
        return ((0.0, 1.0, 1.0), (1.0, 0.18, 0.58))
    if count == 4:
        return ((-1.0, 0.20, 0.58), (-0.35, 0.38, 0.72),
                (0.0, 1.0, 1.0), (0.9, 0.16, 0.50))
    return ((-1.0, 0.24, 0.70), (0.0, 1.0, 1.0),
            (1.0, 0.18, 0.58))

def _draw_curve(image, points, color, alpha, visual, fade_radius,
                branch_detail=False):
    chord = math.hypot(points[-1][0]-points[0][0],
                       points[-1][1]-points[0][1])
    sample_count = min(64, max(8, int(chord / 18.0) + 2))
    samples = _sample_bezier(points, sample_count)
    patterns = ((0.0, 0.42, 0.55),) if branch_detail else _filaments(
        visual["filament_count"])
    spread = 0.0 if branch_detail else visual["filament_spread"]
    sheath_radius = (visual["line_weight"] *
                      (3.4 if branch_detail else visual["sheath_width"]) * 0.5)
    max_offset = max(abs(item[0]) for item in patterns) * spread
    max_line_radius = max(item[2] for item in patterns) * visual["line_weight"] * 0.5
    margin = max(sheath_radius, max_offset + max_line_radius) + AA + 2.0
    segment_count = len(samples) - 1

    for index in range(segment_count):
        ax, ay = float(samples[index, 0]), float(samples[index, 1])
        bx, by = float(samples[index+1, 0]), float(samples[index+1, 1])
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
        along = (xx-ax)*tx + (yy-ay)*ty
        along_out = numpy.maximum(-along, 0.0) + numpy.maximum(along-length, 0.0)
        perpendicular = (xx-ax)*nx + (yy-ay)*ny

        local_t = numpy.clip(along/length, 0.0, 1.0)
        global_t = (index + local_t) / float(segment_count)
        fade_t = min(0.22, max(0.015, fade_radius/max(chord, 1.0)))
        endpoint = numpy.clip(numpy.minimum(global_t, 1.0-global_t)/fade_t, 0.0, 1.0)
        endpoint = endpoint*endpoint*(3.0-2.0*endpoint)

        center_distance = numpy.sqrt(along_out*along_out + perpendicular*perpendicular)
        intensity = (_coverage(center_distance, sheath_radius) *
                     visual["sheath_brightness"])
        for offset, strength, weight in patterns:
            distance = numpy.sqrt(along_out*along_out +
                                  (perpendicular-offset*spread)**2)
            radius = max(0.05, visual["line_weight"]*weight*0.5)
            intensity += _coverage(distance, radius) * strength
        intensity *= endpoint * alpha
        patch = image[y0:y1, x0:x1, :]
        numpy.maximum(patch, intensity[:, :, None]*color, out=patch)

def _draw_side_branch(image, edge, points, alpha, visual):
    a_id, b_id = edge[0], edge[1]
    seed = (a_id*31 + b_id*17) % 100
    if seed/100.0 > visual["side_branch_amount"]:
        return
    t = 0.34 + (seed % 25)/100.0
    x, y = _bezier_position(points, t)
    tx, ty = _bezier_tangent(points, t)
    side = -1.0 if seed % 2 else 1.0
    nx, ny = -ty*side, tx*side
    length = 20.0 + seed % 24
    end = (x + tx*length*0.34 + nx*length,
           y + ty*length*0.34 + ny*length)
    c1 = (x + tx*length*0.18 + nx*length*0.18,
          y + ty*length*0.18 + ny*length*0.18)
    c2 = (end[0] - tx*length*0.18, end[1] - ty*length*0.18)
    _draw_curve(image, ((x, y), c1, c2, end), visual["line_color"],
                alpha*0.72, visual, 2.0, branch_detail=True)

def _draw_energy(image, edge, points, alpha, now, visual):
    if visual["energy_amount"] <= 0.0 or visual["energy_speed"] <= 0.0:
        return
    travel = ((now*visual["energy_speed"] + edge[0]*0.137) % 1.18) - 0.09
    if travel < 0.0 or travel > 1.0:
        return
    x, y = _bezier_position(points, travel)
    halo_radius = visual["line_weight"]*2.4 + 2.0
    margin = int(math.ceil(halo_radius + AA + 1.0))
    x0, x1 = max(0, int(x)-margin), min(WIDTH, int(x)+margin+1)
    y0, y1 = max(0, int(y)-margin), min(HEIGHT, int(y)+margin+1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = numpy.ogrid[y0:y1, x0:x1]
    distance = numpy.sqrt((xx-x)**2 + (yy-y)**2)
    amount = alpha*visual["energy_amount"]
    intensity = (_coverage(distance, halo_radius)*amount*0.22 +
                 _coverage(distance, max(0.5, visual["line_weight"]*0.55))*amount*0.72)
    patch = image[y0:y1, x0:x1, :]
    numpy.maximum(patch, intensity[:, :, None]*visual["core_color"], out=patch)

def onCook(scriptOp):
    visual = _visuals()
    image = numpy.zeros((HEIGHT, WIDTH, 3), dtype=numpy.float32)
    now = float(absTime.seconds)
    for edge in _edges():
        a_id, b_id, ax, ay, bx, by, stored_distance, trunk = edge
        distance = math.hypot(bx-ax, by-ay)
        proximity = max(0.0, 1.0-distance/390.0)
        hierarchy = 1.0 if trunk else visual["branch_brightness"]
        alpha = ((105.0/255.0)*visual["line_brightness"]*hierarchy*
                 (0.5+proximity*0.5))
        points = _bezier_points(edge, now, visual)
        _draw_curve(image, points, visual["line_color"], alpha, visual,
                    visual["node_radius"]*1.15)
        if trunk:
            _draw_side_branch(image, edge, points, alpha, visual)
        _draw_energy(image, edge, points, alpha, now, visual)
    numpy.clip(image, 0.0, 1.0, out=image)
    scriptOp.copyNumpyArray(image)

def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''


FRAME_EXECUTE_CODE = '''"""Cook animated Phase 3C connections each playing frame."""
CONTROLS = "/project1/mutual_illumination/visual_controls"
RENDERER = "/project1/mutual_illumination/render_connections/phase2_connection_renderer"

def onFrameStart(frame):
    controls, renderer = op(CONTROLS), op(RENDERER)
    if controls is None or renderer is None:
        return
    curve_moves = (float(controls.par.Curveamount.eval()) > 0.0 and
                   float(controls.par.Curvemotion.eval()) > 0.0)
    energy_moves = (float(controls.par.Energyamount.eval()) > 0.0 and
                    float(controls.par.Energyspeed.eval()) > 0.0)
    if curve_moves or energy_moves:
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
    method = {"float": page.appendFloat, "int": page.appendInt}[kind]
    group = method(name, label=label, replace=False)
    _configure_new(list(group), default, minimum, maximum)
    return True


def _activate_labels(component):
    for name, label in ACTIVE_LABELS.items():
        parameter = getattr(component.par, name, None)
        if parameter is None:
            raise RuntimeError("Missing Phase 3A parameter: " + name)
        parameter.label = label
        if parameter.label != label:
            raise RuntimeError("Failed to update label for " + name)


def _owned(parent, name, kind, initialize=True):
    existing = parent.op(name)
    if existing is not None:
        if existing.fetch(P3C_KEY, None, search=False) != P3C_VALUE:
            raise RuntimeError("Refusing unowned operator: " + existing.path)
        return existing
    created = (parent.create(kind, name) if initialize
               else parent.create(kind, name, initialize=False))
    created.store(P3C_KEY, P3C_VALUE)
    return created


def _validate_v02():
    if project.name != EXPECTED_PROJECT:
        raise RuntimeError(
            "Phase 3C may only run in {}; current project is {}".format(
                EXPECTED_PROJECT, project.name))

    controls = _require(CONTROLS)
    edge_data = _require(EDGE_DATA)
    callbacks = _require(CONNECTION_CALLBACKS)
    renderer = _require(CONNECTION_RENDERER)
    graph_execute = _require(GRAPH_EXECUTE)
    composite = _require(COMPOSITE)

    if controls.fetch(P3A_KEY, None, search=False) != P3A_VALUE:
        raise RuntimeError("visual_controls is not the verified Phase 3A component")
    if controls.fetch(P3B_KEY, None, search=False) != P3B_VALUE:
        raise RuntimeError("Phase 3B must be installed in the open v02 project")
    for operator in (callbacks, renderer, graph_execute, composite):
        if operator.fetch(P2_KEY, None, search=False) != P2_VALUE:
            raise RuntimeError("Phase 2 ownership missing on " + operator.path)
    for operator in (callbacks, renderer):
        if operator.fetch(P3A_KEY, None, search=False) != P3A_VALUE:
            raise RuntimeError("Phase 3A ownership missing on " + operator.path)

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
    return controls, callbacks, renderer


def build_phase3c():
    controls, callbacks, renderer = _validate_v02()
    frame_execute = _owned(renderer.parent(), "phase3c_frame_execute", executeDAT,
                           initialize=False)
    frame_execute.nodeX, frame_execute.nodeY = 460, -100
    frame_execute.color = (0.44, 0.31, 0.10)
    frame_execute.comment = "Phase 3C curve and energy animation driver"
    _par(frame_execute, "active", False)

    created_count = 0
    for spec in NEW_PARAMETERS:
        if _ensure_parameter(controls, spec):
            created_count += 1
    _activate_labels(controls)

    frame_execute.text = FRAME_EXECUTE_CODE
    _par(frame_execute, "framestart", True)
    for name in ("start", "create", "exit", "frameend", "playstatechange",
                 "devicechange"):
        parameter = getattr(frame_execute.par, name, None)
        if parameter is not None:
            parameter.val = False

    callbacks.text = CONNECTION_RENDER_CODE
    callbacks.store(P3C_KEY, P3C_VALUE)
    renderer.store(P3C_KEY, P3C_VALUE)
    controls.store(P3C_KEY, P3C_VALUE)

    params = _require(VISUAL_PARAMS)
    params_out = _require(VISUAL_PARAMS_OUT)
    params.cook(force=True)
    params_out.cook(force=True)
    renderer.cook(force=True)
    final_out = _require(FINAL_OUT)
    final_out.cook(force=True)

    for operator in (renderer, final_out):
        if list(operator.errors()):
            raise RuntimeError("Renderer error on {}: {}".format(
                operator.path, operator.errors()))
    if (int(renderer.width), int(renderer.height)) != (WIDTH, HEIGHT):
        raise RuntimeError("Connection renderer resolution changed during Phase 3C")
    if (int(final_out.width), int(final_out.height)) != (WIDTH, HEIGHT):
        raise RuntimeError("FINAL_OUT resolution changed during Phase 3C")

    _par(frame_execute, "active", True)
    print("[Phase 3C] Mycelium connection visuals installed; TOE was NOT saved.")
    print("[Phase 3C] Existing visual-control values preserved.")
    print("[Phase 3C] New Mycelium parameters added:", created_count)
    print("[Phase 3C] Animation frame driver active:", frame_execute.path)
    print("[Phase 3C] MST topology and edge_data were not modified.")
    return frame_execute


PHASE3C_RESULT = build_phase3c()
