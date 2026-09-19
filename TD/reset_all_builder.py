"""Install a unified Reset All API and reuse the existing reset button.

Run in the TouchDesigner Textport while TD_visual_prototype_v04.toe is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\reset_all_builder.py', encoding='utf-8').read())

The builder is incremental, preserves all visual controls, and never saves the
project. It does not execute Reset All during installation.
"""

ROOT = "/project1/mutual_illumination"
INPUT_MODULE = ROOT + "/input"
RESET_BUTTON = INPUT_MODULE + "/reset_nodes_button"
RESET_EXECUTE = INPUT_MODULE + "/phase1a_reset_execute"
RESET_SYSTEM = INPUT_MODULE + "/reset_all_system"
NODE_DATA = ROOT + "/data/node_data"
NODE_SYSTEM = ROOT + "/data/node_system"
DIAGNOSTICS = ROOT + "/data/phase1b_diagnostics"
EDGE_DATA = ROOT + "/graph/edge_data"
GRAPH_SYSTEM = ROOT + "/graph/graph_system"
GRAPH_EXECUTE = ROOT + "/graph/phase2_graph_execute"
TRANSITION_MANAGER = ROOT + "/render_connections/phase3d_transition_manager"
NODE_RENDERER = ROOT + "/render_nodes/phase1a_node_renderer"
CONNECTION_RENDERER = ROOT + "/render_connections/phase2_connection_renderer"
PHASE1A_OUT = ROOT + "/output/phase1a_out"
COMPOSITE = ROOT + "/output/phase2_composite"
FINAL_OUT = ROOT + "/output/FINAL_OUT"

A1_KEY, A1_VALUE = "mutual_illumination_phase1a", "dynamic_nodes_v01"
B1_KEY, B1_VALUE = "mutual_illumination_phase1b", "mouse_drag_v03_diagnostics"
P2_KEY, P2_VALUE = "mutual_illumination_phase2", "dynamic_mst_v01"
P3B_KEY, P3B_VALUE = "mutual_illumination_phase3b", "node_glow_breathing_v01"
P3C_KEY, P3C_VALUE = "mutual_illumination_phase3c", "mycelium_connections_v01"
P3D_KEY, P3D_VALUE = "mutual_illumination_phase3d", "connection_transitions_v01"
RESET_KEY, RESET_VALUE = "mutual_illumination_reset_all", "unified_reset_v01"
EXPECTED_PROJECT = "TD_visual_prototype_v04.toe"
WIDTH, HEIGHT = 1280, 720
NODE_SCHEMA = ("id", "x", "y", "dragging")
EDGE_SCHEMA = ("edge_id", "a_id", "b_id", "ax", "ay", "bx", "by",
               "distance", "trunk")


RESET_SYSTEM_CODE = '''"""Public Reset All API for current and future interaction state."""
NODE_DATA = "/project1/mutual_illumination/data/node_data"
NODE_SYSTEM = "/project1/mutual_illumination/data/node_system"
DIAGNOSTICS = "/project1/mutual_illumination/data/phase1b_diagnostics"
EDGE_DATA = "/project1/mutual_illumination/graph/edge_data"
GRAPH_SYSTEM = "/project1/mutual_illumination/graph/graph_system"
TRANSITION_MANAGER = "/project1/mutual_illumination/render_connections/phase3d_transition_manager"
NODE_RENDERER = "/project1/mutual_illumination/render_nodes/phase1a_node_renderer"
CONNECTION_RENDERER = "/project1/mutual_illumination/render_connections/phase2_connection_renderer"
FINAL_OUT = "/project1/mutual_illumination/output/FINAL_OUT"

_reset_hooks = {}
_reset_running = False

def _require(path):
    operator = op(path)
    if operator is None:
        raise RuntimeError("Reset All missing operator: " + path)
    return operator

def _diag(name, value):
    table = op(DIAGNOSTICS)
    if table is None:
        return
    for row in range(1, table.numRows):
        if table[row, 0].val == name:
            table[row, 1] = "" if value is None else str(value)
            return

def register_reset_hook(name, callback):
    """Register a future Ripple/Ambient/etc. cleanup callback by stable name."""
    if not name or not callable(callback):
        raise ValueError("register_reset_hook requires a name and callable")
    _reset_hooks[str(name)] = callback

def unregister_reset_hook(name):
    _reset_hooks.pop(str(name), None)

def registered_hooks():
    return tuple(sorted(_reset_hooks))

def _reset_interaction_flags(manager):
    manager.store("phase1b_dragging_id", None)
    manager.store("phase1b_previous_lselect", 0)
    manager.store("phase1b_render_pending", False)
    manager.store("phase1b_panel_event_count", 0)
    _diag("status", "reset")
    _diag("lselect", 0)
    _diag("dragging_id", None)
    _diag("node_x", None)
    _diag("node_y", None)
    _diag("render_pending", 0)
    _diag("panel_event_count", 0)
    _diag("last_error", "")

def _run_extension_hooks():
    for name in tuple(sorted(_reset_hooks)):
        try:
            _reset_hooks[name]()
        except Exception as error:
            print("[Reset All] Hook {} failed: {}".format(name, repr(error)))

def reset_all():
    """Immediately clear interaction, graph, transitions, and rendered output."""
    global _reset_running
    if _reset_running:
        return False
    _reset_running = True
    try:
        node_system = _require(NODE_SYSTEM)
        graph_system = _require(GRAPH_SYSTEM)
        transitions = _require(TRANSITION_MANAGER)

        # Public APIs own their respective table/state invariants.
        node_system.module.clear_nodes()
        _reset_interaction_flags(node_system)
        transitions.module.clear()
        graph_system.module.update_graph(force=True)

        # update_graph cooks the connection renderer. Clear again afterward so
        # Reset can never be interpreted as an ordinary edge-removal fade.
        transitions.module.clear()
        _run_extension_hooks()

        # Explicit cooks make Reset independent of Timeline play state and DAT order.
        _require(NODE_RENDERER).cook(force=True)
        _require(CONNECTION_RENDERER).cook(force=True)
        _require(FINAL_OUT).cook(force=True)
        _reset_interaction_flags(node_system)

        node_table, edge_table = _require(NODE_DATA), _require(EDGE_DATA)
        if node_table.numRows != 1:
            raise RuntimeError("Reset All did not empty node_data")
        if edge_table.numRows != 1:
            raise RuntimeError("Reset All did not empty edge_data")
        if transitions.module.state_count() != 0:
            raise RuntimeError("Reset All did not clear transition state")
        print("[Reset All] Nodes, edges, transitions, and rendered output cleared.")
        return True
    finally:
        _reset_running = False
'''


RESET_EXECUTE_CODE = '''"""Route the existing button through the unified Reset All API."""
RESET_SYSTEM = "/project1/mutual_illumination/input/reset_all_system"

def onOffToOn(panelValue):
    system = op(RESET_SYSTEM)
    if system is None:
        raise RuntimeError("Reset All system is missing")
    system.module.reset_all()
    return

def whileOn(panelValue): return
def onOnToOff(panelValue): return
def whileOff(panelValue): return
def onValueChange(panelValue): return
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


def _owned(parent, name, kind):
    existing = parent.op(name)
    if existing is not None:
        if existing.fetch(RESET_KEY, None, search=False) != RESET_VALUE:
            raise RuntimeError("Refusing unowned operator: " + existing.path)
        return existing
    created = parent.create(kind, name)
    created.store(RESET_KEY, RESET_VALUE)
    return created


def _marker(operator, key, value, label):
    if operator.fetch(key, None, search=False) != value:
        raise RuntimeError(label + " ownership is missing on " + operator.path)


def _validate_v04():
    if project.name != EXPECTED_PROJECT:
        raise RuntimeError(
            "Reset All may only run in {}; current project is {}".format(
                EXPECTED_PROJECT, project.name))

    button = _require(RESET_BUTTON)
    reset_execute = _require(RESET_EXECUTE)
    node_system = _require(NODE_SYSTEM)
    graph_system = _require(GRAPH_SYSTEM)
    graph_execute = _require(GRAPH_EXECUTE)
    transitions = _require(TRANSITION_MANAGER)
    node_renderer = _require(NODE_RENDERER)
    connection_renderer = _require(CONNECTION_RENDERER)
    composite = _require(COMPOSITE)

    for operator in (button, reset_execute):
        _marker(operator, A1_KEY, A1_VALUE, "Phase 1A reset control")
    _marker(node_system, B1_KEY, B1_VALUE, "Phase 1B node system")
    for operator in (graph_system, graph_execute, connection_renderer, composite):
        _marker(operator, P2_KEY, P2_VALUE, "Phase 2 graph")
    _marker(node_renderer, P3B_KEY, P3B_VALUE, "Phase 3B node renderer")
    _marker(connection_renderer, P3C_KEY, P3C_VALUE, "Phase 3C renderer")
    _marker(transitions, P3D_KEY, P3D_VALUE, "Phase 3D transition manager")

    if not callable(getattr(node_system.module, "clear_nodes", None)):
        raise RuntimeError("node_system.clear_nodes() is unavailable")
    if not callable(getattr(graph_system.module, "update_graph", None)):
        raise RuntimeError("graph_system.update_graph() is unavailable")
    if not callable(getattr(transitions.module, "clear", None)):
        raise RuntimeError("transition manager clear() is unavailable")
    if not callable(getattr(transitions.module, "state_count", None)):
        raise RuntimeError("transition manager state_count() is unavailable")

    node_headers = tuple(cell.val for cell in _require(NODE_DATA).row(0))
    edge_headers = tuple(cell.val for cell in _require(EDGE_DATA).row(0))
    if node_headers != NODE_SCHEMA:
        raise RuntimeError("node_data schema changed: " + repr(node_headers))
    if edge_headers != EDGE_SCHEMA:
        raise RuntimeError("edge_data schema changed: " + repr(edge_headers))
    if list(composite.inputs) != [_require(PHASE1A_OUT)]:
        raise RuntimeError("Protected Composite wire is not phase1a_out")
    if _path_from_par(composite.par.top) != connection_renderer.path:
        raise RuntimeError("Protected Composite TOP parameter is incorrect")
    if str(composite.par.operand.eval()).lower() != "add":
        raise RuntimeError("Protected Composite operation is not Add")
    if (int(composite.width), int(composite.height)) != (WIDTH, HEIGHT):
        raise RuntimeError("Protected Composite is not 1280x720")
    return button, reset_execute


def build_reset_all():
    button, reset_execute = _validate_v04()
    system = _owned(_require(INPUT_MODULE), "reset_all_system", textDAT)
    system.nodeX, system.nodeY = 480, -80
    system.color = (0.46, 0.16, 0.12)
    system.comment = "Public unified Reset All API and future cleanup hooks"

    old_code = reset_execute.text
    old_active = bool(reset_execute.par.active.eval())
    old_label = reset_execute.comment
    old_button_label = button.par.label.eval()
    old_button_comment = button.comment
    _par(reset_execute, "active", False)
    try:
        system.text = RESET_SYSTEM_CODE
        system.cook(force=True)
        if not callable(getattr(system.module, "reset_all", None)):
            raise RuntimeError("reset_all_system module did not load reset_all()")
        if not callable(getattr(system.module, "register_reset_hook", None)):
            raise RuntimeError("reset_all_system module did not load hook API")

        reset_execute.text = RESET_EXECUTE_CODE
        reset_execute.comment = "Invoke the unified Reset All API"
        _par(button, "label", "Reset All")
        button.comment = "Clear nodes, graph, transitions, and interaction state"
        reset_execute.store(RESET_KEY, RESET_VALUE)
        button.store(RESET_KEY, RESET_VALUE)
        _par(reset_execute, "active", True)
    except Exception:
        reset_execute.text = old_code
        reset_execute.comment = old_label
        _par(button, "label", old_button_label)
        button.comment = old_button_comment
        _par(reset_execute, "active", old_active)
        raise

    final_out = _require(FINAL_OUT)
    if (int(final_out.width), int(final_out.height)) != (WIDTH, HEIGHT):
        raise RuntimeError("FINAL_OUT resolution changed during Reset All install")
    if list(final_out.errors()):
        raise RuntimeError("FINAL_OUT has errors: " + repr(final_out.errors()))

    print("[Reset All] Unified reset installed; TOE was NOT saved.")
    print("[Reset All] Existing button upgraded:", button.path)
    print("[Reset All] Public API:", system.path + ".module.reset_all()")
    print("[Reset All] Visual Controls were not changed.")
    return system


RESET_ALL_RESULT = build_reset_all()
