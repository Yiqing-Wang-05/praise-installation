"""Install Phase 3A unified visual controls into the open v02 TOE.

Run in the TouchDesigner Textport while TD_visual_prototype_v02.toe is open:

    exec(open(r'C:\\Users\\Maipe\\Documents\\GitHub\\praise-installation\\TD\\phase3a_builder.py', encoding='utf-8').read())

The builder is incremental, preserves existing custom parameter values, and
never saves the project.
"""

ROOT = "/project1/mutual_illumination"
CONTROLS = ROOT + "/visual_controls"
NODE_CALLBACKS = ROOT + "/render_nodes/phase1a_node_callbacks"
NODE_RENDERER = ROOT + "/render_nodes/phase1a_node_renderer"
CONNECTION_CALLBACKS = ROOT + "/render_connections/phase2_connection_callbacks"
CONNECTION_RENDERER = ROOT + "/render_connections/phase2_connection_renderer"
PHASE1A_OUT = ROOT + "/output/phase1a_out"
COMPOSITE = ROOT + "/output/phase2_composite"
PHASE2_OUT = ROOT + "/output/phase2_out"
FINAL_OUT = ROOT + "/output/FINAL_OUT"
GRAPH_EXECUTE = ROOT + "/graph/phase2_graph_execute"

B1_KEY, B1_VALUE = "mutual_illumination_phase1b", "mouse_drag_v03_diagnostics"
P2_KEY, P2_VALUE = "mutual_illumination_phase2", "dynamic_mst_v01"
P3_KEY, P3_VALUE = "mutual_illumination_phase3a", "visual_controls_v01"
EXPECTED_PROJECT = "TD_visual_prototype_v02.toe"
WIDTH, HEIGHT = 1280, 720


# kind, page, name, label, default, min, max
PARAMETERS = (
    ("float", "Node", "Nodesize", "Node Size (radius px)", 13.0, 2.0, 80.0),
    ("rgb", "Node", "Nodecolor", "Node Color", (1.0, 206/255, 137/255), 0.0, 1.0),
    ("float", "Node", "Edgesoftness", "Edge Softness", 1.25, 0.1, 12.0),

    ("rgb", "Connections", "Linecolor", "Line Color", (231/255, 159/255, 83/255), 0.0, 1.0),
    ("float", "Connections", "Lineweight", "Line Weight", 1.25, 0.1, 12.0),
    ("float", "Connections", "Linebrightness", "Line Brightness", 1.0, 0.0, 3.0),
    ("float", "Connections", "Branchbrightness", "Branch Brightness", 0.72, 0.0, 1.5),

    ("float", "Glow", "Glowamount", "Glow Amount [Reserved 3B]", 1.35, 0.0, 4.0),
    ("float", "Glow", "Glowradius", "Glow Radius [Reserved 3B]", 7.5, 0.0, 20.0),
    ("int", "Glow", "Glowlayers", "Glow Layers [Reserved 3B]", 16, 1, 32),
    ("float", "Glow", "Innerglowsize", "Inner Glow Size [Reserved 3B]", 2.4, 0.0, 8.0),

    ("toggle", "Breathing", "Breathingenabled", "Enable [Reserved 3B]", False, 0, 1),
    ("float", "Breathing", "Breathingspeed", "Speed [Reserved 3B]", 0.58, 0.0, 3.0),
    ("float", "Breathing", "Breathingamount", "Size Amount [Reserved 3B]", 0.23, 0.0, 1.0),
    ("float", "Breathing", "Breathingbrightness", "Brightness Amount [Reserved 3B]", 0.38, 0.0, 1.0),
    ("float", "Breathing", "Breathingglow", "Glow Amount [Reserved 3B]", 0.32, 0.0, 1.0),

    ("float", "Mycelium", "Curveamount", "Curve Amount [Reserved 3C]", 0.085, 0.0, 0.35),
    ("float", "Mycelium", "Curvemotion", "Curve Motion [Reserved 3C]", 0.22, 0.0, 2.0),
    ("float", "Mycelium", "Filamentspread", "Filament Spread [Reserved 3C]", 3.2, 0.0, 16.0),
    ("float", "Mycelium", "Sidebranchamount", "Side Branch Amount [Reserved 3C]", 0.55, 0.0, 1.0),
    ("float", "Mycelium", "Energyspeed", "Energy Speed [Reserved 3C]", 0.085, 0.0, 1.0),

    ("toggle", "Ripple", "Rippleenabled", "Enable [Reserved 3D]", False, 0, 1),
    ("rgb", "Ripple", "Ripplecolor", "Ripple Color [Reserved 3D]", (1.0, 191/255, 112/255), 0.0, 1.0),
    ("float", "Ripple", "Ripplestrength", "Strength [Reserved 3D]", 1.0, 0.0, 3.0),
    ("float", "Ripple", "Rippleduration", "Duration [Reserved 3D]", 2.6, 0.1, 10.0),
    ("float", "Ripple", "Ripplemaxradius", "Max Radius [Reserved 3D]", 105.0, 1.0, 400.0),

    ("toggle", "Ambient", "Ambientenabled", "Enable [Reserved 3E]", False, 0, 1),
    ("float", "Ambient", "Ambientglow", "Glow Amount [Reserved 3E]", 0.72, 0.0, 3.0),
    ("float", "Ambient", "Ambientradius", "Radius [Reserved 3E]", 0.48, 0.0, 1.5),
)


CONFIG_API_CODE = '''"""Stable access API for all Phase 3 renderers."""
CONTROLS = "/project1/mutual_illumination/visual_controls"

def controls():
    result = op(CONTROLS)
    if result is None:
        raise RuntimeError("Missing visual controls: " + CONTROLS)
    return result

def value(name, default=None):
    parameter = getattr(controls().par, name, None)
    return default if parameter is None else parameter.eval()

def rgb(name):
    owner = controls()
    return tuple(float(getattr(owner.par, name + suffix).eval())
                 for suffix in ("r", "g", "b"))
'''


REFRESH_CODE = '''"""Refresh current visual renderers when a control changes."""
NODE_RENDERER = "/project1/mutual_illumination/render_nodes/phase1a_node_renderer"
CONNECTION_RENDERER = "/project1/mutual_illumination/render_connections/phase2_connection_renderer"
FINAL_OUT = "/project1/mutual_illumination/output/FINAL_OUT"

def _refresh():
    for path in (NODE_RENDERER, CONNECTION_RENDERER, FINAL_OUT):
        operator = op(path)
        if operator is not None:
            operator.cook(force=True)

def onValueChange(channel, sampleIndex, val, prev):
    _refresh()
    return

def onOffToOn(channel, sampleIndex, val, prev): return
def whileOn(channel, sampleIndex, val, prev): return
def onOnToOff(channel, sampleIndex, val, prev): return
def whileOff(channel, sampleIndex, val, prev): return
'''


NODE_RENDER_CODE = '''"""Render node_data using Phase 3A visual controls."""
import numpy

TABLE = "/project1/mutual_illumination/data/node_data"
DIAG = "/project1/mutual_illumination/data/phase1b_diagnostics"
MANAGER = "/project1/mutual_illumination/data/node_system"
CONTROLS = "/project1/mutual_illumination/visual_controls"
WIDTH, HEIGHT = 1280, 720

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _diag(name, value):
    dat = op(DIAG)
    if dat:
        for row in range(1, dat.numRows):
            if dat[row, 0].val == name:
                dat[row, 1] = "" if value is None else str(value); break

def _nodes():
    result, table = [], op(TABLE)
    if table:
        for row in range(1, table.numRows):
            try:
                result.append((int(table[row,"id"].val),
                               float(table[row,"x"].val),
                               float(table[row,"y"].val)))
            except (TypeError, ValueError, AttributeError): pass
    return result

def _visuals():
    control = op(CONTROLS)
    if control is None: raise RuntimeError("Missing visual_controls")
    radius = max(0.1, float(control.par.Nodesize.eval()))
    softness = max(0.01, float(control.par.Edgesoftness.eval()))
    color = numpy.array((control.par.Nodecolorr.eval(),
                         control.par.Nodecolorg.eval(),
                         control.par.Nodecolorb.eval()), dtype=numpy.float32)
    return radius, softness, color

def onCook(scriptOp):
    radius, softness, color = _visuals()
    image = numpy.zeros((HEIGHT, WIDTH, 4), dtype=numpy.float32); image[:,:,3] = 1
    nodes = _nodes()
    for node_id, x, y in nodes:
        margin = int(radius + softness + 2)
        x0=max(0,int(x)-margin); x1=min(WIDTH,int(x)+margin+1)
        y0=max(0,int(y)-margin); y1=min(HEIGHT,int(y)+margin+1)
        if x0 >= x1 or y0 >= y1: continue
        yy, xx = numpy.ogrid[y0:y1, x0:x1]
        distance = numpy.sqrt((xx-x)**2 + (yy-y)**2)
        coverage = numpy.clip((radius+softness-distance)/softness,0,1).astype(numpy.float32)
        numpy.maximum(image[y0:y1,x0:x1,:3], coverage[:,:,None]*color,
                      out=image[y0:y1,x0:x1,:3])
    scriptOp.copyNumpyArray(image); _diag("last_render_frame", absTime.frame)
    manager=op(MANAGER)
    drag_id=None if manager is None else manager.fetch("phase1b_dragging_id",None,search=False)
    rendered=next((node for node in nodes if node[0]==drag_id),None)
    _diag("last_render_node_id",None if rendered is None else rendered[0])
    _diag("last_render_node_x",None if rendered is None else rendered[1])
    _diag("last_render_node_y",None if rendered is None else rendered[2])

def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''


CONNECTION_RENDER_CODE = '''"""Render edge_data using Phase 3A visual controls."""
import numpy

EDGE_DATA = "/project1/mutual_illumination/graph/edge_data"
CONTROLS = "/project1/mutual_illumination/visual_controls"
WIDTH, HEIGHT, SOFTNESS = 1280, 720, 1.0

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _edges():
    result=[]; table=op(EDGE_DATA)
    if table:
        for row in range(1,table.numRows):
            try:
                result.append((float(table[row,"ax"].val),float(table[row,"ay"].val),
                               float(table[row,"bx"].val),float(table[row,"by"].val),
                               int(table[row,"trunk"].val)))
            except (TypeError,ValueError,AttributeError): pass
    return result

def _visuals():
    control=op(CONTROLS)
    if control is None: raise RuntimeError("Missing visual_controls")
    width=max(0.05,float(control.par.Lineweight.eval()))
    brightness=max(0.0,float(control.par.Linebrightness.eval()))
    branch=max(0.0,float(control.par.Branchbrightness.eval()))
    color=numpy.array((control.par.Linecolorr.eval(),control.par.Linecolorg.eval(),
                       control.par.Linecolorb.eval()),dtype=numpy.float32)
    return width,color*brightness,branch

def onCook(scriptOp):
    line_width,trunk_color,branch_brightness=_visuals()
    image=numpy.zeros((HEIGHT,WIDTH,4),dtype=numpy.float32); image[:,:,3]=1.
    radius=line_width*0.5+SOFTNESS
    for ax,ay,bx,by,trunk in _edges():
        x0=max(0,int(min(ax,bx)-radius-1)); x1=min(WIDTH,int(max(ax,bx)+radius+2))
        y0=max(0,int(min(ay,by)-radius-1)); y1=min(HEIGHT,int(max(ay,by)+radius+2))
        if x0>=x1 or y0>=y1: continue
        yy,xx=numpy.ogrid[y0:y1,x0:x1]; dx,dy=bx-ax,by-ay; length2=dx*dx+dy*dy
        if length2<=1e-9: continue
        t=numpy.clip(((xx-ax)*dx+(yy-ay)*dy)/length2,0.,1.)
        distance=numpy.sqrt((xx-(ax+t*dx))**2+(yy-(ay+t*dy))**2)
        coverage=numpy.clip((radius-distance)/SOFTNESS,0.,1.).astype(numpy.float32)
        color=trunk_color if trunk else trunk_color*branch_brightness
        numpy.maximum(image[y0:y1,x0:x1,:3],coverage[:,:,None]*color,
                      out=image[y0:y1,x0:x1,:3])
    scriptOp.copyNumpyArray(image)

def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''


def _require(path):
    operator = op(path)
    if operator is None: raise RuntimeError("Missing operator: " + path)
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
    for menu_name, label in zip(parameter.menuNames, parameter.menuLabels):
        if wanted.lower() in (menu_name + " " + label).lower():
            parameter.val = menu_name; return
    raise RuntimeError("Menu choice {} unavailable on {}".format(wanted, operator.path))


def _owned(parent, name, kind, initialize=True):
    existing = parent.op(name)
    if existing is not None:
        if existing.fetch(P3_KEY, None, search=False) != P3_VALUE:
            raise RuntimeError("Refusing unowned operator: " + existing.path)
        return existing
    created = parent.create(kind, name) if initialize else parent.create(kind, name, initialize=False)
    created.store(P3_KEY, P3_VALUE)
    return created


def _page(component, name):
    for page in component.customPages:
        if page.name == name: return page
    return component.appendCustomPage(name)


def _configure_new(parameters, default, minimum, maximum):
    values = default if isinstance(default, tuple) else (default,)
    for index, parameter in enumerate(parameters):
        value = values[index] if index < len(values) else values[0]
        parameter.default = value; parameter.val = value
        parameter.min = minimum; parameter.max = maximum
        parameter.normMin = minimum; parameter.normMax = maximum
        parameter.clampMin = True; parameter.clampMax = True


def _ensure_parameter(component, spec):
    kind, page_name, name, label, default, minimum, maximum = spec
    page = _page(component, page_name)
    if kind == "rgb":
        parts = [getattr(component.par, name + suffix, None) for suffix in ("r","g","b")]
        if all(part is not None for part in parts): return False
        if any(part is not None for part in parts):
            raise RuntimeError("Incomplete existing RGB parameter: " + name)
        group = page.appendRGB(name, label=label, replace=False)
    else:
        existing = getattr(component.par, name, None)
        if existing is not None: return False
        method = {"float": page.appendFloat, "int": page.appendInt,
                  "toggle": page.appendToggle}[kind]
        group = method(name, label=label, replace=False)
    _configure_new(list(group), default, minimum, maximum)
    return True


def _connect(target, source):
    if list(target.inputs) == [source]: return
    target.inputConnectors[0].connect(source)
    if list(target.inputs) != [source]:
        raise RuntimeError("Failed to connect {} -> {}".format(source.path, target.path))


def _path_from_par(parameter):
    value = parameter.eval()
    return value.path if hasattr(value, "path") else str(value)


def _validate_v02_and_logic():
    if project.name != EXPECTED_PROJECT:
        raise RuntimeError(
            "Phase 3A may only run in {}; current project is {}".format(
                EXPECTED_PROJECT, project.name
            )
        )
    node_callbacks = _require(NODE_CALLBACKS)
    node_renderer = _require(NODE_RENDERER)
    connection_callbacks = _require(CONNECTION_CALLBACKS)
    connection_renderer = _require(CONNECTION_RENDERER)
    composite = _require(COMPOSITE)
    graph_execute = _require(GRAPH_EXECUTE)
    if node_callbacks.fetch(B1_KEY,None,search=False) != B1_VALUE:
        raise RuntimeError("Phase 1B renderer ownership is missing")
    for operator in (connection_callbacks, connection_renderer, composite, graph_execute):
        if operator.fetch(P2_KEY,None,search=False) != P2_VALUE:
            raise RuntimeError("Phase 2 ownership is missing on " + operator.path)
    if list(composite.inputs) != [_require(PHASE1A_OUT)]:
        raise RuntimeError("Protected Composite wire is not phase1a_out")
    if _path_from_par(composite.par.top) != connection_renderer.path:
        raise RuntimeError("Protected Composite TOP parameter is incorrect")
    if str(composite.par.operand.eval()).lower() != "add":
        raise RuntimeError("Protected Composite operation is not Add")
    composite.cook(force=True)
    if (int(composite.width),int(composite.height)) != (WIDTH,HEIGHT):
        raise RuntimeError("Protected Composite is not 1280x720")
    if list(composite.errors()):
        raise RuntimeError("Protected Composite has errors: " + repr(composite.errors()))
    return node_callbacks,node_renderer,connection_callbacks,connection_renderer


def build_phase3a():
    node_callbacks,node_renderer,connection_callbacks,connection_renderer = _validate_v02_and_logic()
    root = _require(ROOT)
    controls = _owned(root, "visual_controls", baseCOMP)
    controls.nodeX, controls.nodeY = 1320, -180
    controls.color = (0.28, 0.22, 0.38)
    controls.comment = "Developer-only unified visual controls; not part of FINAL_OUT"
    controls.viewer = True

    created_count = 0
    for spec in PARAMETERS:
        if _ensure_parameter(controls, spec): created_count += 1

    api = _owned(controls, "visual_config_api", textDAT)
    params = _owned(controls, "visual_params", parameterCHOP)
    params_out = _owned(controls, "visual_params_out", nullCHOP)
    execute = _owned(controls, "visual_config_execute", chopexecuteDAT, initialize=False)
    panel = _owned(controls, "visual_control_panel", parameterCOMP)

    api.text = CONFIG_API_CODE; execute.text = REFRESH_CODE
    api.nodeX,api.nodeY=0,120; params.nodeX,params.nodeY=200,120
    params_out.nodeX,params_out.nodeY=400,120; execute.nodeX,execute.nodeY=600,120
    panel.nodeX,panel.nodeY=0,-80; panel.par.w=620; panel.par.h=760

    _par(execute,"active",False)
    _par(params,"ops",controls.path)
    _menu(params,"fetch","parameters")
    _par(params,"pargroups","*"); _par(params,"parameter","*")
    _par(params,"custom",True); _par(params,"builtin",False)
    _menu(params,"nameformat","parameter")
    _connect(params_out,params)

    _par(execute,"chop",params_out.path); _par(execute,"channel","*")
    for name,value in (("offtoon",False),("whileon",False),("ontooff",False),
                       ("whileoff",False),("valuechange",True)):
        _par(execute,name,value)

    _par(panel,"op",controls.path)
    for name,value in (("header",False),("pagenames",True),("labels",True),
                       ("separators",True),("allowexpand",False),
                       ("builtin",False),("custom",True)):
        _par(panel,name,value)
    panel.viewer=True; panel.activeViewer=True

    node_callbacks.text = NODE_RENDER_CODE
    connection_callbacks.text = CONNECTION_RENDER_CODE
    node_callbacks.store(P3_KEY,P3_VALUE); node_renderer.store(P3_KEY,P3_VALUE)
    connection_callbacks.store(P3_KEY,P3_VALUE); connection_renderer.store(P3_KEY,P3_VALUE)

    params.cook(force=True); params_out.cook(force=True)
    if int(params_out.numChans) < 7:
        raise RuntimeError("visual_params_out did not expose the active controls")
    node_renderer.cook(force=True); connection_renderer.cook(force=True)
    _require(FINAL_OUT).cook(force=True)
    for operator in (node_renderer,connection_renderer,_require(FINAL_OUT)):
        if list(operator.errors()):
            raise RuntimeError("Renderer error on {}: {}".format(operator.path,operator.errors()))
    if (int(_require(FINAL_OUT).width),int(_require(FINAL_OUT).height)) != (WIDTH,HEIGHT):
        raise RuntimeError("FINAL_OUT resolution changed during Phase 3A")

    _par(execute,"active",True)
    print("[Phase 3A] Unified visual controls installed; TOE was NOT saved.")
    print("[Phase 3A] Project:", project.name)
    print("[Phase 3A] Existing values preserved; new parameters added:", created_count)
    print("[Phase 3A] Open:", panel.path)
    print("[Phase 3A] Active now: Node and Connections pages only.")
    return controls


PHASE3A_RESULT = build_phase3a()
