"""Incrementally install Phase 3E Ripple and Ambient effects into v05.

Run in the TouchDesigner Textport while TD_visual_prototype_v05.toe is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\phase3e_builder.py', encoding='utf-8').read())

The builder preserves all earlier visual systems and control values, uses one
procedural effects TOP, supports safe reruns, and never saves the project.
"""

ROOT = "/project1/mutual_illumination"
CONTROLS = ROOT + "/visual_controls"
VISUAL_PARAMS = CONTROLS + "/visual_params"
VISUAL_PARAMS_OUT = CONTROLS + "/visual_params_out"
VISUAL_EXECUTE = CONTROLS + "/visual_config_execute"
NODE_DATA = ROOT + "/data/node_data"
NODE_SYSTEM = ROOT + "/data/node_system"
RESET_SYSTEM = ROOT + "/input/reset_all_system"
RENDER_EFFECTS = ROOT + "/render_effects"
EFFECTS_MANAGER = RENDER_EFFECTS + "/phase3e_effects_manager"
EFFECTS_CALLBACKS = RENDER_EFFECTS + "/phase3e_effects_callbacks"
EFFECTS_RENDERER = RENDER_EFFECTS + "/phase3e_effects_renderer"
EFFECTS_EXECUTE = RENDER_EFFECTS + "/phase3e_frame_execute"
OUTPUT = ROOT + "/output"
PHASE1A_OUT = OUTPUT + "/phase1a_out"
PHASE2_COMPOSITE = OUTPUT + "/phase2_composite"
PHASE2_OUT = OUTPUT + "/phase2_out"
EFFECTS_SELECT = OUTPUT + "/phase3e_effects_select"
PHASE3E_COMPOSITE = OUTPUT + "/phase3e_composite"
PHASE3E_OUT = OUTPUT + "/phase3e_out"
FINAL_OUT = OUTPUT + "/FINAL_OUT"
CONNECTION_RENDERER = ROOT + "/render_connections/phase2_connection_renderer"

B1_KEY, B1_VALUE = "mutual_illumination_phase1b", "mouse_drag_v03_diagnostics"
P2_KEY, P2_VALUE = "mutual_illumination_phase2", "dynamic_mst_v01"
P3A_KEY, P3A_VALUE = "mutual_illumination_phase3a", "visual_controls_v01"
P3D_KEY, P3D_VALUE = "mutual_illumination_phase3d", "connection_transitions_v01"
RESET_KEY, RESET_VALUE = "mutual_illumination_reset_all", "unified_reset_v01"
P3E_KEY, P3E_VALUE = "mutual_illumination_phase3e", "ripple_ambient_v01"
EXPECTED_PROJECT = "TD_visual_prototype_v05.toe"
WIDTH, HEIGHT = 1280, 720

NODE_OVERRIDE_MARKER = "\n# === Phase 3E ripple trigger override ===\n"
RESET_EXTENSION_MARKER = "\n# === Phase 3E persistent reset hook ===\n"
REFRESH_EXTENSION_MARKER = "\n# === Phase 3E visual refresh extension ===\n"


AMBIENT_COLOR_PARAMETER = (
    "rgb", "Ambient", "Ambientcolor", "Ambient Color",
    (1.0, 206 / 255, 137 / 255), 0.0, 1.0,
)

ACTIVE_LABELS = {
    "Rippleenabled": "Enable",
    "Ripplecolor": "Ripple Color",
    "Ripplestrength": "Strength",
    "Rippleduration": "Duration",
    "Ripplemaxradius": "Max Radius",
    "Ambientenabled": "Enable",
    "Ambientglow": "Glow Amount",
    "Ambientradius": "Radius",
}


EFFECTS_MANAGER_CODE = '''"""Transient Ripple event state for Phase 3E."""
CONTROLS = "/project1/mutual_illumination/visual_controls"
RENDERER = "/project1/mutual_illumination/render_effects/phase3e_effects_renderer"
_MAX_RIPPLES = 64
_MAX_TRIGGER_IDS = 4096
_ripples = []
_triggered_ids = set()
_triggered_order = []

def _enabled():
    controls = op(CONTROLS)
    return controls is not None and bool(controls.par.Rippleenabled.eval())

def trigger(node_id, x, y, now=None):
    node_id = int(node_id)
    if node_id in _triggered_ids:
        return False
    _triggered_ids.add(node_id)
    _triggered_order.append(node_id)
    if len(_triggered_order) > _MAX_TRIGGER_IDS:
        _triggered_ids.discard(_triggered_order.pop(0))
    if not _enabled():
        return False
    born = float(absTime.seconds if now is None else now)
    _ripples.append((node_id, float(x), float(y), born))
    if len(_ripples) > _MAX_RIPPLES:
        del _ripples[:-_MAX_RIPPLES]
    renderer = op(RENDERER)
    if renderer is not None:
        renderer.cook(force=True)
    return True

def events(now, duration, enabled=True):
    if not enabled:
        _ripples.clear()
        return []
    now, duration = float(now), max(0.001, float(duration))
    alive, result = [], []
    for node_id, x, y, born in _ripples:
        age = max(0.0, now-born)
        if age < duration:
            alive.append((node_id, x, y, born))
            result.append((node_id, x, y, min(1.0, age/duration)))
    _ripples[:] = alive
    return result

def has_active():
    return bool(_ripples)

def state_count():
    return len(_ripples)

def clear():
    _ripples.clear()
    _triggered_ids.clear()
    _triggered_order.clear()
'''


EFFECTS_RENDER_CODE = '''"""Render Phase 3E Ambient and Ripple layers in one Script TOP."""
import math
import numpy

NODE_DATA = "/project1/mutual_illumination/data/node_data"
CONTROLS = "/project1/mutual_illumination/visual_controls"
MANAGER = "/project1/mutual_illumination/render_effects/phase3e_effects_manager"
WIDTH, HEIGHT = 1280, 720
TAU = math.pi*2.0
AA = 1.0

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _rgb(control, name):
    return numpy.array((getattr(control.par, name+"r").eval(),
                        getattr(control.par, name+"g").eval(),
                        getattr(control.par, name+"b").eval()),
                       dtype=numpy.float32)

def _visuals():
    control = op(CONTROLS)
    if control is None:
        raise RuntimeError("Missing visual_controls")
    return {
        "ripple_enabled": bool(control.par.Rippleenabled.eval()),
        "ripple_color": _rgb(control, "Ripplecolor"),
        "ripple_strength": max(0.0, float(control.par.Ripplestrength.eval())),
        "ripple_duration": max(0.001, float(control.par.Rippleduration.eval())),
        "ripple_radius": max(0.0, float(control.par.Ripplemaxradius.eval())),
        "ambient_enabled": bool(control.par.Ambientenabled.eval()),
        "ambient_color": _rgb(control, "Ambientcolor"),
        "ambient_glow": max(0.0, float(control.par.Ambientglow.eval())),
        "ambient_radius": max(0.0, float(control.par.Ambientradius.eval())),
        "breathing_speed": max(0.0, float(control.par.Breathingspeed.eval())),
    }

def _nodes():
    result, table = [], op(NODE_DATA)
    if table is None:
        return result
    for row in range(1, table.numRows):
        try:
            result.append((int(table[row, "id"].val),
                           float(table[row, "x"].val),
                           float(table[row, "y"].val)))
        except (TypeError, ValueError, AttributeError):
            pass
    return result

def _stable_phase(node_id):
    hashed = (int(node_id)*2654435761) & 0xffffffff
    return (hashed/4294967296.0)*TAU

def _coverage(distance, radius):
    value = numpy.clip((radius+AA-distance)/(2.0*AA), 0.0, 1.0)
    return value*value*(3.0-2.0*value)

def _draw_ambient(image, nodes, now, visual):
    if not visual["ambient_enabled"] or not nodes:
        return
    center_x = sum(node[1] for node in nodes)/len(nodes)
    center_y = sum(node[2] for node in nodes)/len(nodes)
    activity = sum(math.sin(now*visual["breathing_speed"]*TAU+
                            _stable_phase(node[0]))*0.5+0.5
                   for node in nodes)/len(nodes)
    diameter = min(WIDTH, HEIGHT)*visual["ambient_radius"]*(0.9+activity*0.18)
    radius = max(0.0, diameter*0.5)
    if radius <= 0.0 or visual["ambient_glow"] <= 0.0:
        return
    margin = int(math.ceil(radius+2.0))
    x0, x1 = max(0, int(center_x)-margin), min(WIDTH, int(center_x)+margin+1)
    y0, y1 = max(0, int(center_y)-margin), min(HEIGHT, int(center_y)+margin+1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = numpy.ogrid[y0:y1, x0:x1]
    distance = numpy.sqrt((xx-center_x)**2+(yy-center_y)**2).astype(numpy.float32)
    q = numpy.clip(distance/radius, 0.0, 1.0)
    # Closed-form approximation of the prototype's eight additive circles.
    profile = (8.0/3.0)*((1.15-q)**3-0.15**3)
    profile[distance >= radius] = 0.0
    intensity = profile*(visual["ambient_glow"]/255.0)
    image[y0:y1, x0:x1, :] += intensity[:, :, None]*visual["ambient_color"]

def _draw_ripple(image, x, y, progress, visual):
    eased = 1.0-(1.0-progress)**3.0
    radius = 6.0+visual["ripple_radius"]*eased
    alpha = ((68.0/255.0)*(1.0-progress)**2.0*
             visual["ripple_strength"])
    if alpha <= 0.0:
        return
    halo_width = 3.2
    margin = int(math.ceil(radius+halo_width*3.0+2.0))
    x0, x1 = max(0, int(x)-margin), min(WIDTH, int(x)+margin+1)
    y0, y1 = max(0, int(y)-margin), min(HEIGHT, int(y)+margin+1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = numpy.ogrid[y0:y1, x0:x1]
    distance = numpy.sqrt((xx-x)**2+(yy-y)**2).astype(numpy.float32)
    ring_distance = numpy.abs(distance-radius)
    core = _coverage(ring_distance, 0.625)
    haze = numpy.exp(-0.5*(ring_distance/halo_width)**2).astype(numpy.float32)*0.18
    intensity = (core+haze)*alpha
    image[y0:y1, x0:x1, :] += intensity[:, :, None]*visual["ripple_color"]

def onCook(scriptOp):
    visual = _visuals()
    image = numpy.zeros((HEIGHT, WIDTH, 3), dtype=numpy.float32)
    now = float(absTime.seconds)
    _draw_ambient(image, _nodes(), now, visual)
    manager = op(MANAGER)
    if manager is None:
        raise RuntimeError("Missing Phase 3E effects manager")
    for node_id, x, y, progress in manager.module.events(
            now, visual["ripple_duration"], visual["ripple_enabled"]):
        _draw_ripple(image, x, y, progress, visual)
    numpy.clip(image, 0.0, 1.0, out=image)
    scriptOp.copyNumpyArray(image)

def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''


EFFECTS_EXECUTE_CODE = '''"""Cook Phase 3E effects only while animation is needed."""
CONTROLS = "/project1/mutual_illumination/visual_controls"
NODE_DATA = "/project1/mutual_illumination/data/node_data"
MANAGER = "/project1/mutual_illumination/render_effects/phase3e_effects_manager"
RENDERER = "/project1/mutual_illumination/render_effects/phase3e_effects_renderer"

def onFrameStart(frame):
    controls, nodes, manager, renderer = (op(CONTROLS), op(NODE_DATA),
                                          op(MANAGER), op(RENDERER))
    if any(item is None for item in (controls, nodes, manager, renderer)):
        return
    ambient_moves = bool(controls.par.Ambientenabled.eval()) and nodes.numRows > 1
    if ambient_moves or manager.module.has_active():
        renderer.cook(force=True)

def onStart(): return
def onCreate(): return
def onExit(): return
def onFrameEnd(frame): return
def onPlayStateChange(state): return
def onDeviceChange(): return
'''


NODE_OVERRIDE_CODE = '''# Trigger only after the canonical node API succeeds.
_phase3e_original_add_node = add_node

def add_node(u, v):
    node_id = _phase3e_original_add_node(u, v)
    if node_id is None:
        return None
    table = _table()
    row = _row(table, node_id)
    if row is not None:
        manager = op("/project1/mutual_illumination/render_effects/phase3e_effects_manager")
        if manager is not None:
            manager.module.trigger(node_id, float(table[row, "x"].val),
                                   float(table[row, "y"].val),
                                   float(absTime.seconds))
    return node_id
'''


RESET_EXTENSION_CODE = '''# Registered at module load, including after reopening the TOE.
def _phase3e_reset_effects():
    manager = op("/project1/mutual_illumination/render_effects/phase3e_effects_manager")
    renderer = op("/project1/mutual_illumination/render_effects/phase3e_effects_renderer")
    if manager is not None:
        manager.module.clear()
    if renderer is not None:
        renderer.cook(force=True)

register_reset_hook("phase3e_effects", _phase3e_reset_effects)
'''


REFRESH_EXTENSION_CODE = '''# Extend the existing visual-control refresh path.
_phase3e_base_refresh = _refresh

def _refresh():
    _phase3e_base_refresh()
    for path in (
            "/project1/mutual_illumination/render_effects/phase3e_effects_renderer",
            "/project1/mutual_illumination/output/phase3e_composite",
            "/project1/mutual_illumination/output/FINAL_OUT"):
        operator = op(path)
        if operator is not None:
            operator.cook(force=True)
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


def _menu(operator, name, wanted):
    parameter = getattr(operator.par, name, None)
    if parameter is None:
        raise RuntimeError("Missing menu {} on {}".format(name, operator.path))
    wanted = wanted.lower()
    for menu_name, label in zip(parameter.menuNames, parameter.menuLabels):
        if wanted in (menu_name+" "+label).lower():
            parameter.val = menu_name
            return
    raise RuntimeError("Menu choice {} unavailable on {}".format(wanted, operator.path))


def _path_from_par(parameter):
    value = parameter.eval()
    return value.path if hasattr(value, "path") else str(value)


def _connect(target, source):
    if list(target.inputs) == [source]:
        return
    target.inputConnectors[0].connect(source)
    if list(target.inputs) != [source]:
        raise RuntimeError("Failed to connect {} -> {}".format(source.path, target.path))


def _owned(parent, name, kind, initialize=True):
    existing = parent.op(name)
    if existing is not None:
        if existing.fetch(P3E_KEY, None, search=False) != P3E_VALUE:
            raise RuntimeError("Refusing unowned operator: " + existing.path)
        return existing
    created = (parent.create(kind, name) if initialize
               else parent.create(kind, name, initialize=False))
    created.store(P3E_KEY, P3E_VALUE)
    return created


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
    if kind != "rgb":
        raise RuntimeError("Unsupported Phase 3E parameter kind: " + kind)
    parts = [getattr(component.par, name+suffix, None) for suffix in ("r", "g", "b")]
    if all(part is not None for part in parts):
        return False
    if any(part is not None for part in parts):
        raise RuntimeError("Incomplete existing RGB parameter: " + name)
    group = _page(component, page_name).appendRGB(name, label=label, replace=False)
    _configure_new(list(group), default, minimum, maximum)
    return True


def _activate_labels(component):
    for name, label in ACTIVE_LABELS.items():
        parameter = getattr(component.par, name, None)
        # TouchDesigner exposes RGB custom parameters as component names
        # (for example Ripplecolorr/g/b), rather than as the ParGroup name.
        if parameter is None:
            parameter = getattr(component.par, name + "r", None)
        if parameter is None:
            raise RuntimeError("Missing Phase 3A parameter: " + name)
        parameter.label = label
        if parameter.label != label:
            raise RuntimeError("Failed to update label for " + name)


def _base_text(text, marker):
    return text.split(marker, 1)[0]


def _marker(operator, key, value, label):
    if operator.fetch(key, None, search=False) != value:
        raise RuntimeError(label + " ownership is missing on " + operator.path)


def _validate_v05():
    if project.name != EXPECTED_PROJECT:
        raise RuntimeError(
            "Phase 3E may only run in {}; current project is {}".format(
                EXPECTED_PROJECT, project.name))
    controls = _require(CONTROLS)
    node_system = _require(NODE_SYSTEM)
    reset_system = _require(RESET_SYSTEM)
    visual_execute = _require(VISUAL_EXECUTE)
    phase2_composite = _require(PHASE2_COMPOSITE)
    phase2_out = _require(PHASE2_OUT)
    final_out = _require(FINAL_OUT)
    connection_renderer = _require(CONNECTION_RENDERER)

    _marker(controls, P3A_KEY, P3A_VALUE, "Phase 3A controls")
    _marker(node_system, B1_KEY, B1_VALUE, "Phase 1B node system")
    _marker(visual_execute, P3A_KEY, P3A_VALUE, "Phase 3A control execute")
    _marker(phase2_composite, P2_KEY, P2_VALUE, "Phase 2 Composite")
    _marker(phase2_out, P2_KEY, P2_VALUE, "Phase 2 output")
    _marker(connection_renderer, P3D_KEY, P3D_VALUE, "Phase 3D renderer")
    _marker(reset_system, RESET_KEY, RESET_VALUE, "Unified Reset All")

    if list(phase2_composite.inputs) != [_require(PHASE1A_OUT)]:
        raise RuntimeError("Protected Phase 2 Composite wire changed")
    if _path_from_par(phase2_composite.par.top) != connection_renderer.path:
        raise RuntimeError("Protected Phase 2 Composite TOP parameter changed")
    if str(phase2_composite.par.operand.eval()).lower() != "add":
        raise RuntimeError("Protected Phase 2 Composite is not Add")
    if (int(phase2_out.width), int(phase2_out.height)) != (WIDTH, HEIGHT):
        raise RuntimeError("phase2_out is not 1280x720")
    current_inputs = list(final_out.inputs)
    existing_phase3e = op(PHASE3E_OUT)
    allowed = [[phase2_out]]
    if existing_phase3e is not None:
        allowed.append([existing_phase3e])
    if current_inputs not in allowed:
        raise RuntimeError("Unexpected FINAL_OUT input: " + repr(current_inputs))
    return controls, node_system, reset_system, visual_execute


def build_phase3e():
    controls, node_system, reset_system, visual_execute = _validate_v05()
    root, output = _require(ROOT), _require(OUTPUT)
    render_effects = _owned(root, "render_effects", baseCOMP)
    manager = _owned(render_effects, "phase3e_effects_manager", textDAT)
    callbacks = _owned(render_effects, "phase3e_effects_callbacks", textDAT)
    renderer = _owned(render_effects, "phase3e_effects_renderer", scriptTOP,
                      initialize=False)
    frame_execute = _owned(render_effects, "phase3e_frame_execute", executeDAT,
                           initialize=False)
    effects_select = _owned(output, "phase3e_effects_select", selectTOP)
    composite = _owned(output, "phase3e_composite", compositeTOP)
    phase_out = _owned(output, "phase3e_out", nullTOP)

    render_effects.nodeX, render_effects.nodeY = 1320, 100
    render_effects.color = (0.35, 0.22, 0.12)
    render_effects.comment = "Phase 3E procedural Ripple and Ambient layer"
    manager.nodeX, manager.nodeY = 0, 80
    callbacks.nodeX, callbacks.nodeY = 210, 80
    renderer.nodeX, renderer.nodeY = 430, 80
    frame_execute.nodeX, frame_execute.nodeY = 650, 80
    effects_select.nodeX, effects_select.nodeY = 790, -20
    composite.nodeX, composite.nodeY = 980, -80
    phase_out.nodeX, phase_out.nodeY = 1170, -80

    old_node_code = node_system.text
    old_reset_code = reset_system.text
    old_refresh_code = visual_execute.text
    old_refresh_active = bool(visual_execute.par.active.eval())
    old_final_inputs = list(_require(FINAL_OUT).inputs)
    _par(frame_execute, "active", False)
    _par(visual_execute, "active", False)
    try:
        created_color = _ensure_parameter(controls, AMBIENT_COLOR_PARAMETER)
        _activate_labels(controls)

        manager.text = EFFECTS_MANAGER_CODE
        callbacks.text = EFFECTS_RENDER_CODE
        frame_execute.text = EFFECTS_EXECUTE_CODE
        _par(frame_execute, "framestart", True)
        for name in ("start", "create", "exit", "frameend", "playstatechange",
                     "devicechange"):
            parameter = getattr(frame_execute.par, name, None)
            if parameter is not None:
                parameter.val = False

        node_system.text = (_base_text(node_system.text, NODE_OVERRIDE_MARKER)+
                            NODE_OVERRIDE_MARKER+NODE_OVERRIDE_CODE)
        reset_system.text = (_base_text(reset_system.text, RESET_EXTENSION_MARKER)+
                             RESET_EXTENSION_MARKER+RESET_EXTENSION_CODE)
        visual_execute.text = (_base_text(visual_execute.text, REFRESH_EXTENSION_MARKER)+
                               REFRESH_EXTENSION_MARKER+REFRESH_EXTENSION_CODE)

        _par(renderer, "callbacks", callbacks.path)
        _menu(renderer, "outputresolution", "custom")
        _par(renderer, "resolutionw", WIDTH)
        _par(renderer, "resolutionh", HEIGHT)
        _par(effects_select, "top", renderer.path)
        _menu(composite, "operand", "add")
        _par(composite, "top", effects_select.path)
        _menu(composite, "outputresolution", "custom")
        _par(composite, "resolutionw", WIDTH)
        _par(composite, "resolutionh", HEIGHT)
        _menu(composite, "outputaspect", "resolution")
        _connect(composite, _require(PHASE2_OUT))
        _connect(phase_out, composite)
        _connect(_require(FINAL_OUT), phase_out)

        params, params_out = _require(VISUAL_PARAMS), _require(VISUAL_PARAMS_OUT)
        params.cook(force=True)
        params_out.cook(force=True)
        manager.cook(force=True)
        node_system.cook(force=True)
        reset_system.cook(force=True)
        visual_execute.cook(force=True)
        frame_execute.cook(force=True)
        if not callable(getattr(node_system.module, "add_node", None)):
            raise RuntimeError("Phase 3E node add wrapper did not load")
        if "phase3e_effects" not in reset_system.module.registered_hooks():
            raise RuntimeError("Phase 3E Reset All hook did not register")
        renderer.cook(force=True)
        composite.cook(force=True)
        phase_out.cook(force=True)
        final_out = _require(FINAL_OUT)
        final_out.cook(force=True)

        if list(composite.inputs) != [_require(PHASE2_OUT)]:
            raise RuntimeError("Phase 3E Composite wire is not phase2_out")
        if _path_from_par(composite.par.top) != effects_select.path:
            raise RuntimeError("Phase 3E Composite TOP parameter is incorrect")
        if str(composite.par.operand.eval()).lower() != "add":
            raise RuntimeError("Phase 3E Composite operation is not Add")
        if list(final_out.inputs) != [phase_out]:
            raise RuntimeError("FINAL_OUT is not connected to phase3e_out")
        for operator in (renderer, composite, phase_out, final_out):
            if list(operator.errors()):
                raise RuntimeError("Phase 3E error on {}: {}".format(
                    operator.path, operator.errors()))
            if (int(operator.width), int(operator.height)) != (WIDTH, HEIGHT):
                raise RuntimeError("{} is not 1280x720".format(operator.path))

        for operator in (render_effects, manager, callbacks, renderer,
                         frame_execute, effects_select, composite, phase_out,
                         node_system, reset_system, visual_execute, controls):
            operator.store(P3E_KEY, P3E_VALUE)
        _par(visual_execute, "active", True)
        _par(frame_execute, "active", True)
    except Exception:
        node_system.text = old_node_code
        reset_system.text = old_reset_code
        visual_execute.text = old_refresh_code
        _par(visual_execute, "active", old_refresh_active)
        if old_final_inputs:
            _connect(_require(FINAL_OUT), old_final_inputs[0])
        raise

    print("[Phase 3E] Ripple and Ambient installed; TOE was NOT saved.")
    print("[Phase 3E] Existing visual-control values preserved.")
    print("[Phase 3E] Ambient Color added:", created_color)
    print("[Phase 3E] Effects renderer:", renderer.path)
    print("[Phase 3E] Reset hook: phase3e_effects")
    print("[Phase 3E] FINAL_OUT:", final_out.width, "x", final_out.height)
    return render_effects


PHASE3E_RESULT = build_phase3e()
