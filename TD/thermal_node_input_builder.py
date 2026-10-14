"""Install an isolated multi-source thermal adapter for the existing node graph.

Run in the TouchDesigner Textport while the verified v05-derived thermal project
is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\thermal_node_input_builder.py', encoding='utf-8').read())

The builder defaults to Mouse input and never saves the TOE. It adds controlled
external-node CRUD functions to node_system, registers one Reset All hook, and
creates only /project1/mutual_illumination/input/thermal_node_input. Existing
MST, renderers, visual controls, effects, mouse add_node(), and FINAL_OUT are not
rewritten or reconnected.
"""

ROOT = "/project1/mutual_illumination"
INPUT = ROOT + "/input"
THERMAL_TEST = ROOT + "/thermal_serial_test"
THERMAL_FRAME_STATE = THERMAL_TEST + "/thermal_frame_state"
THERMAL_SOURCES = THERMAL_TEST + "/thermal_sources"
NODE_DATA = ROOT + "/data/node_data"
NODE_SYSTEM = ROOT + "/data/node_system"
MOUSE_EXECUTE = INPUT + "/phase1b_frame_execute"
GRAPH_SYSTEM = ROOT + "/graph/graph_system"
RIPPLE_MANAGER = ROOT + "/render_effects/phase3e_effects_manager"
RESET_SYSTEM = INPUT + "/reset_all_system"
FINAL_OUT = ROOT + "/output/FINAL_OUT"

ADAPTER = INPUT + "/thermal_node_input"
MANAGER = ADAPTER + "/thermal_node_manager"
EXECUTE = ADAPTER + "/thermal_node_execute"
STATUS = ADAPTER + "/thermal_node_status"
BINDINGS = ADAPTER + "/thermal_node_bindings"
INFO = ADAPTER + "/thermal_node_info"

OWNER_KEY = "mutual_illumination_thermal_node_input"
OWNER_VALUE = "multi_source_adapter_v02"
ACCEPTED_OWNER_VALUES = ("single_source_adapter_v01", OWNER_VALUE)
THERMAL_TEST_OWNER_KEY = "mutual_illumination_thermal_serial_test"
THERMAL_TEST_OWNER_VALUES = ("multi_source_v03",)
NODE_EXTENSION_MARKER = "\n# === Thermal external-node API v01 ===\n"
RESET_EXTENSION_MARKER = "\n# === Thermal node input reset hook v01 ===\n"
THERMAL_ID_START = 1000000
STALE_TIMEOUT_SECONDS = 1.0
NODE_SCHEMA = ("id", "x", "y", "dragging")

PROTECTED_PATHS = (
    ROOT + "/graph/edge_data",
    ROOT + "/render_nodes",
    ROOT + "/render_connections",
    ROOT + "/render_effects/phase3e_effects_renderer",
    ROOT + "/visual_controls",
    FINAL_OUT,
)


NODE_EXTENSION_CODE = '''"""Controlled external-node API for thermal input.

This extension deliberately does not replace or wrap the existing add_node().
"""
THERMAL_EXTERNAL_ID_MIN = 1000000

def _external_id(node_id):
    node_id = int(node_id)
    if node_id < THERMAL_EXTERNAL_ID_MIN:
        raise ValueError("External thermal node IDs must be >= 1000000")
    return node_id

def has_node(node_id):
    return _row(_table(), int(node_id)) is not None

def node_position(node_id):
    table = _table()
    row = _row(table, int(node_id))
    if row is None:
        return None
    return float(table[row, "x"].val), float(table[row, "y"].val)

def add_external_node(node_id, u, v):
    node_id = _external_id(node_id)
    table = _table()
    if _row(table, node_id) is not None:
        raise ValueError("Node ID already exists: {}".format(node_id))
    x, y = _xy(u, v)
    table.appendRow((node_id, x, y, 0))
    _request_render()
    _flush_render()
    print("[Thermal Node Input] Added external node", node_id)
    return node_id

def update_node(node_id, u, v):
    node_id = int(node_id)
    table = _table()
    row = _row(table, node_id)
    if row is None:
        return False
    x, y = _xy(u, v)
    table[row, "x"] = x
    table[row, "y"] = y
    table[row, "dragging"] = 0
    _request_render()
    _flush_render()
    return True

def remove_node(node_id):
    node_id = int(node_id)
    table = _table()
    row = _row(table, node_id)
    if row is None:
        return False
    if _drag_id() == node_id:
        release_drag()
        row = _row(table, node_id)
        if row is None:
            return True
    table.deleteRow(row)
    _request_render()
    _flush_render()
    print("[Thermal Node Input] Removed node", node_id)
    return True
'''


MANAGER_CODE = '''"""Single thermal-source lifecycle and Mouse/Thermal switch."""
import math

THERMAL_STATE = "/project1/mutual_illumination/thermal_serial_test/hotspot_state"
NODE_SYSTEM = "/project1/mutual_illumination/data/node_system"
MOUSE_EXECUTE = "/project1/mutual_illumination/input/phase1b_frame_execute"
RIPPLE_MANAGER = "/project1/mutual_illumination/render_effects/phase3e_effects_manager"
MANAGER = "/project1/mutual_illumination/input/thermal_node_input/thermal_node_manager"
STATUS = "/project1/mutual_illumination/input/thermal_node_input/thermal_node_status"
THERMAL_ID_START = 1000000
STALE_TIMEOUT_SECONDS = 1.0

SOURCE_KEY = "thermal_input_source"
NODE_ID_KEY = "thermal_owned_node_id"
NEXT_ID_KEY = "thermal_next_node_id"
LAST_SEQ_KEY = "thermal_last_seq"
LAST_PRESENT_KEY = "thermal_last_present"
LAST_RX_KEY = "thermal_last_rx_seconds"
SUPPRESSED_KEY = "thermal_suppressed_until_absent"
MESSAGE_KEY = "thermal_adapter_message"

def _owner():
    owner = op(MANAGER)
    if owner is None:
        raise RuntimeError("Missing thermal_node_manager")
    return owner

def _nodes():
    system = op(NODE_SYSTEM)
    if system is None:
        raise RuntimeError("Missing node_system")
    return system.module

def source():
    return str(_owner().fetch(SOURCE_KEY, "mouse", search=False)).lower()

def thermal_node_id():
    return _owner().fetch(NODE_ID_KEY, None, search=False)

def _set_mouse_active(active):
    execute = op(MOUSE_EXECUTE)
    if execute is None:
        raise RuntimeError("Missing mouse frame execute")
    execute.par.active = bool(active)

def _set_message(message):
    _owner().store(MESSAGE_KEY, str(message))
    _write_status()

def _write_status():
    owner = _owner()
    table = op(STATUS)
    if table is None:
        return
    table.clear()
    table.appendRow(("key", "value"))
    rows = (
        ("source", source()),
        ("thermal_node_id", thermal_node_id()),
        ("next_thermal_id", owner.fetch(NEXT_ID_KEY, THERMAL_ID_START, search=False)),
        ("last_seq", owner.fetch(LAST_SEQ_KEY, None, search=False)),
        ("last_present", owner.fetch(LAST_PRESENT_KEY, 0, search=False)),
        ("last_rx_seconds", owner.fetch(LAST_RX_KEY, None, search=False)),
        ("suppressed_until_absent", int(bool(owner.fetch(SUPPRESSED_KEY, False, search=False)))),
        ("stale_timeout_seconds", STALE_TIMEOUT_SECONDS),
        ("message", owner.fetch(MESSAGE_KEY, "ready", search=False)),
    )
    for key, value in rows:
        table.appendRow((key, "" if value is None else value))

def _remove_owned_node(reason):
    owner = _owner()
    node_id = thermal_node_id()
    if node_id is not None:
        _nodes().remove_node(int(node_id))
    owner.store(NODE_ID_KEY, None)
    owner.store(MESSAGE_KEY, str(reason))
    _write_status()

def _allocate_id():
    owner, nodes = _owner(), _nodes()
    node_id = max(THERMAL_ID_START,
                  int(owner.fetch(NEXT_ID_KEY, THERMAL_ID_START, search=False)))
    while nodes.has_node(node_id):
        node_id += 1
    owner.store(NEXT_ID_KEY, node_id + 1)
    return node_id

def _create_node(u, v):
    owner, nodes = _owner(), _nodes()
    node_id = _allocate_id()
    nodes.add_external_node(node_id, u, v)
    owner.store(NODE_ID_KEY, node_id)
    position = nodes.node_position(node_id)
    ripple = op(RIPPLE_MANAGER)
    if ripple is not None and position is not None:
        ripple.module.trigger(node_id, position[0], position[1],
                              float(absTime.seconds))
    owner.store(MESSAGE_KEY, "thermal node created")
    _write_status()
    return node_id

def _update_node(u, v):
    owner = _owner()
    node_id = thermal_node_id()
    if node_id is None:
        return _create_node(u, v)
    if not _nodes().update_node(int(node_id), u, v):
        owner.store(NODE_ID_KEY, None)
        owner.store(MESSAGE_KEY, "owned node missing; waiting for next seq")
        _write_status()
        return None
    owner.store(MESSAGE_KEY, "thermal node updated")
    _write_status()
    return node_id

def set_source(value):
    wanted = str(value).strip().lower()
    if wanted not in ("mouse", "thermal"):
        raise ValueError("Input source must be 'mouse' or 'thermal'")
    owner = _owner()
    current = source()
    if wanted == "thermal":
        node_system = _nodes()
        node_system.release_drag()
        _set_mouse_active(False)
        owner.store(SOURCE_KEY, "thermal")
        if current != "thermal":
            owner.store(LAST_SEQ_KEY, None)
            owner.store(LAST_PRESENT_KEY, 0)
            owner.store(LAST_RX_KEY, None)
            owner.store(SUPPRESSED_KEY, False)
        owner.store(MESSAGE_KEY, "thermal active; mouse writes disabled")
    else:
        _remove_owned_node("thermal node removed for mouse mode")
        owner.store(SOURCE_KEY, "mouse")
        owner.store(LAST_SEQ_KEY, None)
        owner.store(LAST_PRESENT_KEY, 0)
        owner.store(LAST_RX_KEY, None)
        owner.store(SUPPRESSED_KEY, False)
        _set_mouse_active(True)
        owner.store(MESSAGE_KEY, "mouse active")
    _write_status()
    print("[Thermal Node Input] Source:", wanted)
    return wanted

def _read_state():
    table = op(THERMAL_STATE)
    if table is None or table.numRows < 2:
        return None
    try:
        status = table[1, "status"].val
        if status not in ("present", "absent"):
            return None
        present = int(table[1, "present"].val)
        u = float(table[1, "u"].val)
        v = float(table[1, "v"].val)
        sequence = int(table[1, "seq"].val)
        if present not in (0, 1) or sequence < 0:
            return None
        if not (math.isfinite(u) and math.isfinite(v) and
                0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
            return None
        if (present == 1) != (status == "present"):
            return None
        return present, u, v, sequence
    except (TypeError, ValueError, AttributeError):
        return None

def _check_stale(now):
    owner = _owner()
    last_rx = owner.fetch(LAST_RX_KEY, None, search=False)
    if (thermal_node_id() is not None and last_rx is not None and
            now - float(last_rx) > STALE_TIMEOUT_SECONDS):
        _remove_owned_node("serial stale; thermal node removed")
        owner.store(LAST_PRESENT_KEY, 0)
        owner.store(LAST_RX_KEY, None)
        return True
    return False

def tick(now=None):
    if source() != "thermal":
        return False
    now = float(absTime.seconds if now is None else now)
    state = _read_state()
    if state is None:
        return _check_stale(now)
    present, u, v, sequence = state
    owner = _owner()
    last_sequence = owner.fetch(LAST_SEQ_KEY, None, search=False)
    if last_sequence is not None and int(last_sequence) == sequence:
        return _check_stale(now)

    owner.store(LAST_SEQ_KEY, sequence)
    owner.store(LAST_RX_KEY, now)
    suppressed = bool(owner.fetch(SUPPRESSED_KEY, False, search=False))
    if present:
        if not suppressed:
            _update_node(u, v)
        else:
            owner.store(MESSAGE_KEY, "reset latch: waiting for p=0")
    else:
        _remove_owned_node("thermal source absent")
        owner.store(SUPPRESSED_KEY, False)
    owner.store(LAST_PRESENT_KEY, present)
    _write_status()
    return True

def on_reset_all():
    owner = _owner()
    owner.store(NODE_ID_KEY, None)
    owner.store(LAST_SEQ_KEY, None)
    owner.store(LAST_PRESENT_KEY, 0)
    owner.store(LAST_RX_KEY, None)
    owner.store(SUPPRESSED_KEY, source() == "thermal")
    owner.store(MESSAGE_KEY, "reset; waiting for p=0" if source() == "thermal" else "reset")
    _set_mouse_active(source() == "mouse")
    _write_status()
'''


# V2 replaces the single-source manager above. The legacy text remains in this
# builder only as an audit trail; MANAGER_CODE below is what TouchDesigner gets.
MANAGER_CODE = '''"""Multi-source thermal lifecycle and Mouse/Thermal switch."""
import math

FRAME_STATE = "/project1/mutual_illumination/thermal_serial_test/thermal_frame_state"
SOURCES = "/project1/mutual_illumination/thermal_serial_test/thermal_sources"
NODE_SYSTEM = "/project1/mutual_illumination/data/node_system"
MOUSE_EXECUTE = "/project1/mutual_illumination/input/phase1b_frame_execute"
RIPPLE_MANAGER = "/project1/mutual_illumination/render_effects/phase3e_effects_manager"
MANAGER = "/project1/mutual_illumination/input/thermal_node_input/thermal_node_manager"
STATUS = "/project1/mutual_illumination/input/thermal_node_input/thermal_node_status"
BINDINGS_TABLE = "/project1/mutual_illumination/input/thermal_node_input/thermal_node_bindings"
THERMAL_ID_START = 1000000
STALE_TIMEOUT_SECONDS = 1.0
MAX_SOURCES = 8

SOURCE_KEY = "thermal_input_source"
BINDINGS_KEY = "thermal_track_bindings_v2"
NEXT_ID_KEY = "thermal_next_node_id"
SESSION_KEY = "thermal_session_v2"
LAST_FRAME_KEY = "thermal_last_frame_v2"
LAST_RX_KEY = "thermal_last_rx_seconds"
IGNORED_KEY = "thermal_reset_ignored_tracks_v2"
MESSAGE_KEY = "thermal_adapter_message"
LEGACY_NODE_ID_KEY = "thermal_owned_node_id"

def _owner():
    owner = op(MANAGER)
    if owner is None:
        raise RuntimeError("Missing thermal_node_manager")
    return owner

def _nodes():
    system = op(NODE_SYSTEM)
    if system is None:
        raise RuntimeError("Missing node_system")
    return system.module

def source():
    return str(_owner().fetch(SOURCE_KEY, "mouse", search=False)).lower()

def _bindings():
    value = _owner().fetch(BINDINGS_KEY, {}, search=False)
    return dict(value) if isinstance(value, dict) else {}

def _store_bindings(value):
    _owner().store(BINDINGS_KEY, dict(value))

def _ignored():
    value = _owner().fetch(IGNORED_KEY, (), search=False)
    try:
        return set(value)
    except TypeError:
        return set()

def _store_ignored(value):
    _owner().store(IGNORED_KEY, tuple(sorted(value)))

def _set_mouse_active(active):
    execute = op(MOUSE_EXECUTE)
    if execute is None:
        raise RuntimeError("Missing mouse frame execute")
    execute.par.active = bool(active)

def _write_tables():
    owner = _owner()
    bindings = _bindings()
    status = op(STATUS)
    if status is not None:
        status.clear()
        status.appendRow(("key", "value"))
        rows = (
            ("source", source()),
            ("session", owner.fetch(SESSION_KEY, None, search=False)),
            ("last_frame", owner.fetch(LAST_FRAME_KEY, None, search=False)),
            ("active_nodes", len(bindings)),
            ("next_thermal_id", owner.fetch(NEXT_ID_KEY, THERMAL_ID_START, search=False)),
            ("last_rx_seconds", owner.fetch(LAST_RX_KEY, None, search=False)),
            ("reset_ignored_tracks", len(_ignored())),
            ("stale_timeout_seconds", STALE_TIMEOUT_SECONDS),
            ("message", owner.fetch(MESSAGE_KEY, "ready", search=False)),
        )
        for key, value in rows:
            status.appendRow((key, "" if value is None else value))
    table = op(BINDINGS_TABLE)
    if table is not None:
        table.clear()
        table.appendRow(("session", "track_id", "node_id", "u", "v", "seen", "miss"))
        for key in sorted(bindings):
            item = bindings[key]
            table.appendRow((key[0], key[1], item["node_id"], item["u"], item["v"],
                             item["seen"], item["miss"]))

def _allocate_node_id():
    owner, nodes = _owner(), _nodes()
    node_id = max(THERMAL_ID_START,
                  int(owner.fetch(NEXT_ID_KEY, THERMAL_ID_START, search=False)))
    while nodes.has_node(node_id):
        node_id += 1
    owner.store(NEXT_ID_KEY, node_id + 1)
    return node_id

def _remove_key(bindings, key):
    item = bindings.pop(key, None)
    if item is not None:
        _nodes().remove_node(int(item["node_id"]))

def _remove_all(reason):
    owner = _owner()
    bindings = _bindings()
    for key in list(bindings):
        _remove_key(bindings, key)
    legacy_id = owner.fetch(LEGACY_NODE_ID_KEY, None, search=False)
    if legacy_id is not None:
        _nodes().remove_node(int(legacy_id))
        owner.store(LEGACY_NODE_ID_KEY, None)
    _store_bindings(bindings)
    owner.store(MESSAGE_KEY, str(reason))

def _create_binding(bindings, key, item, now):
    node_id = _allocate_node_id()
    nodes = _nodes()
    nodes.add_external_node(node_id, item["u"], item["v"])
    bindings[key] = dict(item, node_id=node_id)
    position = nodes.node_position(node_id)
    ripple = op(RIPPLE_MANAGER)
    if ripple is not None and position is not None:
        ripple.module.trigger(node_id, position[0], position[1], float(now))

def _read_snapshot():
    frame = op(FRAME_STATE)
    sources = op(SOURCES)
    if frame is None or sources is None or frame.numRows < 2:
        return None
    try:
        if frame[1, "status"].val != "ok":
            return None
        session = int(frame[1, "session"].val)
        sequence = int(frame[1, "seq"].val)
        count = int(frame[1, "count"].val)
        if session <= 0 or sequence < 0 or count < 0 or count > MAX_SOURCES:
            return None
        result = {}
        for row in range(1, sources.numRows):
            track_id = int(sources[row, "track_id"].val)
            u = float(sources[row, "u"].val)
            v = float(sources[row, "v"].val)
            seen = int(sources[row, "seen"].val)
            miss = int(sources[row, "miss"].val)
            if (track_id <= 0 or not math.isfinite(u) or not math.isfinite(v) or
                    not 0.0 <= u <= 1.0 or not 0.0 <= v <= 1.0 or
                    seen not in (0, 1) or miss < 0 or track_id in result):
                return None
            result[track_id] = {"u": u, "v": v, "seen": seen, "miss": miss}
        if len(result) != count:
            return None
        return session, sequence, result
    except (TypeError, ValueError, AttributeError):
        return None

def _apply_snapshot(session, sequence, sources, now):
    owner = _owner()
    previous_session = owner.fetch(SESSION_KEY, None, search=False)
    if previous_session is None or int(previous_session) != session:
        _remove_all("thermal session changed; old nodes removed")
        _store_ignored(set())
        owner.store(SESSION_KEY, session)

    bindings = _bindings()
    ignored = _ignored()
    current_keys = {(session, track_id) for track_id in sources}
    ignored.intersection_update(current_keys)

    for key in list(bindings):
        if key not in current_keys:
            _remove_key(bindings, key)

    for track_id in sorted(sources):
        key = (session, track_id)
        item = sources[track_id]
        if key in ignored:
            continue
        existing = bindings.get(key)
        if existing is None:
            _create_binding(bindings, key, item, now)
            continue
        node_id = int(existing["node_id"])
        if not _nodes().update_node(node_id, item["u"], item["v"]):
            bindings.pop(key, None)
            _create_binding(bindings, key, item, now)
        else:
            bindings[key] = dict(item, node_id=node_id)

    _store_bindings(bindings)
    _store_ignored(ignored)
    owner.store(SESSION_KEY, session)
    owner.store(LAST_FRAME_KEY, (session, sequence))
    owner.store(LAST_RX_KEY, float(now))
    owner.store(MESSAGE_KEY, "thermal snapshot applied: {} source(s)".format(len(sources)))
    _write_tables()

def _check_stale(now):
    owner = _owner()
    last_rx = owner.fetch(LAST_RX_KEY, None, search=False)
    if last_rx is not None and now - float(last_rx) > STALE_TIMEOUT_SECONDS:
        if _bindings():
            _remove_all("serial stale; all thermal nodes removed")
        owner.store(LAST_RX_KEY, None)
        _write_tables()
        return True
    return False

def set_source(value):
    wanted = str(value).strip().lower()
    if wanted not in ("mouse", "thermal"):
        raise ValueError("Input source must be 'mouse' or 'thermal'")
    owner = _owner()
    if wanted == "thermal":
        _nodes().release_drag()
        _set_mouse_active(False)
        if source() != "thermal":
            _remove_all("starting thermal mode")
            owner.store(SESSION_KEY, None)
            owner.store(LAST_FRAME_KEY, None)
            owner.store(LAST_RX_KEY, None)
            _store_ignored(set())
        owner.store(SOURCE_KEY, "thermal")
        owner.store(MESSAGE_KEY, "thermal active; mouse writes disabled")
    else:
        _remove_all("thermal nodes removed for mouse mode")
        owner.store(SOURCE_KEY, "mouse")
        owner.store(SESSION_KEY, None)
        owner.store(LAST_FRAME_KEY, None)
        owner.store(LAST_RX_KEY, None)
        _store_ignored(set())
        _set_mouse_active(True)
        owner.store(MESSAGE_KEY, "mouse active")
    _write_tables()
    print("[Thermal Node Input] Source:", wanted)
    return wanted

def tick(now=None):
    if source() != "thermal":
        return False
    now = float(absTime.seconds if now is None else now)
    snapshot = _read_snapshot()
    if snapshot is None:
        return _check_stale(now)
    session, sequence, sources = snapshot
    frame_key = (session, sequence)
    if _owner().fetch(LAST_FRAME_KEY, None, search=False) == frame_key:
        return _check_stale(now)
    _apply_snapshot(session, sequence, sources, now)
    return True

def on_reset_all():
    owner = _owner()
    bindings = _bindings()
    if source() == "thermal":
        ignored = _ignored()
        ignored.update(bindings.keys())
        _store_ignored(ignored)
    else:
        _store_ignored(set())
    # Reset All has already cleared node_data; do not mutate it a second time.
    _store_bindings({})
    owner.store(LEGACY_NODE_ID_KEY, None)
    owner.store(LAST_FRAME_KEY, None)
    owner.store(LAST_RX_KEY, None)
    owner.store(MESSAGE_KEY, "reset; existing thermal track IDs suppressed")
    _set_mouse_active(source() == "mouse")
    _write_tables()
'''


EXECUTE_CODE = '''"""Advance the thermal adapter while the timeline is playing."""
MANAGER = "/project1/mutual_illumination/input/thermal_node_input/thermal_node_manager"

def onFrameStart(frame):
    manager = op(MANAGER)
    if manager is not None:
        try:
            manager.module.tick(float(absTime.seconds))
        except Exception as error:
            print("[Thermal Node Input] tick failed:", repr(error))

def onStart(): return
def onCreate(): return
def onExit(): return
def onFrameEnd(frame): return
def onPlayStateChange(state): return
def onDeviceChange(): return
'''


RESET_EXTENSION_CODE = '''# Register without changing Reset All's existing sequence.
def _thermal_node_input_reset_hook():
    manager = op("/project1/mutual_illumination/input/thermal_node_input/thermal_node_manager")
    if manager is not None:
        manager.module.on_reset_all()

register_reset_hook("thermal_node_input", _thermal_node_input_reset_hook)
'''


def _require(path):
    operator = op(path)
    if operator is None:
        raise RuntimeError("Thermal node input missing required operator: " + path)
    return operator


def _set_par(operator, name, value):
    parameter = getattr(operator.par, name, None)
    if parameter is None:
        raise RuntimeError("Missing parameter {} on {}".format(name, operator.path))
    parameter.val = value


def _owned(parent, name, operator_type, initialize=True):
    existing = parent.op(name)
    if existing is not None:
        if existing.fetch(OWNER_KEY, None, search=False) not in ACCEPTED_OWNER_VALUES:
            raise RuntimeError("Refusing to alter unowned operator: " + existing.path)
        return existing
    if initialize:
        created = parent.create(operator_type, name)
    else:
        created = parent.create(operator_type, name, initialize=False)
    created.store(OWNER_KEY, OWNER_VALUE)
    return created


def _base_text(text, marker):
    return str(text).split(marker, 1)[0].rstrip()


def _validate_baseline():
    root = _require(ROOT)
    input_module = _require(INPUT)
    node_data = _require(NODE_DATA)
    node_system = _require(NODE_SYSTEM)
    mouse_execute = _require(MOUSE_EXECUTE)
    graph_system = _require(GRAPH_SYSTEM)
    ripple_manager = _require(RIPPLE_MANAGER)
    reset_system = _require(RESET_SYSTEM)
    thermal_frame_state = _require(THERMAL_FRAME_STATE)
    thermal_sources = _require(THERMAL_SOURCES)
    _require(FINAL_OUT)

    schema = tuple(cell.val for cell in node_data.row(0))
    if schema != NODE_SCHEMA:
        raise RuntimeError("Unexpected node_data schema: " + repr(schema))
    frame_schema = tuple(cell.val for cell in thermal_frame_state.row(0))
    source_schema = tuple(cell.val for cell in thermal_sources.row(0))
    if not {"session", "seq", "count", "status"}.issubset(set(frame_schema)):
        raise RuntimeError("thermal_frame_state schema is incompatible: " + repr(frame_schema))
    if not {"track_id", "u", "v", "seen", "miss"}.issubset(set(source_schema)):
        raise RuntimeError("thermal_sources schema is incompatible: " + repr(source_schema))
    for table in (thermal_frame_state, thermal_sources):
        if table.fetch(THERMAL_TEST_OWNER_KEY, None, search=False) not in THERMAL_TEST_OWNER_VALUES:
            raise RuntimeError(table.path + " is not owned by the multi-source thermal test")
    for name in ("add_node", "release_drag", "clear_nodes"):
        if not callable(getattr(node_system.module, name, None)):
            raise RuntimeError("node_system API missing: " + name)
    if not callable(getattr(graph_system.module, "update_graph", None)):
        raise RuntimeError("graph_system.update_graph() is unavailable")
    if not callable(getattr(ripple_manager.module, "trigger", None)):
        raise RuntimeError("Ripple manager trigger() is unavailable")
    if not callable(getattr(reset_system.module, "register_reset_hook", None)):
        raise RuntimeError("Reset All hook API is unavailable")
    protected = {path: _require(path) for path in PROTECTED_PATHS}
    return root, input_module, node_system, mouse_execute, reset_system, protected


def _fill_status(table):
    table.clear()
    table.appendRow(("key", "value"))
    table.appendRow(("source", "mouse"))
    table.appendRow(("message", "builder installed; Mouse remains active"))


def _fill_bindings(table):
    table.clear()
    table.appendRow(("session", "track_id", "node_id", "u", "v", "seen", "miss"))


def _fill_info(table):
    table.clear()
    table.appendRow(("Purpose", "Up to eight canonical thermal tracks -> existing node graph"))
    table.appendRow(("Default", "Mouse; builder never auto-switches to Thermal"))
    table.appendRow(("Thermal frame", THERMAL_FRAME_STATE))
    table.appendRow(("Thermal sources", THERMAL_SOURCES))
    table.appendRow(("Node IDs", "1000000 upward; new ID for each presence generation"))
    table.appendRow(("Stale timeout", "1.0 second"))
    table.appendRow(("Set Thermal", "op('{}').module.set_source('thermal')".format(MANAGER)))
    table.appendRow(("Set Mouse", "op('{}').module.set_source('mouse')".format(MANAGER)))
    table.appendRow(("Isolation", "No visual, MST, coordinate, or FINAL_OUT modifications"))


def build_thermal_node_input():
    _, input_module, node_system, mouse_execute, reset_system, protected = _validate_baseline()
    adapter = _owned(input_module, "thermal_node_input", baseCOMP)
    manager = _owned(adapter, "thermal_node_manager", textDAT)
    execute = _owned(adapter, "thermal_node_execute", executeDAT, initialize=False)
    status = _owned(adapter, "thermal_node_status", tableDAT)
    bindings = _owned(adapter, "thermal_node_bindings", tableDAT)
    info = _owned(adapter, "thermal_node_info", tableDAT)

    adapter.nodeX, adapter.nodeY = 760, -520
    adapter.color = (0.52, 0.23, 0.10)
    adapter.comment = "Multi-source Thermal/Mouse input switch; visual graph unchanged"
    manager.nodeX, manager.nodeY = 0, 100
    execute.nodeX, execute.nodeY = 240, 100
    status.nodeX, status.nodeY = 480, 100
    bindings.nodeX, bindings.nodeY = 480, -40
    info.nodeX, info.nodeY = 0, -100

    old_node_text = node_system.text
    old_reset_text = reset_system.text
    old_mouse_active = bool(mouse_execute.par.active.eval())
    _set_par(execute, "active", False)
    try:
        node_system.text = (_base_text(old_node_text, NODE_EXTENSION_MARKER) +
                            NODE_EXTENSION_MARKER + NODE_EXTENSION_CODE)
        reset_system.text = (_base_text(old_reset_text, RESET_EXTENSION_MARKER) +
                             RESET_EXTENSION_MARKER + RESET_EXTENSION_CODE)
        manager.text = MANAGER_CODE
        execute.text = EXECUTE_CODE
        _fill_status(status)
        _fill_bindings(bindings)
        _fill_info(info)

        _set_par(execute, "framestart", True)
        for name in ("start", "create", "exit", "frameend", "playstatechange", "devicechange"):
            parameter = getattr(execute.par, name, None)
            if parameter is not None:
                parameter.val = False

        for operator in (adapter, manager, execute, status, bindings, info):
            operator.store(OWNER_KEY, OWNER_VALUE)
        if manager.fetch("thermal_next_node_id", None, search=False) is None:
            manager.store("thermal_next_node_id", THERMAL_ID_START)

        node_system.cook(force=True)
        manager.cook(force=True)
        reset_system.cook(force=True)
        for name in ("add_external_node", "update_node", "remove_node",
                     "has_node", "node_position"):
            if not callable(getattr(node_system.module, name, None)):
                raise RuntimeError("Thermal node_system extension missing: " + name)
        for name in ("set_source", "source", "tick", "on_reset_all"):
            if not callable(getattr(manager.module, name, None)):
                raise RuntimeError("Thermal manager API missing: " + name)
        if "thermal_node_input" not in reset_system.module.registered_hooks():
            raise RuntimeError("Thermal Reset All hook was not registered")

        _set_par(execute, "active", True)
        manager.module.set_source("mouse")
        if not bool(mouse_execute.par.active.eval()):
            raise RuntimeError("Builder did not leave Mouse input active")
        for path, original in protected.items():
            if op(path) != original:
                raise RuntimeError("Protected operator changed unexpectedly: " + path)
    except Exception:
        _set_par(execute, "active", False)
        node_system.text = old_node_text
        reset_system.text = old_reset_text
        node_system.cook(force=True)
        reset_system.cook(force=True)
        _set_par(mouse_execute, "active", old_mouse_active)
        raise

    print("[Thermal Node Input] Installed; TOE was NOT saved.")
    print("[Thermal Node Input] Default source: Mouse")
    print("[Thermal Node Input] Thermal:", "op('{}').module.set_source('thermal')".format(MANAGER))
    print("[Thermal Node Input] Mouse:", "op('{}').module.set_source('mouse')".format(MANAGER))
    print("[Thermal Node Input] Existing MST, visuals, controls, and FINAL_OUT unchanged.")
    return adapter


THERMAL_NODE_INPUT_RESULT = build_thermal_node_input()
