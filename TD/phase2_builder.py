"""Incrementally install Phase 2 dynamic MST connections. Does not save TOE."""

ROOT = "/project1/mutual_illumination"
NODE_DATA = ROOT + "/data/node_data"
GRAPH = ROOT + "/graph"
EDGE_DATA = GRAPH + "/edge_data"
EDGE_DATA_OUT = GRAPH + "/edge_data_out"
GRAPH_SYSTEM = GRAPH + "/graph_system"
GRAPH_EXEC = GRAPH + "/phase2_graph_execute"
RENDER_MODULE = ROOT + "/render_connections"
CALLBACKS = RENDER_MODULE + "/phase2_connection_callbacks"
RENDERER = RENDER_MODULE + "/phase2_connection_renderer"
OUTPUT = ROOT + "/output"
NODES_OUT = OUTPUT + "/phase1a_out"
COMPOSITE = OUTPUT + "/phase2_composite"
PHASE2_OUT = OUTPUT + "/phase2_out"
FINAL_OUT = OUTPUT + "/FINAL_OUT"

A1_KEY, A1_VALUE = "mutual_illumination_phase1a", "dynamic_nodes_v01"
B1_KEY, B1_VALUE = "mutual_illumination_phase1b", "mouse_drag_v03_diagnostics"
P2_KEY, P2_VALUE = "mutual_illumination_phase2", "dynamic_mst_v01"
BOOTSTRAP_KEY, BOOTSTRAP_VALUE = "mutual_illumination_builder", "bootstrap_v02"
WIDTH, HEIGHT = 1280, 720

GRAPH_SYSTEM_CODE = '''"""Python prototype connection algorithm adapted to DAT rows."""
import math

NODE_DATA = "/project1/mutual_illumination/data/node_data"
EDGE_DATA = "/project1/mutual_illumination/graph/edge_data"
GRAPH_SYSTEM = "/project1/mutual_illumination/graph/graph_system"
RENDERER = "/project1/mutual_illumination/render_connections/phase2_connection_renderer"
SIGNATURE_KEY = "phase2_node_signature"
MAX_DEGREE = 3
CONNECTION_DISTANCE = 390.0
CONNECTION_DENSITY = 0.24

def _nodes():
    result, table = [], op(NODE_DATA)
    if table is None: return result
    for row in range(1, table.numRows):
        try:
            result.append((int(table[row,"id"].val),
                           float(table[row,"x"].val),
                           float(table[row,"y"].val)))
        except (TypeError, ValueError, AttributeError): pass
    return result

def _affinity(a_id, b_id):
    low, high = sorted((a_id, b_id))
    return (((low * 73856093) ^ (high * 19349663)) & 0xFFFF) / 65535.0

def _orientation(a, b, c):
    return (b[1]-a[1])*(c[2]-a[2]) - (b[2]-a[2])*(c[1]-a[1])

def _crosses(candidate, selected):
    a, b = candidate[0], candidate[1]
    for edge in selected:
        c, d = edge[0], edge[1]
        if len({a[0],b[0],c[0],d[0]}) < 4: continue
        if (_orientation(a,b,c)*_orientation(a,b,d) < 0 and
                _orientation(c,d,a)*_orientation(c,d,b) < 0):
            return True
    return False

def _choose(nodes):
    if len(nodes) < 2: return []
    edges=[]
    for index, first in enumerate(nodes):
        for second in nodes[index+1:]:
            distance=math.hypot(second[1]-first[1], second[2]-first[2])
            edges.append((first,second,distance,True))
    edges.sort(key=lambda edge: edge[2])
    parent={node[0]:node[0] for node in nodes}
    degree={node[0]:0 for node in nodes}
    def find(node_id):
        while parent[node_id] != node_id:
            parent[node_id]=parent[parent[node_id]]; node_id=parent[node_id]
        return node_id
    trunk=[]
    for edge in edges:
        a_id,b_id=edge[0][0],edge[1][0]
        a_root,b_root=find(a_id),find(b_id)
        if a_root==b_root or degree[a_id]>=MAX_DEGREE or degree[b_id]>=MAX_DEGREE: continue
        trunk.append(edge); parent[a_root]=b_root
        degree[a_id]+=1; degree[b_id]+=1
        if len(trunk)==len(nodes)-1: break
    selected=list(trunk)
    trunk_pairs={frozenset((edge[0][0],edge[1][0])) for edge in trunk}
    for edge in edges:
        a_id,b_id=edge[0][0],edge[1][0]
        if frozenset((a_id,b_id)) in trunk_pairs: continue
        if edge[2] > CONNECTION_DISTANCE*0.72: continue
        if degree[a_id]>=MAX_DEGREE or degree[b_id]>=MAX_DEGREE: continue
        if _affinity(a_id,b_id) > CONNECTION_DENSITY: continue
        branch=(edge[0],edge[1],edge[2],False)
        if _crosses(branch,selected): continue
        selected.append(branch); degree[a_id]+=1; degree[b_id]+=1
    return selected

def update_graph(force=False):
    owner=op(GRAPH_SYSTEM); nodes=_nodes()
    signature=tuple((node[0],round(node[1],3),round(node[2],3)) for node in nodes)
    if not force and owner.fetch(SIGNATURE_KEY,None,search=False)==signature: return False
    selected=_choose(nodes); table=op(EDGE_DATA)
    table.clear(); table.appendRow(("edge_id","a_id","b_id","ax","ay","bx","by","distance","trunk"))
    for edge_id,edge in enumerate(selected,1):
        a,b,distance,trunk=edge
        table.appendRow((edge_id,a[0],b[0],round(a[1],3),round(a[2],3),
                         round(b[1],3),round(b[2],3),round(distance,3),int(trunk)))
    owner.store(SIGNATURE_KEY,signature)
    renderer=op(RENDERER)
    if renderer: renderer.cook(force=True)
    return True
'''

GRAPH_EXECUTE_CODE = '''GRAPH_SYSTEM = "/project1/mutual_illumination/graph/graph_system"
def onFrameStart(frame):
    system=op(GRAPH_SYSTEM)
    if system: system.module.update_graph()
def onStart(): return
def onCreate(): return
def onExit(): return
def onFrameEnd(frame): return
def onPlayStateChange(state): return
def onDeviceChange(): return
'''

RENDER_CODE = '''import numpy
EDGE_DATA = "/project1/mutual_illumination/graph/edge_data"
WIDTH,HEIGHT=1280,720
LINE_WIDTH,SOFTNESS=1.25,1.0
TRUNK_RGB=numpy.array((231.,159.,83.),dtype=numpy.float32)/255.
BRANCH_RGB=TRUNK_RGB*0.72
def onSetupParameters(scriptOp): return
def onPulse(par): return
def _edges():
    result=[]; table=op(EDGE_DATA)
    if table:
        for row in range(1,table.numRows):
            try: result.append((float(table[row,"ax"].val),float(table[row,"ay"].val),float(table[row,"bx"].val),float(table[row,"by"].val),int(table[row,"trunk"].val)))
            except (TypeError,ValueError,AttributeError): pass
    return result
def onCook(scriptOp):
    image=numpy.zeros((HEIGHT,WIDTH,4),dtype=numpy.float32); image[:,:,3]=1.
    radius=LINE_WIDTH*0.5+SOFTNESS
    for ax,ay,bx,by,trunk in _edges():
        x0=max(0,int(min(ax,bx)-radius-1)); x1=min(WIDTH,int(max(ax,bx)+radius+2))
        y0=max(0,int(min(ay,by)-radius-1)); y1=min(HEIGHT,int(max(ay,by)+radius+2))
        if x0>=x1 or y0>=y1: continue
        yy,xx=numpy.ogrid[y0:y1,x0:x1]; dx,dy=bx-ax,by-ay; length2=dx*dx+dy*dy
        if length2<=1e-9: continue
        t=numpy.clip(((xx-ax)*dx+(yy-ay)*dy)/length2,0.,1.)
        distance=numpy.sqrt((xx-(ax+t*dx))**2+(yy-(ay+t*dy))**2)
        coverage=numpy.clip((radius-distance)/SOFTNESS,0.,1.).astype(numpy.float32)
        color=TRUNK_RGB if trunk else BRANCH_RGB
        numpy.maximum(image[y0:y1,x0:x1,:3],coverage[:,:,None]*color,out=image[y0:y1,x0:x1,:3])
    scriptOp.copyNumpyArray(image)
def onGetCookLevel(scriptOp): return CookLevel.AUTOMATIC
'''

def _require(path):
    item=op(path)
    if item is None: raise RuntimeError("Missing operator: "+path)
    return item

def _par(item,name,value):
    parameter=getattr(item.par,name,None)
    if parameter is None: raise RuntimeError("Missing parameter {} on {}".format(name,item.path))
    parameter.val=value

def _menu(item,name,wanted):
    parameter=getattr(item.par,name,None)
    if parameter is None: raise RuntimeError("Missing menu {} on {}".format(name,item.path))
    for menu_name,label in zip(parameter.menuNames,parameter.menuLabels):
        if wanted.lower() in (menu_name+" "+label).lower(): parameter.val=menu_name; return
    raise RuntimeError("Menu choice {} unavailable on {}".format(wanted,item.path))

def _owned(parent,name,kind,initialize=True):
    item=parent.op(name)
    if item:
        if item.fetch(P2_KEY,None,search=False)!=P2_VALUE: raise RuntimeError("Refusing unowned operator: "+item.path)
        return item
    item=parent.create(kind,name) if initialize else parent.create(kind,name,initialize=False)
    item.store(P2_KEY,P2_VALUE); return item

def _bootstrap_root_is_valid():
    root=op(ROOT)
    return root is not None and root.fetch(
        BOOTSTRAP_KEY,None,search=False
    )==BOOTSTRAP_VALUE

def _adopt_bootstrap_edge_ops(graph):
    """Adopt only the two canonical DATs made by bootstrap_v02."""
    edge_data=graph.op("edge_data")
    edge_out=graph.op("edge_data_out")
    if edge_data is None or edge_out is None:
        raise RuntimeError("Bootstrap graph/edge_data or edge_data_out is missing")
    if edge_data.opType!="tableDAT":
        raise RuntimeError("Bootstrap graph/edge_data must be a Table DAT")
    if edge_out.opType!="nullDAT":
        raise RuntimeError("Bootstrap graph/edge_data_out must be a Null DAT")

    data_owner=edge_data.fetch(P2_KEY,None,search=False)
    out_owner=edge_out.fetch(P2_KEY,None,search=False)
    for owner in (data_owner,out_owner):
        if owner not in (None,P2_VALUE):
            raise RuntimeError("Canonical edge DATs carry an unexpected owner marker")
    headers=[cell.val for cell in edge_data.row(0)] if edge_data.numRows else []
    allowed=(
        ["a_id","b_id","distance","trunk"],
        ["edge_id","a_id","b_id","ax","ay","bx","by","distance","trunk"],
    )
    if headers not in allowed:
        raise RuntimeError(
            "Canonical edge_data has an unrecognized schema: "+repr(headers)
        )
    if data_owner is None or out_owner is None:
        if not _bootstrap_root_is_valid():
            raise RuntimeError(
                "Cannot adopt canonical edge DATs: bootstrap_v02 root marker is missing"
            )
        edge_data.store(P2_KEY,P2_VALUE)
        edge_out.store(P2_KEY,P2_VALUE)
    return edge_data,edge_out

def _connect(target,index,source):
    if index>=len(target.inputConnectors): raise RuntimeError("No input {} on {}".format(index,target.path))
    if len(target.inputs)>index and target.inputs[index]==source: return
    target.inputConnectors[index].connect(source)

def _set_composite_wire(composite,source):
    """Keep one local wire; the connection texture comes from par.top."""
    if not source.opType.endswith("TOP") or not source.outputConnectors:
        raise RuntimeError("Composite wire source is not a valid TOP: "+source.path)
    if source.parent()!=composite.parent():
        raise RuntimeError("Composite wire source must share its network: "+source.path)
    while composite.inputs:
        composite.inputConnectors[0].disconnect()
    source.outputConnectors[0].connect(composite)
    actual=list(composite.inputs)
    if actual!=[source]:
        raise RuntimeError(
            "Composite wire verification failed; expected {}, got {}".format(
                source.path,
                [source.path for source in actual],
            )
        )

def _validate_composite(composite,wire_source,top_source):
    actual=list(composite.inputs)
    if actual!=[wire_source]:
        raise RuntimeError(
            "Composite wire mismatch; expected {}, got {}".format(
                wire_source.path,
                [source.path for source in actual],
            )
        )
    selected=composite.par.top.eval()
    selected_path=selected.path if hasattr(selected,"path") else str(selected)
    if selected_path!=top_source.path:
        raise RuntimeError(
            "Composite TOP parameter mismatch; expected {}, got {}".format(
                top_source.path,selected_path
            )
        )
    composite.cook(force=True)
    errors=list(composite.errors())
    if errors:
        raise RuntimeError(
            "Composite TOP reports errors: "+" | ".join(str(error) for error in errors)
        )

def _validate_single_input(target,source):
    actual=list(target.inputs)
    if actual!=[source]:
        raise RuntimeError(
            "Output chain mismatch on {}; expected {}, got {}".format(
                target.path,source.path,[item.path for item in actual]
            )
        )
    target.cook(force=True)
    errors=list(target.errors())
    if errors:
        raise RuntimeError(
            "{} reports errors: {}".format(
                target.path," | ".join(str(error) for error in errors)
            )
        )

def _validate_resolution(target):
    target.cook(force=True)
    width,height=int(target.width),int(target.height)
    if (width,height)!=(WIDTH,HEIGHT):
        raise RuntimeError(
            "{} resolution is {}x{}, expected {}x{}".format(
                target.path,width,height,WIDTH,HEIGHT
            )
        )
    aspect=float(width)/float(height)
    if abs(aspect-(16.0/9.0))>0.0001:
        raise RuntimeError("{} aspect is {}".format(target.path,aspect))

def build_phase2():
    nodes=_require(NODE_DATA); graph=_require(GRAPH); render_module=_require(RENDER_MODULE)
    output=_require(OUTPUT); nodes_out=_require(NODES_OUT); final=_require(FINAL_OUT)
    manager=_require(ROOT+"/data/node_system")
    if manager.fetch(B1_KEY,None,search=False)!=B1_VALUE:
        raise RuntimeError("Phase 1B v03 must be installed before Phase 2")
    edge_data,edge_out=_adopt_bootstrap_edge_ops(graph)
    graph_system=_owned(graph,"graph_system",textDAT)
    graph_exec=_owned(graph,"phase2_graph_execute",executeDAT,False)
    callbacks=_owned(render_module,"phase2_connection_callbacks",textDAT)
    renderer=_owned(render_module,"phase2_connection_renderer",scriptTOP)
    composite=_owned(output,"phase2_composite",compositeTOP)
    phase_out=_owned(output,"phase2_out",nullTOP)
    _par(graph_exec,"active",False)
    edge_data.clear(); edge_data.appendRow(("edge_id","a_id","b_id","ax","ay","bx","by","distance","trunk"))
    _connect(edge_out,0,edge_data)
    graph_system.text=GRAPH_SYSTEM_CODE; graph_exec.text=GRAPH_EXECUTE_CODE; callbacks.text=RENDER_CODE
    graph_system.nodeX,graph_system.nodeY=0,80; edge_data.nodeX,edge_data.nodeY=220,80; graph_exec.nodeX,graph_exec.nodeY=440,80
    callbacks.nodeX,callbacks.nodeY=0,80; renderer.nodeX,renderer.nodeY=220,80
    composite.nodeX,composite.nodeY=390,-80; phase_out.nodeX,phase_out.nodeY=580,-80
    _par(renderer,"callbacks",callbacks.path); _menu(renderer,"outputresolution","custom")
    _par(renderer,"resolutionw",WIDTH); _par(renderer,"resolutionh",HEIGHT)
    _menu(composite,"operand","add")
    _par(composite,"top",renderer.path)
    _menu(composite,"outputresolution","custom")
    _par(composite,"resolutionw",WIDTH); _par(composite,"resolutionh",HEIGHT)
    _menu(composite,"outputaspect","resolution")
    _set_composite_wire(composite,nodes_out)
    _connect(phase_out,0,composite)
    _par(graph_exec,"framestart",True)
    graph_system.store("phase2_node_signature",None)
    graph_system.module.update_graph(force=True)
    _validate_composite(composite,nodes_out,renderer)
    _validate_resolution(composite)
    _validate_single_input(phase_out,composite)
    _validate_resolution(phase_out)
    _connect(final,0,phase_out)
    _validate_single_input(final,phase_out)
    _validate_resolution(final)
    _par(graph_exec,"active",True)
    if not bool(graph_exec.par.active.eval()):
        raise RuntimeError("phase2_graph_execute did not become active")
    print("[Phase 2] Dynamic MST installed; TOE was NOT saved.")
    print("[Phase 2] Inspect graph/edge_data; keep the timeline playing.")
    print("[Phase 2] Composite wire verified:", nodes_out.path)
    print("[Phase 2] Composite TOP parameter verified:", renderer.path)
    print("[Phase 2] Output verified: 1280x720, graph execute Active=True")
    return phase_out

PHASE2_RESULT=build_phase2()
