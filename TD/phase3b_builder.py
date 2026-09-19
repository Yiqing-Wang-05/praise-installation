"""Incrementally install Phase 3B node glow and breathing into v02.

Run in the TouchDesigner Textport while TD_visual_prototype_v02.toe is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\phase3b_builder.py', encoding='utf-8').read())

This builder reuses the Phase 1/2/3A network, preserves existing visual-control
values, and never saves the project.
"""

ROOT = "/project1/mutual_illumination"
CONTROLS = ROOT + "/visual_controls"
VISUAL_PARAMS = CONTROLS + "/visual_params"
VISUAL_PARAMS_OUT = CONTROLS + "/visual_params_out"
NODE_CALLBACKS = ROOT + "/render_nodes/phase1a_node_callbacks"
NODE_RENDERER = ROOT + "/render_nodes/phase1a_node_renderer"
FRAME_EXECUTE = ROOT + "/render_nodes/phase3b_frame_execute"
CONNECTION_RENDERER = ROOT + "/render_connections/phase2_connection_renderer"
PHASE1A_OUT = ROOT + "/output/phase1a_out"
COMPOSITE = ROOT + "/output/phase2_composite"
FINAL_OUT = ROOT + "/output/FINAL_OUT"

B1_KEY, B1_VALUE = "mutual_illumination_phase1b", "mouse_drag_v03_diagnostics"
P2_KEY, P2_VALUE = "mutual_illumination_phase2", "dynamic_mst_v01"
P3A_KEY, P3A_VALUE = "mutual_illumination_phase3a", "visual_controls_v01"
P3B_KEY, P3B_VALUE = "mutual_illumination_phase3b", "node_glow_breathing_v01"
EXPECTED_PROJECT = "TD_visual_prototype_v02.toe"
WIDTH, HEIGHT = 1280, 720


# Only missing parameters are created. Existing values, defaults, and ranges
# are deliberately left untouched.
CORE_PARAMETERS = (
    ("rgb", "Corecolor", "Core Color", (1.0, 239 / 255, 205 / 255), 0.0, 1.0),
    ("float", "Coresize", "Core Size", 0.58, 0.1, 1.5),
    ("float", "Corebrightness", "Core Brightness", 1.0, 0.0, 2.0),
)

ACTIVE_LABELS = {
    "Glowamount": "Glow Amount",
    "Glowradius": "Glow Radius",
    "Glowlayers": "Glow Layers",
    "Innerglowsize": "Inner Glow Size",
    "Breathingenabled": "Enable",
    "Breathingspeed": "Speed",
    "Breathingamount": "Size Amount",
    "Breathingbrightness": "Brightness Amount",
    "Breathingglow": "Glow Amount",
}


NODE_RENDER_CODE = '''"""Phase 3B local-patch node glow and breathing renderer."""
import math
import numpy

TABLE = "/project1/mutual_illumination/data/node_data"
DIAG = "/project1/mutual_illumination/data/phase1b_diagnostics"
MANAGER = "/project1/mutual_illumination/data/node_system"
CONTROLS = "/project1/mutual_illumination/visual_controls"
WIDTH, HEIGHT = 1280, 720
TAU = math.pi * 2.0

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _diag(name, value):
    dat = op(DIAG)
    if dat:
        for row in range(1, dat.numRows):
            if dat[row, 0].val == name:
                dat[row, 1] = "" if value is None else str(value)
                break

def _nodes():
    result, table = [], op(TABLE)
    if table:
        for row in range(1, table.numRows):
            try:
                result.append((int(table[row, "id"].val),
                               float(table[row, "x"].val),
                               float(table[row, "y"].val)))
            except (TypeError, ValueError, AttributeError):
                pass
    return result

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
        "radius": max(0.1, float(control.par.Nodesize.eval())),
        "softness": max(0.05, float(control.par.Edgesoftness.eval())),
        "node_color": _rgb(control, "Nodecolor"),
        "core_color": _rgb(control, "Corecolor"),
        "core_size": max(0.01, float(control.par.Coresize.eval())),
        "core_brightness": max(0.0, float(control.par.Corebrightness.eval())),
        "glow_amount": max(0.0, float(control.par.Glowamount.eval())),
        "glow_radius": max(0.0, float(control.par.Glowradius.eval())),
        "glow_layers": max(1, int(control.par.Glowlayers.eval())),
        "inner_glow_size": max(0.0, float(control.par.Innerglowsize.eval())),
        "breathing": bool(control.par.Breathingenabled.eval()),
        "breathing_speed": max(0.0, float(control.par.Breathingspeed.eval())),
        "size_amount": max(0.0, float(control.par.Breathingamount.eval())),
        "brightness_amount": max(0.0, float(control.par.Breathingbrightness.eval())),
        "breathing_glow": max(0.0, float(control.par.Breathingglow.eval())),
    }

def _stable_phase(node_id):
    # Integer hashing makes phase stable for an ID without adding a table column.
    hashed = (int(node_id) * 2654435761) & 0xffffffff
    return (hashed / 4294967296.0) * TAU

def _coverage(distance, radius, softness):
    value = numpy.clip((radius + softness - distance) / (2.0 * softness), 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)

def _add_circle(patch, distance, radius, softness, color, strength):
    if radius <= 0.0 or strength <= 0.0:
        return
    coverage = _coverage(distance, radius, softness).astype(numpy.float32)
    patch += coverage[:, :, None] * color * float(strength)

def _add_outer_halo(patch, distance, radius, halo_extent, layers,
                    color, glow_amount, brightness):
    if halo_extent <= 0.0 or glow_amount <= 0.0:
        return
    # Closed-form accumulation of the Python prototype's concentric layers.
    # q=0 is the node boundary and q=1 is the halo's outer edge.
    q = numpy.clip((distance - radius) / halo_extent, 0.0, 1.0)
    profile = (float(layers) / 3.0) * ((1.12 - q) ** 3.0 - 0.12 ** 3.0)
    strength = (6.0 / 255.0) * glow_amount * brightness
    patch += profile[:, :, None] * color * strength

_STAMP_CACHE = {}
_STAMP_SIGNATURE = None
_BREATHING_BINS = 32

def _cache_signature(visual):
    return (visual["radius"], visual["softness"],
            tuple(float(value) for value in visual["node_color"]),
            tuple(float(value) for value in visual["core_color"]),
            visual["core_size"], visual["core_brightness"],
            visual["glow_amount"], visual["glow_radius"],
            visual["glow_layers"], visual["inner_glow_size"],
            visual["size_amount"], visual["brightness_amount"],
            visual["breathing_glow"])

def _node_state(node_id, now, visual):
    if not visual["breathing"]:
        return -1, 1.0, 1.0, 1.0
    wave = math.sin(now * visual["breathing_speed"] * TAU + _stable_phase(node_id))
    pulse = wave * 0.5 + 0.5
    bin_index = int(round(pulse * (_BREATHING_BINS - 1)))
    pulse = bin_index / float(_BREATHING_BINS - 1)
    wave = pulse * 2.0 - 1.0
    size_scale = 1.0 + wave * visual["size_amount"]
    brightness = 1.0 - visual["brightness_amount"] + pulse * visual["brightness_amount"]
    glow_breath = 1.0 - visual["breathing_glow"] + pulse * visual["breathing_glow"]
    return bin_index, size_scale, brightness, glow_breath

def _draw_node_pixels(image, x, y, visual, size_scale, brightness, glow_breath):
    radius = max(0.1, visual["radius"] * max(0.05, size_scale))
    halo_extent = (radius * visual["glow_radius"] *
                   visual["glow_amount"] * max(0.0, glow_breath))
    outer_radius = radius + halo_extent
    inner_radius = radius * (1.0 + visual["inner_glow_size"])
    extent = max(radius * 1.2, outer_radius, inner_radius)
    margin = int(math.ceil(extent + visual["softness"] * 2.0 + 2.0))

    image_height, image_width = image.shape[:2]
    x0 = max(0, int(math.floor(x)) - margin)
    x1 = min(image_width, int(math.floor(x)) + margin + 1)
    y0 = max(0, int(math.floor(y)) - margin)
    y1 = min(image_height, int(math.floor(y)) + margin + 1)
    if x0 >= x1 or y0 >= y1:
        return

    yy, xx = numpy.ogrid[y0:y1, x0:x1]
    distance = numpy.sqrt((xx - x) ** 2 + (yy - y) ** 2).astype(numpy.float32)
    patch = image[y0:y1, x0:x1, :3]

    # The two cumulative profiles reproduce the brightness distribution of the
    # prototype's outer and inner layer stacks without full-frame blur passes.
    _add_outer_halo(patch, distance, radius, halo_extent,
                    visual["glow_layers"], visual["node_color"],
                    visual["glow_amount"], brightness)

    # Restrict denser light to its much smaller local crop. This avoids doing
    # core work across the full halo rectangle for every node and frame.
    inner_extent = radius * visual["inner_glow_size"]
    inner_bound = max(radius * 1.2, radius + inner_extent)
    inner_margin = int(math.ceil(inner_bound + visual["softness"] * 2.0 + 2.0))
    ix0 = max(x0, int(math.floor(x)) - inner_margin)
    ix1 = min(x1, int(math.floor(x)) + inner_margin + 1)
    iy0 = max(y0, int(math.floor(y)) - inner_margin)
    iy1 = min(y1, int(math.floor(y)) + inner_margin + 1)
    inner_distance = distance[iy0-y0:iy1-y0, ix0-x0:ix1-x0]
    inner_patch = image[iy0:iy1, ix0:ix1, :3]
    node_energy = numpy.zeros(inner_distance.shape, dtype=numpy.float32)
    if inner_extent > 0.0:
        q = numpy.clip((inner_distance - radius) / inner_extent, 0.0, 1.0)
        profile = 6.0 * (1.2 * (1.0 - q) - 0.5 * (1.0 - q * q))
        node_energy += profile * ((21.0 / 255.0) * brightness)
    node_energy += (_coverage(inner_distance, radius * 1.2,
                              visual["softness"]).astype(numpy.float32) *
                    ((205.0 / 255.0) * brightness))
    inner_patch += node_energy[:, :, None] * visual["node_color"]

    core_radius = radius * visual["core_size"]
    core_margin = int(math.ceil(core_radius + visual["softness"] * 2.0 + 2.0))
    cx0 = max(x0, int(math.floor(x)) - core_margin)
    cx1 = min(x1, int(math.floor(x)) + core_margin + 1)
    cy0 = max(y0, int(math.floor(y)) - core_margin)
    cy1 = min(y1, int(math.floor(y)) + core_margin + 1)
    core_distance = distance[cy0-y0:cy1-y0, cx0-x0:cx1-x0]
    core_patch = image[cy0:cy1, cx0:cx1, :3]
    _add_circle(core_patch, core_distance, core_radius, visual["softness"] * 0.72,
                visual["core_color"], visual["core_brightness"] * brightness)
    warm_white = numpy.array((1.0, 250.0 / 255.0, 233.0 / 255.0),
                             dtype=numpy.float32)
    _add_circle(core_patch, core_distance, core_radius * (0.22 / 0.58),
                visual["softness"] * 0.55, warm_white,
                (245.0 / 255.0) * brightness)
    numpy.clip(patch, 0.0, 1.0, out=patch)

def _make_stamp(visual, size_scale, brightness, glow_breath):
    radius = max(0.1, visual["radius"] * max(0.05, size_scale))
    halo_extent = (radius * visual["glow_radius"] *
                   visual["glow_amount"] * max(0.0, glow_breath))
    extent = max(radius * 1.2, radius + halo_extent,
                 radius * (1.0 + visual["inner_glow_size"]))
    margin = int(math.ceil(extent + visual["softness"] * 2.0 + 2.0))
    stamp = numpy.zeros((margin * 2 + 1, margin * 2 + 1, 3),
                        dtype=numpy.float32)
    _draw_node_pixels(stamp, margin, margin, visual,
                      size_scale, brightness, glow_breath)
    return stamp

def _draw_node(image, node_id, x, y, now, visual):
    global _STAMP_SIGNATURE
    signature = _cache_signature(visual)
    if signature != _STAMP_SIGNATURE:
        _STAMP_CACHE.clear()
        _STAMP_SIGNATURE = signature
    key, size_scale, brightness, glow_breath = _node_state(
        node_id, now, visual)
    stamp = _STAMP_CACHE.get(key)
    if stamp is None:
        stamp = _make_stamp(visual, size_scale, brightness, glow_breath)
        _STAMP_CACHE[key] = stamp

    center_x, center_y = int(round(x)), int(round(y))
    half_w, half_h = stamp.shape[1] // 2, stamp.shape[0] // 2
    x0, x1 = max(0, center_x-half_w), min(WIDTH, center_x+half_w+1)
    y0, y1 = max(0, center_y-half_h), min(HEIGHT, center_y+half_h+1)
    if x0 >= x1 or y0 >= y1:
        return
    sx0, sy0 = x0-(center_x-half_w), y0-(center_y-half_h)
    sx1, sy1 = sx0+(x1-x0), sy0+(y1-y0)
    patch = image[y0:y1, x0:x1, :3]
    patch += stamp[sy0:sy1, sx0:sx1, :]

def onCook(scriptOp):
    visual = _visuals()
    image = numpy.zeros((HEIGHT, WIDTH, 3), dtype=numpy.float32)
    nodes = _nodes()
    now = float(absTime.seconds)
    for node_id, x, y in nodes:
        _draw_node(image, node_id, x, y, now, visual)
    numpy.clip(image, 0.0, 1.0, out=image)
    scriptOp.copyNumpyArray(image)
    _diag("last_render_frame", absTime.frame)
    manager = op(MANAGER)
    drag_id = None if manager is None else manager.fetch(
        "phase1b_dragging_id", None, search=False)
    rendered = next((node for node in nodes if node[0] == drag_id), None)
    _diag("last_render_node_id", None if rendered is None else rendered[0])
    _diag("last_render_node_x", None if rendered is None else rendered[1])
    _diag("last_render_node_y", None if rendered is None else rendered[2])

def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''


FRAME_EXECUTE_CODE = '''"""Cook animated nodes once per playing timeline frame."""
CONTROLS = "/project1/mutual_illumination/visual_controls"
RENDERER = "/project1/mutual_illumination/render_nodes/phase1a_node_renderer"

def onFrameStart(frame):
    controls, renderer = op(CONTROLS), op(RENDERER)
    if controls is not None and renderer is not None:
        if bool(controls.par.Breathingenabled.eval()):
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


def _ensure_core_parameter(component, spec):
    kind, name, label, default, minimum, maximum = spec
    page = _page(component, "Node")
    if kind == "rgb":
        parts = [getattr(component.par, name + suffix, None)
                 for suffix in ("r", "g", "b")]
        if all(part is not None for part in parts):
            return False
        if any(part is not None for part in parts):
            raise RuntimeError("Incomplete existing RGB parameter: " + name)
        group = page.appendRGB(name, label=label, replace=False)
    else:
        existing = getattr(component.par, name, None)
        if existing is not None:
            return False
        group = page.appendFloat(name, label=label, replace=False)
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
        if existing.fetch(P3B_KEY, None, search=False) != P3B_VALUE:
            raise RuntimeError("Refusing unowned operator: " + existing.path)
        return existing
    created = (parent.create(kind, name) if initialize
               else parent.create(kind, name, initialize=False))
    created.store(P3B_KEY, P3B_VALUE)
    return created


def _validate_v02():
    if project.name != EXPECTED_PROJECT:
        raise RuntimeError(
            "Phase 3B may only run in {}; current project is {}".format(
                EXPECTED_PROJECT, project.name))

    controls = _require(CONTROLS)
    callbacks = _require(NODE_CALLBACKS)
    renderer = _require(NODE_RENDERER)
    connection_renderer = _require(CONNECTION_RENDERER)
    composite = _require(COMPOSITE)

    if controls.fetch(P3A_KEY, None, search=False) != P3A_VALUE:
        raise RuntimeError("visual_controls is not the verified Phase 3A component")
    for operator in (callbacks, renderer):
        if operator.fetch(B1_KEY, None, search=False) != B1_VALUE:
            raise RuntimeError("Phase 1B ownership missing on " + operator.path)
        if operator.fetch(P3A_KEY, None, search=False) != P3A_VALUE:
            raise RuntimeError("Phase 3A ownership missing on " + operator.path)
    if connection_renderer.fetch(P2_KEY, None, search=False) != P2_VALUE:
        raise RuntimeError("Phase 2 connection renderer ownership is missing")
    if composite.fetch(P2_KEY, None, search=False) != P2_VALUE:
        raise RuntimeError("Phase 2 Composite ownership is missing")
    if list(composite.inputs) != [_require(PHASE1A_OUT)]:
        raise RuntimeError("Protected Composite wire is not phase1a_out")
    if _path_from_par(composite.par.top) != connection_renderer.path:
        raise RuntimeError("Protected Composite TOP parameter is incorrect")
    if str(composite.par.operand.eval()).lower() != "add":
        raise RuntimeError("Protected Composite operation is not Add")
    composite.cook(force=True)
    if (int(composite.width), int(composite.height)) != (WIDTH, HEIGHT):
        raise RuntimeError("Protected Composite is not 1280x720")
    if list(composite.errors()):
        raise RuntimeError("Protected Composite has errors: " + repr(composite.errors()))
    return controls, callbacks, renderer


def build_phase3b():
    controls, callbacks, renderer = _validate_v02()
    render_parent = renderer.parent()
    frame_execute = _owned(render_parent, "phase3b_frame_execute", executeDAT,
                           initialize=False)
    frame_execute.nodeX, frame_execute.nodeY = 460, 40
    frame_execute.color = (0.52, 0.28, 0.10)
    frame_execute.comment = "Phase 3B per-frame breathing driver"

    # Disable animation during installation, then preserve all existing control
    # values while adding only missing core controls.
    _par(frame_execute, "active", False)
    created_count = 0
    for spec in CORE_PARAMETERS:
        if _ensure_core_parameter(controls, spec):
            created_count += 1
    _activate_labels(controls)

    frame_execute.text = FRAME_EXECUTE_CODE
    _par(frame_execute, "framestart", True)
    for name in ("start", "create", "exit", "frameend", "playstatechange",
                 "devicechange"):
        parameter = getattr(frame_execute.par, name, None)
        if parameter is not None:
            parameter.val = False

    callbacks.text = NODE_RENDER_CODE
    callbacks.store(P3B_KEY, P3B_VALUE)
    renderer.store(P3B_KEY, P3B_VALUE)
    controls.store(P3B_KEY, P3B_VALUE)

    # Make the Phase 3A parameter stream discover newly added core controls.
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
        raise RuntimeError("Node renderer resolution changed during Phase 3B")
    if (int(final_out.width), int(final_out.height)) != (WIDTH, HEIGHT):
        raise RuntimeError("FINAL_OUT resolution changed during Phase 3B")

    _par(frame_execute, "active", True)
    print("[Phase 3B] Node glow and breathing installed; TOE was NOT saved.")
    print("[Phase 3B] Existing visual-control values preserved.")
    print("[Phase 3B] New core parameters added:", created_count)
    print("[Phase 3B] Breathing frame driver active:", frame_execute.path)
    print("[Phase 3B] Timeline must be playing for breathing animation.")
    return frame_execute


PHASE3B_RESULT = build_phase3b()
