"""Build the stage-one Mutual Illumination TouchDesigner project skeleton.

Run this file from the TouchDesigner Textport in a new, unsaved project:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\bootstrap_builder.py', encoding='utf-8').read())

The script only replaces /project1/mutual_illumination, then saves the current
project as TD_visual_prototype_v01.toe beside this file. It does not open or
modify either of the older .toe projects in this repository.
"""

from pathlib import Path


PROJECT_NAME = "TD_visual_prototype_v01.toe"
OUTPUT_PATH = Path(
    r"C:\Users\Maipe\Documents\GitHub\praise-installation\TD"
) / PROJECT_NAME
ROOT_PATH = "/project1"
BUILD_NAME = "mutual_illumination"
TEMP_BUILD_NAME = "__mutual_illumination_building"
BUILDER_MARKER_KEY = "mutual_illumination_builder"
BUILDER_MARKER_VALUE = "bootstrap_v02"
RESOLUTION = (1280, 720)

MODULE_NAMES = {
    "input",
    "data",
    "graph",
    "render_connections",
    "render_nodes",
    "output",
}
LEGACY_BUILD_CHILDREN = MODULE_NAMES | {"config", "BUILD_NOTES"}


def _require_par(operator, name):
    """Return a required parameter or fail with an actionable TD path."""
    parameter = getattr(operator.par, name, None)
    if parameter is None:
        raise RuntimeError(
            "Required parameter {!r} is unavailable on {} ({}).".format(
                name, operator.path, operator.opType
            )
        )
    return parameter


def _set_required_par(operator, name, value):
    _require_par(operator, name).val = value


def _set_required_rgb(operator, names, rgb):
    if len(names) != 3 or len(rgb) != 3:
        raise ValueError("RGB parameter names and values must each have length 3.")
    for name, value in zip(names, rgb):
        _set_required_par(operator, name, value)


def _normalise_menu_text(value):
    return "".join(character.lower() for character in str(value)
                   if character.isalnum())


def _set_required_menu(operator, name, choices):
    """Select a menu entry by its real name or label in this TD build."""
    parameter = _require_par(operator, name)
    menu_names = list(parameter.menuNames)
    menu_labels = list(parameter.menuLabels)
    normalised_entries = [
        (_normalise_menu_text(menu_name), _normalise_menu_text(menu_label))
        for menu_name, menu_label in zip(menu_names, menu_labels)
    ]

    for choice in choices:
        wanted = _normalise_menu_text(choice)
        for index, (menu_name, menu_label) in enumerate(normalised_entries):
            if wanted in (menu_name, menu_label):
                parameter.val = menu_names[index]
                return

    raise RuntimeError(
        "None of the expected menu values {} exist for {}.par.{}. "
        "Available values: {}".format(
            tuple(choices), operator.path, name,
            tuple(zip(menu_names, menu_labels)),
        )
    )


def _set_resolution(operator, width, height):
    _set_required_menu(operator, "outputresolution", ("custom", "Custom Resolution"))
    _set_required_par(operator, "resolutionw", width)
    _set_required_par(operator, "resolutionh", height)


def _place(operator, x, y, color=None, comment=None):
    operator.nodeX = x
    operator.nodeY = y
    if color is not None:
        operator.color = color
    if comment:
        operator.comment = comment
    return operator


def _connect(target, index, source):
    """Connect an OP using TouchDesigner's Connector API."""
    if target.isMultiInputs:
        connected_count = len(target.inputs)
        if index != connected_count:
            raise RuntimeError(
                "Multi-input connections on {} must be appended in order; "
                "requested index {}, next index is {}.".format(
                    target.path, index, connected_count
                )
            )
        if not source.outputConnectors:
            raise RuntimeError("Source has no output connector: " + source.path)
        source.outputConnectors[0].connect(target)
        return

    connectors = target.inputConnectors
    if index < 0 or index >= len(connectors):
        raise RuntimeError(
            "Cannot connect input {} on {}: operator exposes {} input "
            "connector(s).".format(index, target.path, len(connectors))
        )
    connectors[index].connect(source)


def _has_builder_marker(component):
    return component.fetch(
        BUILDER_MARKER_KEY, None, search=False
    ) == BUILDER_MARKER_VALUE


def _is_first_run_partial(component):
    """Recognize only the exact unmarked skeleton left by bootstrap_v01."""
    child_names = {child.name for child in component.children}
    return (
        MODULE_NAMES.issubset(child_names)
        and child_names.issubset(LEGACY_BUILD_CHILDREN)
    )


def _assert_replaceable(component, label):
    if component is None:
        return
    if _has_builder_marker(component):
        return
    if component.name == BUILD_NAME and _is_first_run_partial(component):
        return
    raise RuntimeError(
        "Refusing to replace {} at {} because it is not marked as a "
        "bootstrap-generated component.".format(label, component.path)
    )


def _make_table(parent_op, name, columns, rows=()):
    table = parent_op.create(tableDAT, name)
    table.clear()
    table.appendRow(columns)
    for row in rows:
        table.appendRow(row)
    return table


def _make_module(root, name, x, color, description):
    module = root.create(baseCOMP, name)
    _place(module, x, 0, color, description)
    module.viewer = True
    return module


def _build_test_output(output_module):
    """Create a tiny TOP proof: black field plus one warm glowing node."""
    background = _place(
        output_module.create(constantTOP, "background"),
        0, 180, (0.18, 0.18, 0.18), "Black canvas",
    )
    _set_resolution(background, *RESOLUTION)
    _set_required_menu(background, "rgbaunit", ("u1", "0 to 1"))
    _set_required_rgb(background, ("colorr", "colorg", "colorb"),
                      (0.0, 0.0, 0.0))
    _set_required_par(background, "alpha", 1.0)

    node = _place(
        output_module.create(circleTOP, "bootstrap_node"),
        0, 60, (0.70, 0.43, 0.15), "Temporary warm node for pipeline validation",
    )
    _set_resolution(node, *RESOLUTION)
    _set_required_menu(node, "centerunit", ("pixels", "Pixels"))
    _set_required_par(node, "centerx", 0.0)
    _set_required_par(node, "centery", 0.0)
    _set_required_menu(node, "justifyh", ("center", "Center"))
    _set_required_menu(node, "justifyv", ("center", "Center"))
    _set_required_menu(node, "radiusunit", ("pixels", "Pixels"))
    _set_required_par(node, "radiusx", 16.0)
    _set_required_par(node, "radiusy", 16.0)
    _set_required_rgb(node, ("fillcolorr", "fillcolorg", "fillcolorb"),
                      (1.0, 206.0 / 255.0, 137.0 / 255.0))
    _set_required_par(node, "fillalpha", 1.0)
    _set_required_rgb(node, ("bgcolorr", "bgcolorg", "bgcolorb"),
                      (0.0, 0.0, 0.0))
    _set_required_par(node, "bgalpha", 0.0)
    _set_required_par(node, "borderwidth", 0.0)
    _set_required_par(node, "borderalpha", 0.0)
    _set_required_par(node, "antialias", True)

    glow = _place(
        output_module.create(blurTOP, "bootstrap_glow"),
        180, 60, (0.70, 0.43, 0.15), "Temporary broad amber glow",
    )
    _connect(glow, 0, node)
    _set_required_menu(glow, "type", ("gaussian", "Gaussian"))
    _set_required_par(glow, "size", 22.0)

    composite = _place(
        output_module.create(compositeTOP, "test_composite"),
        380, 120, (0.42, 0.28, 0.12), "Stage-one test composite",
    )
    _set_required_menu(composite, "operand", ("add", "Add"))
    _connect(composite, 0, background)
    _connect(composite, 1, glow)
    _connect(composite, 2, node)

    final = _place(
        output_module.create(nullTOP, "FINAL_OUT"),
        570, 120, (0.72, 0.48, 0.18), "Canonical output for future stages",
    )
    _connect(final, 0, composite)
    final.viewer = True
    final.display = True

    out_top = _place(output_module.create(outTOP, "out1"), 750, 120)
    _connect(out_top, 0, final)
    return final


def build():
    project_root = op(ROOT_PATH)
    if project_root is None:
        raise RuntimeError("Expected a new TouchDesigner project with /project1.")

    previous = project_root.op(BUILD_NAME)
    stale_temp = project_root.op(TEMP_BUILD_NAME)
    _assert_replaceable(previous, "the existing build")
    _assert_replaceable(stale_temp, "the temporary build")

    # Build transactionally. The previous generated component remains intact
    # until the replacement has been assembled without an exception.
    if stale_temp is not None:
        stale_temp.destroy()

    root = project_root.create(baseCOMP, TEMP_BUILD_NAME)
    root.store(BUILDER_MARKER_KEY, BUILDER_MARKER_VALUE)
    _place(root, 0, 0, (0.36, 0.23, 0.09),
           "Mutual Illumination procedural prototype")
    root.viewer = True

    modules = {
        "input": _make_module(
            root, "input", 0, (0.20, 0.31, 0.37),
            "Mouse input now; thermal blobs later",
        ),
        "data": _make_module(
            root, "data", 220, (0.24, 0.34, 0.25),
            "Dynamic node state and normalized node table",
        ),
        "graph": _make_module(
            root, "graph", 440, (0.35, 0.28, 0.16),
            "Distance, degree-limited MST, and sparse branches",
        ),
        "render_connections": _make_module(
            root, "render_connections", 660, (0.42, 0.25, 0.12),
            "Procedural mycelial connection renderer",
        ),
        "render_nodes": _make_module(
            root, "render_nodes", 880, (0.52, 0.31, 0.12),
            "Procedural warm node renderer",
        ),
        "output": _make_module(
            root, "output", 1100, (0.64, 0.39, 0.14),
            "Composite, feedback, and installation output",
        ),
    }

    config = _make_table(
        root,
        "config",
        ("key", "value", "source"),
        (
            ("resolution_width", RESOLUTION[0], "bootstrap"),
            ("resolution_height", RESOLUTION[1], "bootstrap"),
            ("background", "0,0,0", "Python config.py"),
            ("node_color", "255,206,137", "Python config.py"),
            ("core_color", "255,239,205", "Python config.py"),
            ("line_color", "231,159,83", "Python config.py"),
            ("max_connections_per_node", 3, "Python config.py"),
            ("connection_distance_px", 390.0, "Python config.py"),
        ),
    )
    _place(config, 0, -210, (0.37, 0.29, 0.14),
           "Initial values copied from the Python visual prototype")

    node_data = _make_table(
        modules["data"], "node_data",
        ("id", "x", "y", "phase", "age", "dragging"),
    )
    _place(node_data, 0, 80, comment="Stage two will populate this dynamically")
    node_out = _place(modules["data"].create(nullDAT, "node_data_out"), 180, 80)
    _connect(node_out, 0, node_data)

    edge_data = _make_table(
        modules["graph"], "edge_data",
        ("a_id", "b_id", "distance", "trunk"),
    )
    _place(edge_data, 0, 80, comment="Stage two will populate MST and branch edges")
    edge_out = _place(modules["graph"].create(nullDAT, "edge_data_out"), 180, 80)
    _connect(edge_out, 0, edge_data)

    notes = root.create(textDAT, "BUILD_NOTES")
    notes.text = """Mutual Illumination — stage-one bootstrap

This network is a generated skeleton based on the existing py5 prototype.
The visible warm node is only a pipeline test. Dynamic interaction, MST logic,
curved filaments, breathing, ripples, and thermal input belong to later stages.

Canonical tables:
  data/node_data_out
  graph/edge_data_out

Canonical image output:
  output/FINAL_OUT
"""
    _place(notes, 260, -210, (0.29, 0.25, 0.18))

    final = _build_test_output(modules["output"])

    if previous is not None:
        previous.destroy()
    root.name = BUILD_NAME

    save_path = OUTPUT_PATH
    if not project.save(save_path.as_posix()):
        raise RuntimeError("TouchDesigner did not save the project: " + str(save_path))

    print("[Mutual Illumination] Bootstrap build complete.")
    print("[Mutual Illumination] Root:", root.path)
    print("[Mutual Illumination] Output:", final.path)
    print("[Mutual Illumination] Saved:", save_path)
    return root


BUILD_RESULT = build()
