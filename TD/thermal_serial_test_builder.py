"""Install an isolated MLX90640 multi-source serial preview area.

Run in the TouchDesigner Textport while a v05-derived project is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\thermal_serial_test_builder.py', encoding='utf-8').read())

The builder creates only /project1/mutual_illumination/thermal_serial_test.
It does not connect to or modify mouse input, node_data, MST, visual controls,
Reset All, the existing render system, or FINAL_OUT. It never saves the TOE.
Close Arduino Serial Monitor before running because COM5 can have only one owner.
"""

ROOT = "/project1/mutual_illumination"
TEST = ROOT + "/thermal_serial_test"
SERIAL_IN = TEST + "/serial_in"
PARSER = TEST + "/serial_parser"
FRAME_STATE = TEST + "/thermal_frame_state"
SOURCES = TEST + "/thermal_sources"
POLL_EXECUTE = TEST + "/serial_poll_execute"
RENDER_CALLBACKS = TEST + "/moving_dot_callbacks"
MOVING_DOT = TEST + "/moving_dot"
OUT_PREVIEW = TEST + "/OUT_PREVIEW"

OWNER_KEY = "mutual_illumination_thermal_serial_test"
OWNER_VALUE = "multi_source_v03"
ACCEPTED_OWNER_VALUES = ("single_hotspot_v01", "single_hotspot_v02", OWNER_VALUE)
SERIAL_PORT = "COM5"
BAUD_RATE = "115200"
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 480
MAX_SOURCES = 8

PROTECTED_PATHS = (
    ROOT + "/input/node_input_panel",
    ROOT + "/input/reset_all_system",
    ROOT + "/data/node_data",
    ROOT + "/graph/edge_data",
    ROOT + "/render_nodes",
    ROOT + "/render_connections",
    ROOT + "/visual_controls",
    ROOT + "/output/FINAL_OUT",
)


PARSER_CODE = r'''"""Parse stable single-source THERMAL key=value lines."""
import math

SERIAL_IN = "/project1/mutual_illumination/thermal_serial_test/serial_in"
STATE = "/project1/mutual_illumination/thermal_serial_test/hotspot_state"
RENDERER = "/project1/mutual_illumination/thermal_serial_test/moving_dot"
SCHEMA = ("present", "u", "v", "centroid_x", "centroid_y", "area",
          "background_c", "max_c", "threshold_c", "fps", "seq",
          "status", "raw_line", "updated_at")
REQUIRED_KEYS = ("p", "u", "v", "cx", "cy", "area", "bg", "max",
                 "thr", "fps", "seq")
_last_line = None


def _write(values):
    table = op(STATE)
    if table is None:
        raise RuntimeError("Missing hotspot_state")
    table.clear()
    table.appendRow(SCHEMA)
    table.appendRow(values)


def _refresh():
    renderer = op(RENDERER)
    if renderer is not None:
        renderer.cook(force=True)


def _latest_thermal_line(serial_dat):
    # Serial DAT may expose extra columns. Search newest rows first and choose
    # the text field that carries the recognizable ESP32 summary.
    for row in range(serial_dat.numRows - 1, -1, -1):
        for column in range(serial_dat.numCols):
            value = serial_dat[row, column].val.strip("\x00\r\n ")
            if value.startswith("THERMAL|p="):
                return value
    return None


def parse_line(line):
    line = str(line).strip("\x00\r\n ")
    now = "{:.3f}".format(float(absTime.seconds))
    parts = line.split("|")
    fields = {}
    if not parts or parts[0] != "THERMAL":
        parts = []
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        fields[key.strip()] = value.strip()
    if any(key not in fields for key in REQUIRED_KEYS):
        _write((0, "", "", "", "", 0, "", "", "", "", "",
                "parse_error", line, now))
        _refresh()
        return False

    try:
        present = int(fields["p"])
        u, v = float(fields["u"]), float(fields["v"])
        centroid_x, centroid_y = float(fields["cx"]), float(fields["cy"])
        area = int(fields["area"])
        background = float(fields["bg"])
        maximum = float(fields["max"])
        threshold = float(fields["thr"])
        fps = float(fields["fps"])
        sequence = int(fields["seq"])
    except (TypeError, ValueError):
        _write((0, "", "", "", "", 0, "", "", "", "", "",
                "parse_error", line, now))
        _refresh()
        return False

    finite_values = (u, v, centroid_x, centroid_y, background, maximum,
                     threshold, fps)
    valid = (present in (0, 1) and
             all(math.isfinite(value) for value in finite_values) and
             0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 and
             0.0 <= centroid_x <= 31.0 and 0.0 <= centroid_y <= 23.0 and
             0 <= area <= 768 and fps >= 0.0 and sequence >= 0)
    status = ("present" if present else "absent") if valid else "out_of_range"
    shown_present = present if valid else 0
    _write((shown_present, u, v, centroid_x, centroid_y, area, background,
            maximum, threshold, fps, sequence, status, line, now))
    _refresh()
    return valid


def poll():
    global _last_line
    serial_dat = op(SERIAL_IN)
    if serial_dat is None or serial_dat.numRows < 1:
        return False
    line = _latest_thermal_line(serial_dat)
    if line is None or line == _last_line:
        return False
    _last_line = line
    return parse_line(line)
'''


POLL_EXECUTE_CODE = '''"""Poll the isolated Serial DAT while the timeline is playing."""
PARSER = "/project1/mutual_illumination/thermal_serial_test/serial_parser"

def onFrameStart(frame):
    parser = op(PARSER)
    if parser is not None:
        parser.module.poll()

def onStart(): return
def onCreate(): return
def onExit(): return
def onFrameEnd(frame): return
def onPlayStateChange(state): return
def onDeviceChange(): return
'''


RENDER_CODE = '''"""Render one normalized thermal hotspot as an isolated test dot."""
import numpy

STATE = "/project1/mutual_illumination/thermal_serial_test/hotspot_state"
WIDTH, HEIGHT = 640, 480
DOT_COLOR = numpy.array((1.0, 0.68, 0.30), dtype=numpy.float32)

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _normalized_position():
    table = op(STATE)
    if table is None or table.numRows < 2:
        return None
    try:
        if int(table[1, "present"].val) != 1:
            return None
        return float(table[1, "u"].val), float(table[1, "v"].val)
    except (TypeError, ValueError, AttributeError):
        return None

def onCook(scriptOp):
    image = numpy.zeros((HEIGHT, WIDTH, 4), dtype=numpy.float32)
    image[:, :, 3] = 1.0
    position = _normalized_position()
    if position is not None:
        u, v = position
        center_x = u * (WIDTH - 1)
        center_y = v * (HEIGHT - 1)
        yy, xx = numpy.ogrid[:HEIGHT, :WIDTH]
        distance_squared = (xx - center_x) ** 2 + (yy - center_y) ** 2
        halo = numpy.exp(-distance_squared / (2.0 * 12.0 ** 2)).astype(numpy.float32)
        image[:, :, :3] = halo[:, :, None] * DOT_COLOR * 0.32
        core = distance_squared <= 7.0 ** 2
        image[core, :3] = DOT_COLOR
    scriptOp.copyNumpyArray(image)

def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''


# V3 replaces the legacy single-hotspot parser above while keeping the old
# definition visible in source history for easier comparison and rollback.
PARSER_CODE = r'''"""Parse complete THERMAL2 multi-source snapshots."""
import math

SERIAL_IN = "/project1/mutual_illumination/thermal_serial_test/serial_in"
FRAME_STATE = "/project1/mutual_illumination/thermal_serial_test/thermal_frame_state"
SOURCES = "/project1/mutual_illumination/thermal_serial_test/thermal_sources"
RENDERER = "/project1/mutual_illumination/thermal_serial_test/moving_dot"
MAX_SOURCES = 8
FRAME_SCHEMA = ("session", "seq", "count", "background_c", "threshold_c",
                "fps", "status", "raw_line", "updated_at")
SOURCE_SCHEMA = ("track_id", "u", "v", "centroid_x", "centroid_y", "area",
                 "peak_c", "seen", "miss")
REQUIRED_KEYS = ("session", "seq", "count", "bg", "thr", "fps", "sources")
_last_line = None

def _refresh():
    renderer = op(RENDERER)
    if renderer is not None:
        renderer.cook(force=True)

def _write_frame(values):
    table = op(FRAME_STATE)
    if table is None:
        raise RuntimeError("Missing thermal_frame_state")
    table.clear()
    table.appendRow(FRAME_SCHEMA)
    table.appendRow(values)

def _write_sources(rows):
    table = op(SOURCES)
    if table is None:
        raise RuntimeError("Missing thermal_sources")
    table.clear()
    table.appendRow(SOURCE_SCHEMA)
    for row in rows:
        table.appendRow(row)

def _write_error(line, now, status):
    _write_frame(("", "", "", "", "", "", status, line, now))
    _refresh()

def _latest_thermal_line(serial_dat):
    for row in range(serial_dat.numRows - 1, -1, -1):
        for column in range(serial_dat.numCols):
            value = serial_dat[row, column].val.strip("\x00\r\n ")
            if value.startswith("THERMAL2|session="):
                return value
    return None

def _parse_source(record):
    parts = record.split(",")
    if len(parts) != 9:
        raise ValueError("source field count")
    track_id = int(parts[0])
    u, v = float(parts[1]), float(parts[2])
    centroid_x, centroid_y = float(parts[3]), float(parts[4])
    area = int(parts[5])
    peak = float(parts[6])
    seen, miss = int(parts[7]), int(parts[8])
    finite = (u, v, centroid_x, centroid_y, peak)
    valid = (track_id > 0 and all(math.isfinite(value) for value in finite) and
             0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 and
             0.0 <= centroid_x <= 31.0 and 0.0 <= centroid_y <= 23.0 and
             1 <= area <= 768 and seen in (0, 1) and 0 <= miss <= 1000)
    if not valid:
        raise ValueError("source out of range")
    return (track_id, u, v, centroid_x, centroid_y, area, peak, seen, miss)

def parse_line(line):
    line = str(line).strip("\x00\r\n ")
    now = "{:.3f}".format(float(absTime.seconds))
    parts = line.split("|")
    if not parts or parts[0] != "THERMAL2":
        _write_error(line, now, "parse_error")
        return False
    fields = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        fields[key.strip()] = value.strip()
    if any(key not in fields for key in REQUIRED_KEYS):
        _write_error(line, now, "parse_error")
        return False
    try:
        session = int(fields["session"])
        sequence = int(fields["seq"])
        count = int(fields["count"])
        background = float(fields["bg"])
        threshold = float(fields["thr"])
        fps = float(fields["fps"])
        records = [] if fields["sources"] == "" else fields["sources"].split(";")
        rows = [_parse_source(record) for record in records]
    except (TypeError, ValueError):
        _write_error(line, now, "parse_error")
        return False
    ids = [row[0] for row in rows]
    valid = (0 < session <= 0xFFFFFFFF and 0 <= sequence <= 0xFFFFFFFF and
             0 <= count <= MAX_SOURCES and count == len(rows) and
             len(ids) == len(set(ids)) and
             all(math.isfinite(value) for value in (background, threshold, fps)) and
             fps >= 0.0)
    if not valid:
        _write_error(line, now, "out_of_range")
        return False
    _write_sources(rows)
    _write_frame((session, sequence, count, background, threshold, fps,
                  "ok", line, now))
    _refresh()
    return True

def poll():
    global _last_line
    serial_dat = op(SERIAL_IN)
    if serial_dat is None or serial_dat.numRows < 1:
        return False
    line = _latest_thermal_line(serial_dat)
    if line is None or line == _last_line:
        return False
    _last_line = line
    return parse_line(line)
'''


RENDER_CODE = '''"""Render all normalized thermal tracks in the test preview."""
import numpy

SOURCES = "/project1/mutual_illumination/thermal_serial_test/thermal_sources"
WIDTH, HEIGHT = 640, 480
DOT_COLOR = numpy.array((1.0, 0.68, 0.30), dtype=numpy.float32)

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _positions():
    table = op(SOURCES)
    if table is None or table.numRows < 2:
        return []
    result = []
    for row in range(1, table.numRows):
        try:
            result.append((float(table[row, "u"].val), float(table[row, "v"].val)))
        except (TypeError, ValueError, AttributeError):
            continue
    return result

def onCook(scriptOp):
    image = numpy.zeros((HEIGHT, WIDTH, 4), dtype=numpy.float32)
    image[:, :, 3] = 1.0
    yy, xx = numpy.ogrid[:HEIGHT, :WIDTH]
    for u, v in _positions():
        center_x = u * (WIDTH - 1)
        center_y = v * (HEIGHT - 1)
        distance_squared = (xx - center_x) ** 2 + (yy - center_y) ** 2
        halo = numpy.exp(-distance_squared / (2.0 * 12.0 ** 2)).astype(numpy.float32)
        image[:, :, :3] += halo[:, :, None] * DOT_COLOR * 0.32
        core = distance_squared <= 7.0 ** 2
        image[core, :3] = DOT_COLOR
    numpy.clip(image[:, :, :3], 0.0, 1.0, out=image[:, :, :3])
    scriptOp.copyNumpyArray(image)

def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''


def _require(path):
    operator = op(path)
    if operator is None:
        raise RuntimeError("Thermal serial test missing required operator: " + path)
    return operator


def _set_par(operator, name, value):
    parameter = getattr(operator.par, name, None)
    if parameter is None:
        raise RuntimeError("Missing parameter {} on {}".format(name, operator.path))
    parameter.val = value


def _set_menu(operator, name, wanted):
    parameter = getattr(operator.par, name, None)
    if parameter is None:
        raise RuntimeError("Missing menu {} on {}".format(name, operator.path))
    wanted_lower = str(wanted).lower()
    for menu_name, menu_label in zip(parameter.menuNames, parameter.menuLabels):
        if wanted_lower == str(menu_name).lower() or wanted_lower == str(menu_label).lower():
            parameter.val = menu_name
            return
    for menu_name, menu_label in zip(parameter.menuNames, parameter.menuLabels):
        if wanted_lower in (str(menu_name) + " " + str(menu_label)).lower():
            parameter.val = menu_name
            return
    raise RuntimeError("Menu choice {} unavailable on {}".format(wanted, operator.path))


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


def _connect(target, source):
    if list(target.inputs) != [source]:
        for connector in target.inputConnectors:
            for connection in list(connector.connections):
                connection.disconnect()
        target.inputConnectors[0].connect(source)
    if list(target.inputs) != [source]:
        raise RuntimeError("Failed to connect {} -> {}".format(source.path, target.path))


def _validate_baseline():
    root = _require(ROOT)
    protected = {path: _require(path) for path in PROTECTED_PATHS}
    return root, protected


def _fill_frame_state(table):
    table.clear()
    table.appendRow(("session", "seq", "count", "background_c", "threshold_c",
                     "fps", "status", "raw_line", "updated_at"))
    table.appendRow(("", "", 0, "", "", "", "waiting_for_serial", "", ""))


def _fill_sources(table):
    table.clear()
    table.appendRow(("track_id", "u", "v", "centroid_x", "centroid_y", "area",
                     "peak_c", "seen", "miss"))


def _fill_info(table):
    table.clear()
    table.appendRow(("Purpose", "Isolated THERMAL2 multi-source serial preview"))
    table.appendRow(("Serial", "COM5, 115200 baud, 8-N-1, one snapshot per line"))
    table.appendRow(("Protocol", "THERMAL2|session=...|seq=...|count=...|bg=...|thr=...|fps=...|sources=..."))
    table.appendRow(("Source record", "track_id,u,v,cx,cy,area,peak_c,seen,miss"))
    table.appendRow(("Coordinates", "Canonical u/v from ESP32; TD applies no flip"))
    table.appendRow(("Maximum sources", str(MAX_SOURCES)))
    table.appendRow(("Preview", "640x480 diagnostic TOP; not projector resolution"))
    table.appendRow(("Output", OUT_PREVIEW))
    table.appendRow(("Isolation", "No node_data, MST, existing render, controls, reset, or FINAL_OUT"))


def build_thermal_serial_test():
    root, protected = _validate_baseline()

    test = _owned(root, "thermal_serial_test", baseCOMP)
    serial_in = _owned(test, "serial_in", serialDAT, initialize=False)
    parser = _owned(test, "serial_parser", textDAT)
    frame_state = _owned(test, "thermal_frame_state", tableDAT)
    sources = _owned(test, "thermal_sources", tableDAT)
    poll_execute = _owned(test, "serial_poll_execute", executeDAT, initialize=False)
    callbacks = _owned(test, "moving_dot_callbacks", textDAT)
    renderer = _owned(test, "moving_dot", scriptTOP, initialize=False)
    output = _owned(test, "OUT_PREVIEW", nullTOP)
    info = _owned(test, "thermal_test_info", tableDAT)

    test.nodeX, test.nodeY = 1580, -520
    test.color = (0.48, 0.20, 0.12)
    test.comment = "ISOLATED TEST: COM5 THERMAL2 snapshots to multi-dot preview"
    serial_in.nodeX, serial_in.nodeY = 0, 160
    parser.nodeX, parser.nodeY = 220, 160
    frame_state.nodeX, frame_state.nodeY = 440, 220
    sources.nodeX, sources.nodeY = 440, 80
    poll_execute.nodeX, poll_execute.nodeY = 220, 0
    callbacks.nodeX, callbacks.nodeY = 660, 0
    renderer.nodeX, renderer.nodeY = 660, 160
    output.nodeX, output.nodeY = 880, 160
    info.nodeX, info.nodeY = 0, -180

    # Configure fully before opening COM5.
    _set_par(serial_in, "active", False)
    _set_menu(serial_in, "format", "perline")
    _set_par(serial_in, "port", SERIAL_PORT)
    _set_menu(serial_in, "baudrate", BAUD_RATE)
    _set_menu(serial_in, "databits", "8")
    _set_menu(serial_in, "parity", "none")
    _set_menu(serial_in, "stopbits", "1")
    _set_par(serial_in, "clamp", True)
    _set_par(serial_in, "maxlines", 120)
    bytes_parameter = getattr(serial_in.par, "bytes", None)
    if bytes_parameter is not None:
        bytes_parameter.val = False

    _set_par(poll_execute, "active", False)
    parser.text = PARSER_CODE
    poll_execute.text = POLL_EXECUTE_CODE
    callbacks.text = RENDER_CODE
    _fill_frame_state(frame_state)
    _fill_sources(sources)
    _fill_info(info)

    _set_par(poll_execute, "framestart", True)
    for name in ("start", "create", "exit", "frameend", "playstatechange", "devicechange"):
        parameter = getattr(poll_execute.par, name, None)
        if parameter is not None:
            parameter.val = False

    _set_par(renderer, "callbacks", callbacks.path)
    _set_menu(renderer, "outputresolution", "custom")
    _set_par(renderer, "resolutionw", PREVIEW_WIDTH)
    _set_par(renderer, "resolutionh", PREVIEW_HEIGHT)
    _connect(output, renderer)

    for operator in (test, serial_in, parser, frame_state, sources, poll_execute,
                     callbacks, renderer, output, info):
        operator.store(OWNER_KEY, OWNER_VALUE)

    parser.cook(force=True)
    renderer.cook(force=True)
    output.cook(force=True)
    _set_par(poll_execute, "active", True)
    _set_par(serial_in, "active", True)

    if (int(renderer.width), int(renderer.height)) != (PREVIEW_WIDTH, PREVIEW_HEIGHT):
        raise RuntimeError("moving_dot preview resolution is not 640x480")
    if not bool(serial_in.par.active.eval()):
        raise RuntimeError("serial_in did not become active")
    errors = list(serial_in.errors())
    if errors:
        raise RuntimeError(
            "Serial DAT error (close Arduino Serial Monitor and verify COM5): " + repr(errors)
        )
    for path, original in protected.items():
        if op(path) != original:
            raise RuntimeError("Protected operator changed unexpectedly: " + path)

    print("[Thermal Serial Test] Installed COM5 THERMAL2 multi-source preview.")
    print("[Thermal Serial Test] View:", OUT_PREVIEW)
    print("[Thermal Serial Test] Frame:", FRAME_STATE)
    print("[Thermal Serial Test] Sources:", SOURCES)
    print("[Thermal Serial Test] TOE was NOT saved; existing systems were not connected.")
    return test


THERMAL_SERIAL_TEST_RESULT = build_thermal_serial_test()
