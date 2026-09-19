"""Incremental Phase 1B v03 drag diagnostics. Does not save the TOE."""

ROOT = "/project1/mutual_illumination"
TABLE = ROOT + "/data/node_data"
DIAG = ROOT + "/data/phase1b_diagnostics"
MANAGER = ROOT + "/data/node_system"
PANEL = ROOT + "/input/node_input_panel"
PANEL_EXEC = ROOT + "/input/phase1a_panel_execute"
FRAME_EXEC = ROOT + "/input/phase1b_frame_execute"
CALLBACKS = ROOT + "/render_nodes/phase1a_node_callbacks"
RENDERER = ROOT + "/render_nodes/phase1a_node_renderer"
A1_KEY, A1_VALUE = "mutual_illumination_phase1a", "dynamic_nodes_v01"
B1_KEY, B1_VALUE = "mutual_illumination_phase1b", "mouse_drag_v03_diagnostics"

DIAG_ROWS = (
    ("status", "waiting for frame"), ("lselect", "0"),
    ("mouse_u", "0"), ("mouse_v", "0"), ("dragging_id", ""),
    ("node_x", ""), ("node_y", ""), ("render_pending", "0"),
    ("last_frame_tick", ""), ("last_node_update_frame", ""),
    ("panel_event_count", "0"), ("last_panel_event", ""),
    ("last_panel_event_frame", ""), ("last_render_frame", ""),
    ("last_render_node_id", ""), ("last_render_node_x", ""),
    ("last_render_node_y", ""), ("last_error", ""),
)

NODE_SYSTEM_CODE = '''import math
TABLE = "/project1/mutual_illumination/data/node_data"
DIAG = "/project1/mutual_illumination/data/phase1b_diagnostics"
MANAGER = "/project1/mutual_illumination/data/node_system"
RENDERER = "/project1/mutual_illumination/render_nodes/phase1a_node_renderer"
WIDTH, HEIGHT, DRAG_RADIUS = 1280, 720, 34.0
DRAG_ID, PREV_SELECT = "phase1b_dragging_id", "phase1b_previous_lselect"
PENDING, EVENT_COUNT = "phase1b_render_pending", "phase1b_panel_event_count"

def _table():
    return op(TABLE)

def _manager():
    return op(MANAGER)

def _diag(name, value):
    dat = op(DIAG)
    if dat:
        for row in range(1, dat.numRows):
            if dat[row, 0].val == name:
                dat[row, 1] = "" if value is None else str(value)
                break

def _drag_id():
    return _manager().fetch(DRAG_ID, None, search=False)

def _set_drag_id(value):
    _manager().store(DRAG_ID, value)
    _diag("dragging_id", value)

def _pending(value):
    value = bool(value)
    _manager().store(PENDING, value)
    _diag("render_pending", int(value))

def _xy(u, v):
    u, v = min(max(float(u), 0), 1), min(max(float(v), 0), 1)
    return round(u * (WIDTH - 1), 3), round(v * (HEIGHT - 1), 3)

def _row(table, node_id):
    for row in range(1, table.numRows):
        try:
            if int(table[row, "id"].val) == int(node_id): return row
        except (TypeError, ValueError, AttributeError): pass
    return None

def _drag_flags(table, selected=None):
    for row in range(1, table.numRows):
        table[row, "dragging"] = "1" if row == selected else "0"

def _selected_diag():
    node_id, table = _drag_id(), _table()
    _diag("dragging_id", node_id)
    row = None if node_id is None else _row(table, node_id)
    _diag("node_x", None if row is None else table[row, "x"].val)
    _diag("node_y", None if row is None else table[row, "y"].val)

def _request_render():
    _pending(True)

def _flush_render():
    if not _manager().fetch(PENDING, False, search=False): return
    try:
        renderer = op(RENDERER)
        if renderer is None: raise RuntimeError("renderer missing")
        renderer.cook(force=True)
        _diag("last_error", "")
    except Exception as error:
        _diag("last_error", "render: " + repr(error))
    finally:
        _pending(False)

def add_node(u, v):
    table, ids = _table(), []
    for row in range(1, table.numRows):
        try: ids.append(int(table[row, "id"].val))
        except (TypeError, ValueError, AttributeError): pass
    node_id, (x, y) = max(ids, default=0) + 1, _xy(u, v)
    table.appendRow((node_id, x, y, 0))
    _request_render()
    print("[Phase 1B] Added node", node_id)
    return node_id

def press(u, v):
    table, (x, y) = _table(), _xy(u, v)
    best_row, best_id, best_distance = None, None, DRAG_RADIUS
    for row in range(table.numRows - 1, 0, -1):
        try:
            node_id = int(table[row, "id"].val)
            distance = math.hypot(float(table[row, "x"].val)-x,
                                  float(table[row, "y"].val)-y)
        except (TypeError, ValueError, AttributeError): continue
        if distance < best_distance:
            best_row, best_id, best_distance = row, node_id, distance
    if best_row is None:
        _set_drag_id(None); _drag_flags(table); return add_node(u, v)
    _set_drag_id(best_id); _drag_flags(table, best_row); _selected_diag()
    print("[Phase 1B] Dragging node", best_id)
    return best_id

def drag_to(u, v, frame):
    node_id, table = _drag_id(), _table()
    if node_id is None: return
    row = _row(table, node_id)
    if row is None: return release_drag()
    x, y = _xy(u, v)
    table[row, "x"], table[row, "y"], table[row, "dragging"] = x, y, 1
    _diag("node_x", x); _diag("node_y", y)
    _diag("last_node_update_frame", frame); _request_render()

def release_drag():
    node_id = _drag_id(); _drag_flags(_table()); _set_drag_id(None)
    _selected_diag()
    if node_id is not None: print("[Phase 1B] Released node", node_id)

def record_panel_event(name, frame):
    manager = _manager()
    count = int(manager.fetch(EVENT_COUNT, 0, search=False)) + 1
    manager.store(EVENT_COUNT, count)
    _diag("panel_event_count", count); _diag("last_panel_event", name)
    _diag("last_panel_event_frame", frame)

def frame_tick(lselect, u, v, frame):
    manager, selected = _manager(), int(float(lselect) > 0)
    previous = int(manager.fetch(PREV_SELECT, 0, search=False))
    _diag("lselect", selected); _diag("mouse_u", round(float(u), 6))
    _diag("mouse_v", round(float(v), 6)); _diag("last_frame_tick", frame)
    if selected and not previous: press(u, v)
    if selected and _drag_id() is not None: drag_to(u, v, frame)
    elif not selected and previous: release_drag()
    manager.store(PREV_SELECT, selected)
    _selected_diag(); _flush_render()
    _diag("status", "dragging" if _drag_id() is not None else "idle")

def clear_nodes():
    manager, table = _manager(), _table()
    _set_drag_id(None); manager.store(PREV_SELECT, 0)
    table.clear(); table.appendRow(("id", "x", "y", "dragging"))
    _selected_diag(); _request_render(); print("[Phase 1B] Cleared all nodes")
'''

PANEL_EXECUTE_CODE = '''PANEL = "/project1/mutual_illumination/input/node_input_panel"
MANAGER = "/project1/mutual_illumination/data/node_system"
def onValueChange(panelValue):
    manager = op(MANAGER)
    if manager: manager.module.record_panel_event(panelValue.name, absTime.frame)
def onOffToOn(panelValue): return
def whileOn(panelValue): return
def onOnToOff(panelValue): return
def whileOff(panelValue): return
'''

FRAME_EXECUTE_CODE = '''PANEL = "/project1/mutual_illumination/input/node_input_panel"
MANAGER = "/project1/mutual_illumination/data/node_system"
def onFrameStart(frame):
    panel, manager = op(PANEL), op(MANAGER)
    if panel and manager:
        manager.module.frame_tick(panel.panel.lselect.val, panel.panel.u.val,
                                  panel.panel.v.val, absTime.frame)
def onStart(): return
def onCreate(): return
def onExit(): return
def onFrameEnd(frame): return
def onPlayStateChange(state): return
def onDeviceChange(): return
'''

SCRIPT_TOP_CODE = '''import numpy
TABLE = "/project1/mutual_illumination/data/node_data"
DIAG = "/project1/mutual_illumination/data/phase1b_diagnostics"
MANAGER = "/project1/mutual_illumination/data/node_system"
WIDTH, HEIGHT, RADIUS, SOFT = 1280, 720, 13.0, 1.25
RGB = numpy.array((255., 206., 137.), dtype=numpy.float32) / 255.
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
            try: result.append((int(table[row,"id"].val), float(table[row,"x"].val), float(table[row,"y"].val)))
            except (TypeError, ValueError, AttributeError): pass
    return result
def onCook(scriptOp):
    image = numpy.zeros((HEIGHT, WIDTH, 4), dtype=numpy.float32); image[:,:,3] = 1
    nodes = _nodes()
    for node_id, x, y in nodes:
        margin = int(RADIUS + SOFT + 2); x0=max(0,int(x)-margin); x1=min(WIDTH,int(x)+margin+1)
        y0=max(0,int(y)-margin); y1=min(HEIGHT,int(y)+margin+1)
        if x0 >= x1 or y0 >= y1: continue
        yy, xx = numpy.ogrid[y0:y1, x0:x1]
        coverage = numpy.clip((RADIUS+SOFT-numpy.sqrt((xx-x)**2+(yy-y)**2))/SOFT,0,1).astype(numpy.float32)
        numpy.maximum(image[y0:y1,x0:x1,:3], coverage[:,:,None]*RGB, out=image[y0:y1,x0:x1,:3])
    scriptOp.copyNumpyArray(image); _diag("last_render_frame", absTime.frame)
    manager=op(MANAGER); drag_id=None if manager is None else manager.fetch("phase1b_dragging_id",None,search=False)
    rendered=next((node for node in nodes if node[0]==drag_id),None)
    _diag("last_render_node_id",None if rendered is None else rendered[0])
    _diag("last_render_node_x",None if rendered is None else rendered[1])
    _diag("last_render_node_y",None if rendered is None else rendered[2])
def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''

def _require(path):
    item = op(path)
    if item is None: raise RuntimeError("Missing operator: " + path)
    return item

def _par(item, name, value):
    parameter = getattr(item.par, name, None)
    if parameter is None: raise RuntimeError("Missing parameter {} on {}".format(name,item.path))
    parameter.val = value

def _phase1a(item):
    if item.fetch(A1_KEY,None,search=False) != A1_VALUE:
        raise RuntimeError("Refusing unrecognized operator: " + item.path)

def _owned(parent, name, kind, initialize=True):
    item = parent.op(name)
    if item:
        if item.fetch(B1_KEY,None,search=False) != B1_VALUE:
            raise RuntimeError("Refusing unowned operator: " + item.path)
        return item
    item = parent.create(kind,name) if initialize else parent.create(kind,name,initialize=False)
    item.store(B1_KEY,B1_VALUE); return item

def build_phase1b():
    table, manager, panel = _require(TABLE), _require(MANAGER), _require(PANEL)
    panel_exec, callbacks, renderer = _require(PANEL_EXEC), _require(CALLBACKS), _require(RENDERER)
    for item in (manager,panel,panel_exec,callbacks,renderer): _phase1a(item)
    headers=[cell.val for cell in table.row(0)]
    if "dragging" not in headers: table.appendCol(["dragging"]+["0"]*(table.numRows-1))
    else:
        for row in range(1,table.numRows): table[row,"dragging"]="0"
    _par(panel_exec,"active",False)
    diag=_owned(table.parent(),"phase1b_diagnostics",tableDAT)
    frame_exec=_owned(panel.parent(),"phase1b_frame_execute",executeDAT,False)
    diag.clear(); diag.appendRow(("metric","value"))
    for row in DIAG_ROWS: diag.appendRow(row)
    diag.nodeX,diag.nodeY,diag.comment=420,40,"Live Phase 1B diagnostics"
    frame_exec.nodeX,frame_exec.nodeY,frame_exec.comment=480,80,"Frame-polled drag driver"
    manager.text,panel_exec.text=NODE_SYSTEM_CODE,PANEL_EXECUTE_CODE
    frame_exec.text,callbacks.text=FRAME_EXECUTE_CODE,SCRIPT_TOP_CODE
    for key,value in (("phase1b_dragging_id",None),("phase1b_previous_lselect",0),("phase1b_render_pending",False),("phase1b_panel_event_count",0)): manager.store(key,value)
    _par(panel_exec,"panels",panel.path); _par(panel_exec,"panelvalue","lselect u v")
    for name,value in (("offtoon",False),("whileon",False),("ontooff",False),("whileoff",False),("valuechange",True)): _par(panel_exec,name,value)
    _par(frame_exec,"active",False); _par(frame_exec,"framestart",True)
    for item in (manager,panel_exec,callbacks,renderer): item.store(B1_KEY,B1_VALUE)
    renderer.cook(force=True); _par(panel_exec,"active",True); _par(frame_exec,"active",True)
    print("[Phase 1B] v03 diagnostics installed; TOE was NOT saved.")
    print("[Phase 1B] Open data/phase1b_diagnostics and keep timeline playing.")
    return frame_exec

PHASE1B_RESULT = build_phase1b()
