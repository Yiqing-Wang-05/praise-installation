"""Incrementally install Phase 1A into the existing Mutual Illumination TOE.

Run from the TouchDesigner Textport while TD_visual_prototype_v01.toe is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\phase1a_builder.py', encoding='utf-8').read())

This script does not save the project. Test the live result first, then save the
.toe manually. It only replaces operators carrying its Phase 1A ownership
marker and preserves valid rows already present in data/node_data.
"""


ROOT_PATH = "/project1/mutual_illumination"
WIDTH = 1280
HEIGHT = 720

MARKER_KEY = "mutual_illumination_phase1a"
MARKER_VALUE = "dynamic_nodes_v01"
TEMP_SUFFIX = "__phase1a_building"

PATHS = {
    "input": ROOT_PATH + "/input",
    "data": ROOT_PATH + "/data",
    "render": ROOT_PATH + "/render_nodes",
    "output": ROOT_PATH + "/output",
    "node_data": ROOT_PATH + "/data/node_data",
    "node_data_out": ROOT_PATH + "/data/node_data_out",
    "manager": ROOT_PATH + "/data/node_system",
    "panel": ROOT_PATH + "/input/node_input_panel",
    "panel_execute": ROOT_PATH + "/input/phase1a_panel_execute",
    "reset_button": ROOT_PATH + "/input/reset_nodes_button",
    "reset_execute": ROOT_PATH + "/input/phase1a_reset_execute",
    "callbacks": ROOT_PATH + "/render_nodes/phase1a_node_callbacks",
    "renderer": ROOT_PATH + "/render_nodes/phase1a_node_renderer",
    "select": ROOT_PATH + "/output/phase1a_nodes_select",
    "phase_out": ROOT_PATH + "/output/phase1a_out",
    "final": ROOT_PATH + "/output/FINAL_OUT",
}


NODE_SYSTEM_CODE = '''"""Phase 1A node data API. Loaded as a Text DAT module."""

ROOT_PATH = "/project1/mutual_illumination"
TABLE_PATH = ROOT_PATH + "/data/node_data"
RENDERER_PATH = ROOT_PATH + "/render_nodes/phase1a_node_renderer"
WIDTH = 1280
HEIGHT = 720


def _table():
    table = op(TABLE_PATH)
    if table is None:
        raise RuntimeError("Missing node table: " + TABLE_PATH)
    return table


def _next_id(table):
    existing = []
    for row_index in range(1, table.numRows):
        try:
            existing.append(int(table[row_index, "id"].val))
        except (TypeError, ValueError, AttributeError):
            pass
    return max(existing, default=0) + 1


def add_node(u, v):
    """Add a node from normalized Panel UV coordinates."""
    table = _table()
    u = min(max(float(u), 0.0), 1.0)
    v = min(max(float(v), 0.0), 1.0)
    node_id = _next_id(table)
    x = round(u * (WIDTH - 1), 3)
    # In this Panel viewer, v=0 is the top edge. NumPy row 0 is also the
    # top edge, so the value maps directly to py5-style image coordinates.
    y = round(v * (HEIGHT - 1), 3)
    table.appendRow((node_id, x, y))
    renderer = op(RENDERER_PATH)
    if renderer is not None:
        renderer.cook(force=True)
    print("[Phase 1A] Added node {} at ({:.1f}, {:.1f})".format(node_id, x, y))
    return node_id


def clear_nodes():
    table = _table()
    table.clear()
    table.appendRow(("id", "x", "y"))
    renderer = op(RENDERER_PATH)
    if renderer is not None:
        renderer.cook(force=True)
    print("[Phase 1A] Cleared all nodes")
'''


PANEL_EXECUTE_CODE = '''"""Create one node for each left-click on the input panel."""

PANEL_PATH = "/project1/mutual_illumination/input/node_input_panel"
MANAGER_PATH = "/project1/mutual_illumination/data/node_system"


def onOffToOn(panelValue):
    panel = op(PANEL_PATH)
    manager = op(MANAGER_PATH)
    if panel is None or manager is None:
        raise RuntimeError("Phase 1A panel or node manager is missing.")
    manager.module.add_node(panel.panel.u.val, panel.panel.v.val)
    return


def whileOn(panelValue):
    return


def onOnToOff(panelValue):
    return


def whileOff(panelValue):
    return


def onValueChange(panelValue):
    return
'''


RESET_EXECUTE_CODE = '''"""Clear Phase 1A nodes from the prototype debug button."""

MANAGER_PATH = "/project1/mutual_illumination/data/node_system"


def onOffToOn(panelValue):
    manager = op(MANAGER_PATH)
    if manager is None:
        raise RuntimeError("Phase 1A node manager is missing.")
    manager.module.clear_nodes()
    return


def whileOn(panelValue):
    return


def onOnToOff(panelValue):
    return


def whileOff(panelValue):
    return


def onValueChange(panelValue):
    return
'''


SCRIPT_TOP_CODE = '''"""Render every node_data row into one scalable Script TOP."""

import numpy


TABLE_PATH = "/project1/mutual_illumination/data/node_data"
WIDTH = 1280
HEIGHT = 720
RADIUS = 13.0
EDGE_SOFTNESS = 1.25
NODE_RGB = numpy.array((255.0, 206.0, 137.0), dtype=numpy.float32) / 255.0


def onSetupParameters(scriptOp):
    return


def onPulse(par):
    return


def _read_nodes(table):
    nodes = []
    if table is None or table.numRows < 2:
        return nodes
    for row_index in range(1, table.numRows):
        try:
            node_id = int(table[row_index, "id"].val)
            x = float(table[row_index, "x"].val)
            y = float(table[row_index, "y"].val)
        except (TypeError, ValueError, AttributeError):
            continue
        nodes.append((node_id, x, y))
    return nodes


def onCook(scriptOp):
    image = numpy.zeros((HEIGHT, WIDTH, 4), dtype=numpy.float32)
    image[:, :, 3] = 1.0
    table = op(TABLE_PATH)

    for _node_id, x, y in _read_nodes(table):
        margin = int(RADIUS + EDGE_SOFTNESS + 2.0)
        x0 = max(0, int(x) - margin)
        x1 = min(WIDTH, int(x) + margin + 1)
        y0 = max(0, int(y) - margin)
        y1 = min(HEIGHT, int(y) + margin + 1)
        if x0 >= x1 or y0 >= y1:
            continue

        yy, xx = numpy.ogrid[y0:y1, x0:x1]
        distance = numpy.sqrt((xx - x) ** 2 + (yy - y) ** 2)
        coverage = numpy.clip(
            (RADIUS + EDGE_SOFTNESS - distance) / EDGE_SOFTNESS,
            0.0,
            1.0,
        ).astype(numpy.float32)
        patch = image[y0:y1, x0:x1, :3]
        numpy.maximum(patch, coverage[:, :, None] * NODE_RGB, out=patch)

    scriptOp.copyNumpyArray(image)
    return


def onGetCookLevel(scriptOp):
    return CookLevel.AUTOMATIC
'''


def _require_op(path):
    operator = op(path)
    if operator is None:
        raise RuntimeError("Required bootstrap operator is missing: " + path)
    return operator


def _require_par(operator, name):
    parameter = getattr(operator.par, name, None)
    if parameter is None:
        raise RuntimeError(
            "Required parameter {!r} is unavailable on {} ({}).".format(
                name, operator.path, operator.opType
            )
        )
    return parameter


def _set_par(operator, name, value):
    _require_par(operator, name).val = value


def _normalise(value):
    return "".join(character.lower() for character in str(value)
                   if character.isalnum())


def _set_menu(operator, name, choices):
    parameter = _require_par(operator, name)
    menu_names = list(parameter.menuNames)
    menu_labels = list(parameter.menuLabels)
    entries = [(_normalise(n), _normalise(label))
               for n, label in zip(menu_names, menu_labels)]
    for choice in choices:
        wanted = _normalise(choice)
        for index, entry in enumerate(entries):
            if wanted in entry:
                parameter.val = menu_names[index]
                return
    raise RuntimeError(
        "Expected menu value {} is unavailable for {}.par.{}; choices are {}".format(
            tuple(choices), operator.path, name,
            tuple(zip(menu_names, menu_labels)),
        )
    )


def _place(operator, x, y, color, comment):
    operator.nodeX = x
    operator.nodeY = y
    operator.color = color
    operator.comment = comment
    return operator


def _mark(operator):
    operator.store(MARKER_KEY, MARKER_VALUE)
    return operator


def _is_owned(operator):
    return operator is not None and operator.fetch(
        MARKER_KEY, None, search=False
    ) == MARKER_VALUE


def _assert_owned_or_missing(parent_op, name):
    existing = parent_op.op(name)
    if existing is not None and not _is_owned(existing):
        raise RuntimeError(
            "Refusing to replace unowned operator: " + existing.path
        )
    return existing


def _remove_owned(parent_op, name):
    existing = parent_op.op(name)
    if existing is None:
        return
    if not _is_owned(existing):
        raise RuntimeError("Refusing to remove unowned operator: " + existing.path)
    existing.destroy()


def _connect_input(target, source, index=0):
    connectors = target.inputConnectors
    if index < 0 or index >= len(connectors):
        raise RuntimeError(
            "{} exposes {} input connector(s), cannot connect index {}.".format(
                target.path, len(connectors), index
            )
        )
    connectors[index].connect(source)


def _preserve_node_rows(table):
    rows = []
    if table.numRows > 1:
        for row_index in range(1, table.numRows):
            try:
                node_id = int(table[row_index, "id"].val)
                x = float(table[row_index, "x"].val)
                y = float(table[row_index, "y"].val)
            except (TypeError, ValueError, AttributeError):
                continue
            rows.append((node_id, x, y))
    table.clear()
    table.appendRow(("id", "x", "y"))
    for row in rows:
        table.appendRow(row)
    return len(rows)


def build_phase1a():
    root = _require_op(ROOT_PATH)
    input_module = _require_op(PATHS["input"])
    data_module = _require_op(PATHS["data"])
    render_module = _require_op(PATHS["render"])
    output_module = _require_op(PATHS["output"])
    node_data = _require_op(PATHS["node_data"])
    node_data_out = _require_op(PATHS["node_data_out"])
    final_out = _require_op(PATHS["final"])

    if node_data.opType != "tableDAT":
        raise RuntimeError(PATHS["node_data"] + " must be a Table DAT.")

    stable_names = (
        (input_module, (
            "node_input_panel",
            "phase1a_panel_execute",
            "reset_nodes_button",
            "phase1a_reset_execute",
        )),
        (data_module, ("node_system",)),
        (render_module, ("phase1a_node_callbacks", "phase1a_node_renderer")),
        (output_module, ("phase1a_nodes_select", "phase1a_out")),
    )
    for parent_op, names in stable_names:
        for name in names:
            _assert_owned_or_missing(parent_op, name)
            stale_temp = parent_op.op(name + TEMP_SUFFIX)
            if stale_temp is not None:
                if not _is_owned(stale_temp):
                    raise RuntimeError(
                        "Refusing to remove unowned temporary operator: "
                        + stale_temp.path
                    )
                stale_temp.destroy()

    preserved_count = _preserve_node_rows(node_data)

    manager = _mark(data_module.create(
        textDAT, "node_system" + TEMP_SUFFIX
    ))
    manager.text = NODE_SYSTEM_CODE
    _place(manager, 360, 80, (0.24, 0.34, 0.25),
           "Phase 1A node IDs and Table DAT updates")

    callbacks = _mark(render_module.create(
        textDAT, "phase1a_node_callbacks" + TEMP_SUFFIX
    ))
    callbacks.text = SCRIPT_TOP_CODE
    _place(callbacks, 0, -80, (0.52, 0.31, 0.12),
           "Callbacks for the procedural node Script TOP")

    renderer = _mark(render_module.create(
        scriptTOP, "phase1a_node_renderer" + TEMP_SUFFIX, initialize=False
    ))
    _place(renderer, 220, 40, (0.60, 0.36, 0.12),
           "All node_data rows rendered in one TOP")
    _set_par(renderer, "callbacks", callbacks.path)
    _set_menu(renderer, "outputresolution", ("custom", "Custom Resolution"))
    _set_par(renderer, "resolutionw", WIDTH)
    _set_par(renderer, "resolutionh", HEIGHT)

    select_top = _mark(output_module.create(
        selectTOP, "phase1a_nodes_select" + TEMP_SUFFIX
    ))
    _place(select_top, 0, -80, (0.58, 0.35, 0.13),
           "Select the Phase 1A procedural node texture")
    _set_par(select_top, "top", renderer.path)

    phase_out = _mark(output_module.create(
        nullTOP, "phase1a_out" + TEMP_SUFFIX
    ))
    _place(phase_out, 190, -80, (0.68, 0.42, 0.15),
           "Phase 1A black background and dynamic nodes")
    _connect_input(phase_out, select_top)

    panel = _mark(input_module.create(
        containerCOMP, "node_input_panel" + TEMP_SUFFIX
    ))
    _place(panel, 0, 80, (0.20, 0.31, 0.37),
           "Open this panel viewer and left-click to add nodes")
    _set_par(panel, "w", WIDTH)
    _set_par(panel, "h", HEIGHT)
    _set_par(panel, "enable", True)
    _set_par(panel, "clickthrough", False)
    _set_par(panel, "mouserel", False)
    _set_par(panel, "uvbuttonsleft", True)
    _set_par(panel, "top", final_out.path)
    _set_menu(panel, "topfill", ("off", "Stretch"))
    _set_par(panel, "bgcolorr", 0.0)
    _set_par(panel, "bgcolorg", 0.0)
    _set_par(panel, "bgcolorb", 0.0)
    _set_par(panel, "bgalpha", 1.0)
    panel.viewer = True
    panel.activeViewer = True

    panel_execute = _mark(input_module.create(
        panelexecuteDAT, "phase1a_panel_execute" + TEMP_SUFFIX,
        initialize=False,
    ))
    panel_execute.text = PANEL_EXECUTE_CODE
    _place(panel_execute, 240, 80, (0.20, 0.31, 0.37),
           "Adds one table row on each lselect off-to-on event")
    _set_par(panel_execute, "active", False)
    _set_par(panel_execute, "panels", panel.path)
    _set_par(panel_execute, "panelvalue", "lselect")
    _set_par(panel_execute, "offtoon", True)
    _set_par(panel_execute, "whileon", False)
    _set_par(panel_execute, "ontooff", False)
    _set_par(panel_execute, "whileoff", False)
    _set_par(panel_execute, "valuechange", False)

    reset_button = _mark(input_module.create(
        buttonCOMP, "reset_nodes_button" + TEMP_SUFFIX
    ))
    _place(reset_button, 0, -80, (0.35, 0.18, 0.12),
           "Prototype debug control: clear all dynamic nodes")
    _set_par(reset_button, "label", "Reset Nodes")
    _set_menu(reset_button, "buttontype", ("momentary", "Momentary"))
    _set_par(reset_button, "w", 180)
    _set_par(reset_button, "h", 52)
    _set_par(reset_button, "enable", True)
    _set_par(reset_button, "clickthrough", False)
    reset_button.viewer = True
    reset_button.activeViewer = True

    reset_execute = _mark(input_module.create(
        panelexecuteDAT, "phase1a_reset_execute" + TEMP_SUFFIX,
        initialize=False,
    ))
    reset_execute.text = RESET_EXECUTE_CODE
    _place(reset_execute, 240, -80, (0.35, 0.18, 0.12),
           "Clear node_data when the Reset Nodes button is pressed")
    _set_par(reset_execute, "active", False)
    _set_par(reset_execute, "panels", reset_button.path)
    _set_par(reset_execute, "panelvalue", "state")
    _set_par(reset_execute, "offtoon", True)
    _set_par(reset_execute, "whileon", False)
    _set_par(reset_execute, "ontooff", False)
    _set_par(reset_execute, "whileoff", False)
    _set_par(reset_execute, "valuechange", False)

    # Commit only after every new operator and required parameter succeeded.
    for parent_op, names in stable_names:
        for name in names:
            _remove_owned(parent_op, name)

    manager.name = "node_system"
    callbacks.name = "phase1a_node_callbacks"
    renderer.name = "phase1a_node_renderer"
    select_top.name = "phase1a_nodes_select"
    phase_out.name = "phase1a_out"
    panel.name = "node_input_panel"
    panel_execute.name = "phase1a_panel_execute"
    reset_button.name = "reset_nodes_button"
    reset_execute.name = "phase1a_reset_execute"

    # Refresh path parameters after transactional temp names have been removed.
    _set_par(renderer, "callbacks", callbacks.path)
    _set_par(select_top, "top", renderer.path)
    _set_par(panel, "top", final_out.path)
    _set_par(panel_execute, "panels", panel.path)
    _set_par(reset_execute, "panels", reset_button.path)
    _connect_input(final_out, phase_out)
    _connect_input(node_data_out, node_data)
    _set_par(panel_execute, "active", True)
    _set_par(reset_execute, "active", True)

    renderer.cook(force=True)

    print("[Phase 1A] Incremental build complete; project was NOT auto-saved.")
    print("[Phase 1A] Click panel:", panel.path)
    print("[Phase 1A] Node data:", node_data.path)
    print("[Phase 1A] Renderer:", renderer.path)
    print("[Phase 1A] Reset button:", reset_button.path)
    print("[Phase 1A] Preserved nodes:", preserved_count)
    print("[Phase 1A] Test first, then press Ctrl+S to save the TOE.")
    return panel


PHASE1A_RESULT = build_phase1a()
