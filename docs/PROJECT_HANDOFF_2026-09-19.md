# Mutual Illumination / Praise Installation — Codex Handoff

更新时间：2026-09-19
当前开发工程：`TD/TD_visual_prototype_v05.toe`

## 项目意图

这是一个互动投影毕业设计。项目希望把 praise / 善意带来的 warmth、reciprocity 和 social connection 可视化：善意从 giver 向外传播，并通过人与人形成的网络回到、滋养 giver。

核心视觉语言：

- 纯黑背景；
- 暖琥珀色与 ivory 发光节点；
- 缓慢、独立相位的呼吸；
- 受 mycelium / mycorrhizal network 启发的有机发光连接；
- 克制的环境微光和互动 Ripple；
- 避免 full mesh、长而无意义的连接、明显 crossing 和强烈游戏特效感。

Python visual prototype 是视觉与行为依据，TouchDesigner 版本应尽量复刻它，而不是重新设计一套无关系统。主要参考目录：

`code/visual_prototype/visual_prototype/`

关键文件包括 `connections.py`、`renderer.py`、`node.py`、`simulation.py`、`interaction.py`、`ripples.py`、`config.py` 和 `app.py`。视觉参考图为 `docs/python_visual_reference.png`。

## 重要约定

- TouchDesigner 版本：2025.33070。
- 当前实际交互坐标：左下角 `(0,0)`，X 向右增加，Y 向上增加。
- `node_data`、鼠标输入和 Script TOP 当前映射已经一致，后续不要再次翻转 Y。
- 输出固定为 1280×720、16:9。
- 节点数量必须 data-driven，不为每个节点或每条边手工创建 operator。
- 未来 mouse input 会替换成 thermal blob input，因此视觉事件应尽量连接节点数据 API，而不是绑定具体鼠标回调。
- 所有阶段采用外部增量 builder，在 TouchDesigner Textport 内执行。
- builder 不自动保存 TOE；由用户在真实 TD 中验收后手动保存。
- 不重新运行 `bootstrap_builder.py`，也不覆盖历史 TOE。

## TOE 版本含义

- `TD_visual_prototype_v01.toe`：稳定 Logic Prototype，包含动态节点、拖动、Reset、MST 和基础连接。
- `TD_visual_prototype_v02.toe`：统一 Visual Controls 与 Node Glow / Breathing 阶段。
- `TD_visual_prototype_v03.toe`：Mycelium Connection Visuals 阶段。
- `TD_visual_prototype_v04.toe`：Connection Grow In / Fade Out，以及 Unified Reset All。
- `TD_visual_prototype_v05.toe`：当前 Ripple & Ambient 开发工程。v01–v04 是历史检查点，不允许修改。

## 已完成并在真实 TouchDesigner 验收的功能

- 鼠标点击空白处动态新增 node；
- 按住已有 node 后全画布拖动；
- 独立 node ID 和 `data/node_data`；
- Unified Reset All；
- 基于 Kruskal / Union-Find 的 degree-limited MST；
- 每个节点最多 3 条逻辑连接；
- 少量局部 branch、距离限制与 crossing 控制；
- `graph/edge_data` 驱动连接渲染；
- Node Glow、分层 core / inner glow / outer halo；
- 基于 node ID 稳定 phase offset 的独立 Breathing；
- Bézier Mycelium 曲线、Layered Filaments、Soft Sheath、Side Branches、Energy Flow；
- 新连接 Grow In、旧连接 Fade Out；
- 持续拖动时基于无序 node ID pair 管理连接过渡；
- Unified Visual Control Panel；
- FINAL_OUT 1280×720；
- Reset All 会立即清空节点、边、拖动状态和连接过渡状态，不重置视觉参数。

## 当前 TouchDesigner 架构

主容器：

`/project1/mutual_illumination`

关键路径：

- `/input/node_input_panel`：鼠标交互区域；
- `/input/reset_nodes_button`：已升级为 Reset All；
- `/input/reset_all_system`：统一清理 API，支持 `register_reset_hook(name, callback)`；
- `/data/node_data`：节点表；
- `/data/node_system`：新增、拖动及节点状态 API；
- `/graph/edge_data`：逻辑连接表；
- `/graph/graph_system`：MST 更新；
- `/render_nodes/phase1a_node_renderer`：当前节点 Script TOP；
- `/render_connections/phase2_connection_renderer`：Mycelium 与 Transition Script TOP；
- `/visual_controls`：唯一视觉参数入口；
- `/output/phase2_composite`：节点与连接 Add 合成；
- `/output/FINAL_OUT`：最终输出。

已经验证可靠的 Composite 结构是：

- `phase1a_out` 作为 `phase2_composite` 的普通 wire；
- `phase2_composite.par.top` 指向 connection renderer；
- Composite Operation 为 Add。

不要强制 Composite 使用两个普通 wire。跨 COMP 图像应通过本地 Select TOP 或 `par.top` 接入。

## Unified Visual Controls

唯一入口：

`/project1/mutual_illumination/visual_controls`

已接入的页面与功能：

- Node：Node Size、Node Color、Edge Softness，以及 core 相关参数；
- Glow：Glow Amount、Glow Radius、Glow Layers、Inner Glow Size；
- Breathing：Enable、Speed、Size Amount、Brightness Amount、Glow Amount；
- Connections：Line Color、Line Weight、Line Brightness、Branch Brightness；
- Mycelium：Curve Amount、Curve Motion、Filament Spread、Side Branch Amount、Energy Speed，以及必要的附加参数；
- Transitions：Enable、Growth Duration、Fade Duration 等。

builder 重复运行时必须保留用户手动调整的现有值，只增加缺失参数。

## Phase 3E：Ripple & Ambient

外部 builder：`TD/phase3e_builder.py`

安装目标只允许是 `TD_visual_prototype_v05.toe`。它不会自动保存工程。

Textport 命令：

```python
exec(open(r'C:\Users\Maipe\Documents\GitHub\praise-installation\TD\phase3e_builder.py', encoding='utf-8').read())
```

Phase 3E builder 设计：

- 新建 `/render_effects` Base COMP；
- 一个 transient event manager 管理多个 Ripple；
- 一个 Script TOP 在局部 bounding box 内统一绘制 Ripple 与 Ambient；
- 一个 Frame Execute DAT 仅在 Ripple 活跃或 Ambient 动画需要时刷新；
- 包装 `node_system.add_node()`，只有成功新增节点后才触发 Ripple；
- 拖动、移动鼠标和持续按住不会触发 Ripple；
- Ripple 使用 Python 原型的 cubic ease-out 半径与平方亮度衰减；
- Ambient 以节点平均位置为中心，并根据节点独立呼吸相位缓慢变化；
- 通过 `reset_all_system.register_reset_hook()` 持久注册清理逻辑；
- Reset All 立即清空所有 Ripple，即使 Timeline 暂停；
- 新增 `Ambient Color`，并正式启用 Ripple / Ambient 页面中的预留参数；
- 输出使用一个本地 Select TOP，以及普通 wire + `par.top` 的 Add Composite；
- 安装结束会验证 operator errors 和 1280×720 输出。

Phase 3E 外部脚本已经完成静态编译和模拟验证，包括事件去重、多个 Ripple、实际时间过期、Reset hook、10 个 Ripple 的局部渲染。新会话开始时应先询问或检查 Phase 3E 是否已经在真实 TouchDesigner 中完成视觉验收，不要直接假定已经验收。

与 Python 原型的已知小差异：Ambient 使用连续平滑分布近似原来的 8 层填充圆；Ripple 在 1.25px 核心圆环外增加了克制的柔光，以适配当前 TD 视觉。

## 下一轮建议

1. 在真实 TD 中完成 Phase 3E 验收：Ripple 触发准确性、多 Ripple、所有控制参数、Ambient、暂停状态 Reset、保存重开、10 节点性能和 FINAL_OUT 分辨率。
2. 验收成功后手动保存 v05，并单独提交更新后的 TOE（如果当前提交中的 v05 尚未包含安装结果）。
3. 再进入统一 Visual Refinement，重点处理已经记录的问题：Filament Count 区分不明显、Energy Flow 偏弱、菌丝分叉丰富度不足。
4. 不要在 Phase 3E 验收过程中顺手重做 Mycelium，以免混淆问题来源。

## Git 状态注意事项

- 当前分支 `main` 在本次提交前比 `origin/main` 多 4 个本地提交；除非用户明确要求，不要 push。
- `TD/TD_visual_prototype_v02.toe` 当前存在一项未提交修改。这是既有工作区状态，本轮刻意没有纳入提交，也不要擅自还原或覆盖。
- 不提交 TouchDesigner 自动备份、缓存、临时文件、虚拟环境或无关文件。
