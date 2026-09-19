# Mutual Illumination / Praise Installation — Project & Codex Handoff

> **交接快照：2026-09-19 晚间｜可直接作为新 ChatGPT / Codex 会话的首条项目上下文**  
> **当前成果：Python 视觉原型 + TouchDesigner v05 主要视觉复刻完成；v05 已由用户保存，并让 Codex 提交本地 Git commit。**  
> **下一项技术任务：Python → OSC → TouchDesigner 的最小通信验证。**

## 0. 先读这里：现在是什么状态

1. **不要再把 Phase 3E 当作待开发任务。** 用户已确认 Ripple & Ambient 开发完成，`TD_visual_prototype_v05.toe` 已保存，并让 Codex 为当前 v05 做了**本地 Git commit**。当前交接文档不提供重新安装 3E 的指令。
2. 本轮导师的 **“Replicate the Python look in TouchDesigner” HARD REQUEST** 已实现主要功能。Python 原型仍需保留，不要为了 TD 而弃用、覆盖或删减 Python 代码。
3. 下一步是 **Start working on Python → TouchDesigner OSC connection**：先用 Python 模拟 2–3 个持续运动的节点，OSC 发给 TD，使现有节点、MST 和视觉被外部数据驱动；**先不接传感器、不迁移 MST、不重做视觉**。
4. 与 OSC 并行，继续和老师讨论 Visual Language / Interaction / Installation Design，以及 Concept 与 Installation Art Theory 的关联。
5. 后续视觉优化（Filament Count、Energy Flow 等）作为独立 refinement 阶段，不与 OSC 的首个数据链路实验混做。

## 1. 项目是什么：目标、研究和设计语言

**项目名称：Mutual Illumination / Praise Installation**  
**类型：DKU Digital Media 本科个人 Capstone，互动投影装置**  
**导师：Giovanni Santini**

项目试图让日常赞美（praise）的 **warmth、reciprocity、social connection 和 ripple effect** 可见：给予赞美后，正向的情感连接不仅抵达被赞美的人，也可能通过互动与社交网络回应、滋养给予者，并向更多人传播。

预期装置：观众在桌面上放置手部或其他热源；上方热传感器捕捉热源，电脑生成对应节点和关系；投影仪将实时发光网络映射到桌面。当前仍处于 prototype，**热源先由鼠标模拟，真实热感输入与投影坐标校准尚未完成**。

视觉隐喻来自 **mycelium / mycorrhizal network（菌丝／菌根网络）**：传递、共生、滋养和连接。避免把它简化为“几颗发光球 + 普通直线”。

| 视觉元素 | 当前作品中的表达意图 |
| --- | --- |
| Node / Glow / Breathing | 个体存在、温度与生命节奏 |
| Mycelium / Energy Flow | 连接、传递、滋养与关系延续 |
| Connection Growth / Fade | 关系的建立、变化与消散 |
| Ripple | 一次互动向周围产生的回响 |
| Ambient | 整个网络共享的克制、温暖的空间氛围 |

**视觉要求：** 纯黑背景；暖琥珀色 / ivory 节点；柔和分层光晕；节点独立呼吸；有机弯曲且分层的菌丝；温暖但不花哨；避免 full mesh、无意义的长线、明显交叉、厚重霓虹或游戏技能特效。

**概念仍有待研究：** 现在的 Ripple 由“新增节点”触发，连接方向由稳定的 Node ID 规则决定；它们是原型交互规则，**不应直接等同于最终作品中“谁给予／谁接受赞美”的叙事结论**。后续可以结合观众体验重新定义。

## 2. 运行环境和本地路径

- OS：Windows；TouchDesigner **2025.33070**。
- Git 本地仓库：`C:\Users\Maipe\Documents\GitHub\praise-installation`
- TD 安装：`D:\TouchDesigner\bin\TouchDesigner.exe`
- Codex CLI：PowerShell 中通常使用 `codex.cmd`，避免 `codex.ps1` 受到执行策略拦截。
- Python 视觉参考：`code/visual_prototype/visual_prototype/`
- 原始视觉截图：`docs/python_visual_reference.png`
- 项目背景 PDF：`docs/SW背景信息0826.pdf`
- 本交接文件：`docs/PROJECT_HANDOFF_2026-09-19.md`

**重要 Python 代码：** `app.py`、`config.py`、`connections.py`、`node.py`、`renderer.py`、`ripples.py`、`simulation.py`、`interaction.py`。实际开发前应读代码，不要单凭本交接猜测函数签名。

## 3. TOE 版本和成果边界

| 文件 | 版本里程碑 | 使用约定 |
| --- | --- | --- |
| `TD/TD_visual_prototype_v01.toe` | 鼠标动态节点、拖动、Reset、degree-limited MST | 历史检查点 |
| `TD/TD_visual_prototype_v02.toe` | Unified Visual Controls、Glow、Breathing | 历史检查点 |
| `TD/TD_visual_prototype_v03.toe` | Mycelium Connection 视觉 | 历史检查点 |
| `TD/TD_visual_prototype_v04.toe` | Grow In / Fade Out、Unified Reset All | 历史检查点 |
| **`TD/TD_visual_prototype_v05.toe`** | **Ripple & Ambient；当前完整 TD 视觉复刻成果** | **已保存并交由 Codex 做本地 commit；作为下一阶段基线** |

用户已确认 **Phase 3E 开发完成，v05 本地提交**。这不自动证明 `git push` 到 GitHub 成功，也不能代替逐项查看实际 TD 的重开、性能和所有参数测试；遇到具体问题再根据真实工程核验。**不要建议重新执行 Phase 3E builder 来“完成尚未完成的工作”。**

下一轮 OSC 最好在确认工作区状态后，从 v05 **另存独立试验版**（例如 `TD_visual_prototype_v06_osc.toe`；最终名称由用户决定），保留 v05 作为可回退的视觉稳定基线。

## 4. 当前 TD 中已经实现什么

### 输入、节点和连接逻辑

- 点击空白处动态新增节点；按住已有节点可拖动；唯一 Node ID；动态更新节点坐标。
- Mouse fake input 已经验证。左下角 `(0,0)`，X 向右、Y 向上；TD 当前节点输入与 Script TOP 视觉坐标一致，**不要随意再次翻转 Y**。
- `data/node_data` 提供节点数据；`graph/edge_data` 提供实际 MST 选中的连接。
- 以 Kruskal / Union-Find 为基础构建 degree-limited MST，单个节点最多 **3 条逻辑边**；配合距离限制、少量短 branch 和 crossing 控制，支持 2、5、8、10 等节点测试。
- 视觉层临时保留 Fade Out 的旧连接，**不将它们写回 `edge_data`，不纳入 3 条边上限**。

### Visual Controls 和视觉效果

- 一个统一 Visual Control Panel，参数实时可调；不要创建第二套，也不要重置用户的调整。
- **Node：** 分层 core / inner glow / outer halo、尺寸、颜色、柔化。
- **Breathing：** 根据稳定 Node ID 产生独立相位。
- **Mycelium：** Bézier 曲线、layered filaments、soft sheath、side branches、energy flow、curve motion。
- **Transitions：** 新连接沿已有 Bézier 曲线生长，退出 MST 的连接淡出；采用无序 ID pair 稳定识别连接，避免拖动时不必要的重启动画。
- **Ripple（Phase 3E）：** 节点成功创建时触发，多个涟漪并存；扩散、衰减和消失；控制页面从 Reserved 转为实际功能。
- **Ambient（Phase 3E）：** 补齐低亮度环境微光，接入现有参数页面，与节点和连接共享最终画面。

**Phase 3D 参数默认值（仅供定位，不要覆盖用户现值）：** Growth Duration 约 0.72s、Fade Duration 约 0.42s、Growth Ease 约 2.2。生长方向当前由 ID 归一化决定：较小 ID → 较大 ID，并非已经定义好的 giver → receiver。

### Unified Reset All

`TD/reset_all_builder.py` 添加的统一 API 位于：

`/project1/mutual_illumination/input/reset_all_system`

保留已有 Reset All 按钮，统一清除节点、边、拖动及连接过渡；不重置 Visual Controls。扩展入口：`register_reset_hook(name, callback)`，用于 Ripple 等临时效果统一清理。Phase 3E 的实现说明称已集成该接口。新阶段增加临时视觉数据时也必须接入；**Reset All 不等于普通 MST 断边 Fade Out，需即时清空**。

## 5. TD network 的关键路径和易错点

根容器：`/project1/mutual_illumination`

| 相对路径 | 用途 |
| --- | --- |
| `input/node_input_panel` | 当前 mouse fake input 的操作画布 |
| `input/reset_nodes_button` | UI 上已升级为 Reset All |
| `input/reset_all_system` | 清理与 hook API |
| `data/node_data` | 节点表 |
| `data/node_system` | Node 创建、拖动等交互 API |
| `graph/edge_data` | 逻辑连接数据表 |
| `graph/graph_system` | 图算法更新 |
| `render_nodes/phase1a_node_renderer` | 节点 Script TOP |
| `render_connections/phase2_connection_renderer` | 菌丝、Transition Script TOP |
| `render_connections/phase3d_transition_manager` | 无序 node ID pair 的视觉连接过渡状态 |
| `visual_controls` | 唯一视觉参数入口 |
| `output/phase2_composite` | 历史节点 + 连接合成结构 |
| `output/FINAL_OUT` | 最终画面，**1280×720、16:9** |

Phase 3E 额外建立 `render_effects` 一类的 Ripple / Ambient 渲染层。具体子 operator、合成链路请以 **v05 实际 network + `TD/phase3e_builder.py`** 为准，不能假设仍只存在 Phase 2 的两个视觉图层。

**历史上已经解决、不要重犯的 Composite 问题：** Phase 2 使用 `phase1a_out` 的一条普通 wire，并通过 `phase2_composite.par.top` 引用 connection renderer，Operation = Add。跨 COMP 合成可以用本地 Select TOP / `par.top`，**不要强求两个普通 wire**；新增图层时逐个确认最终 1280×720，避免默认 256×256 造成画面错位或缩放。

Timeline 停止时逐帧视觉可能不再更新，但 Reset All 仍应立即生效；运行交互动画时确保 Timeline 处于播放状态。

## 6. Phase 3E 完成记录：Ripple & Ambient

- builder：`TD/phase3e_builder.py`。
- **当前状态：用户确认已开发完成，v05 已保存并委托 Codex 本地 commit。** 原交接文档写的“等待 3E 安装／验收／提交”已过期；本版已纠正。
- 根据 Codex 上一版实现记录，3E 使用统一 transient Ripple manager、局部 bounding box 绘制、按需逐帧更新；成功 `add_node()` 才触发涟漪，拖动不重复触发；同时增加 Ambient 层，启用 Ripple / Ambient Visual Controls，并接入统一 Reset All hook。
- Ripple 参数：Enable、Color、Strength、Duration、Max Radius。Ambient 参数以当前 v05 Visual Controls 为准，包括 Enable、Glow Amount、Radius 及新增 Color（若实际实现存在）。
- Codex 记录的相对 Python 差异：Ambient 用连续平滑分布近似原来的多层圆；Ripple 为核心圆环补了克制的柔光。后续艺术评审中可直接调整，不必先改回 Python 的每个像素细节。
- **如果需要确认某个细节，先检查 v05 / 实际 `phase3e_builder.py`；不要依据旧 handoff 的预开发描述覆盖现有成果。**

## 7. 导师 9 月 21 日四项要求与现状

原文：

> 1. Replicate the python look in Touchdesigner — HARD REQUEST  
> 2. Start working on python -> touchdesigner OSC connection  
> 3. Progress on visual language / interaction design / installation design both from the point of view of the single audience overall as an “entity”  
> 4. Progress on concept / how your installation relates to topics in installation art theory

| 要求 | 当前状态／行动 |
| --- | --- |
| Python look → TD | **主要视觉复刻已完成：v05**。以后专门 refinement，而非重新搭系统。 |
| Python → TD OSC | **下一项优先技术任务。** 先模拟坐标，不必等到热传感器或投影就位。 |
| Visual / Interaction / Installation Design | 用户计划与项目课老师沟通：单个观众眼中的整个装置、参与方式、台面布局、硬件安装与观众动线。短语 “as an entity” 的确切要求可向老师进一步确认。 |
| Concept / Installation Art Theory | 用户准备继续研究，将身体／温度／空间／参与、赞美／互惠／菌丝等关联到具体理论与案例，避免空泛堆砌术语。 |

## 8. 下一项技术任务：Python → OSC → TouchDesigner

### 两条路线的区别

**A. TD-only（当前 TD prototype 可继续延伸）：**

```text
MLX90640 → ESP32-S3 → USB/串口 → TouchDesigner
                                  ├─ 热数据解析／热源追踪／坐标映射
                                  ├─ node_data → TD MST
                                  └─ TD 视觉 → Projector
```

**B. Hybrid（导师要求开始验证的路线）：**

```text
MLX90640 → ESP32-S3 → USB/串口 → Python
                                  ├─ 温度数据解析／Blob 识别／稳定 ID／滤波／校准
                                  └─ OSC/UDP → TouchDesigner node_data
                                                 ├─ TD MST（首轮保留）
                                                 └─ TD 视觉 → Projector
```

**关键：** OSC 传输的是 Node ID、坐标及必要的事件／状态，**不是把 Python 绘制的画面传给 TD**。第一版不需要让 Python 计算 MST；TD 已有 MST 要继续复用。未来如果要把 MST 也迁回 Python，必须明确单一数据权威，不能两端同时各算一套再互相覆盖。

### 建议做的 OSC Minimum Working Demo（第一个可验收闭环）

1. **先核对 Git 工作区、保存 v05，并另存 OSC 测试工程**，不要直接在唯一稳定版本上大改。暂定 v06 OSC，实际文件名由用户确认。
2. 不接真实传感器：本机 Python 用固定且稳定的 ID 模拟 2–3 个缓慢移动的节点，定期发送 OSC 消息；测试时必须能区分创建、更新、离开或使用完整节点列表快照，具体协议和端口先由 Codex 读完架构再提案。
3. TD 中增量搭建接收层（例如 OSC In DAT），**尽量通过 node_system 的合适 API / 受控 input adapter 更新现有 node_data**；严格保留坐标映射与 ID 一致性。
4. 加一个明确的 **Mouse / OSC Input Source** 切换或隔离机制：OSC 模式时防止 mouse frame execute 把外部位置覆盖，Mouse 模式保留原有手动交互作为 fallback。
5. TD 继续做 degree-limited MST + 全套 v05 视觉；新节点是否触发 Ripple、节点消失如何触发 Fade 等应复用现有事件语义。
6. 断开 Python、清除外部节点、Reset All、切回 Mouse 后必须可恢复；不能出现永不消失的旧 ID 和残影。
7. 测试显示 `Python fake positions → OSC → TD node_data → 可见发光节点/菌丝实时移动`，记录错误、延迟与稳定性；确认最终输出还是 1280×720。

**此次 OSC demo 的成功标准：Python 改动假节点位置，TD 画面实时响应，而且可安全切回 Mouse 输入。** 传感器连接、摄像／热源校准、Projector 空间映射与最终硬件部署是之后的独立任务。

## 9. 已购硬件和实际装置待办

已采购：**MLX90640BAB thermal sensor、ESP32-S3 开发板、焊接服务及所需配件**。用户先前规划过投影仪和传感器固定于桌面上方、电脑可能放在桌下，并考虑 USB 线长及走线。

真正接上硬件之后，需要按顺序验证：

```text
传感器能输出温度阵列
→ ESP32-S3 能读取并传给电脑
→ 电脑能识别多个热源
→ 节点 ID 在移动／靠近时尽量稳定
→ 热数据坐标映射至 TD／投影画面
→ 投影到实体桌面并校准
```

不要把真实热源检测、OSC、TouchDesigner 视觉、Projector calibration 全部放在同一次增量改动中。

## 10. 视觉 refinement 和作品研究：下一阶段备忘

**已记录的视觉问题（不要在 OSC 首轮混改）：**

- Filament Count 从 2 到 4 的差异不够明显；
- Energy Flow 偏弱、不容易观察；
- 菌丝的 side branches / 层次还比较有限，整体可更有机；
- 之后结合 v05 的 Ripple、Ambient、Growth / Fade 统一调整色彩、亮度和节奏；
- 测试投影到真实桌面后，需根据实际亮度、观看距离重新评估细线与 Glow。

**与老师讨论的设计问题：** 一位观众第一眼是否知道怎么参与？桌面中“一个热源”对应谁／什么行为？多个热源对一个观众来说是否构成“一个整体实体”？对赞美的给予和回应，视觉究竟如何区分？热传感器和投影仪如何隐藏／呈现？空间尺度是否支持预期观众体验？

**理论研究方向（待查阅读、案例和精确引文，不要伪称已完成研究）：** 参与式装置、身体／具身交互、场域与空间、反馈与互惠、技术如何使不可见关系可感知。最终应落实为“具体理论／作品 → 本项目哪一种交互或空间决定”，而非泛泛说技术使人连接。

## 11. Git / Codex 协作规矩

- 用户倾向 **中文交流、一次一个阶段、可复制 Prompt、自己在 TD 中跑真实测试**；编程背景非传统 CS，解释清楚但不用过度展开。
- Codex 一般只写独立外部增量 builder，提供准确的 **Textport 单行命令**；未经许可不要运行 builder、自动保存 TOE、重建已验证阶段或修改历史 `.toe`。
- `bootstrap_builder.py`、旧 phase builders 是历史开发记录，**不能为 OSC 直接全部重跑**。
- 本地 **commit ≠ GitHub push**；不要声称已推送云端。若用户要求同步，再核对网络／权限和 `git status`。
- 不要擅自 `git reset`、`git restore`、覆盖用户的 Visual Controls 或删除未提交改动。只暂存本轮相关文件，不提交 TD 自动备份、缓存、虚拟环境。
- 旧 Codex 文档曾记录：在某次提交前 `main` 比 `origin/main` 多 4 个提交、`v02.toe` 存在未提交修改。**这是历史快照，不是当前已验证状态**；新会话先运行 `git status --short`、`git log -1 --oneline`、`git status -sb`，按实时结果处理。

## 12. 给下一段 AI 会话的简短开场

> 我正在做毕业设计 Mutual Illumination / Praise Installation。请把这份 handoff 当作当前项目基线：Python 视觉原型保留；TouchDesigner v05 已完成 Ripple & Ambient 等主要视觉复刻，并已保存和本地 Git commit。不要再让我重做 3E，也不要动旧 TOE。下一步我要完成导师要求的 Python → OSC → TD minimum working demo：先由 Python 发送模拟 Node ID / X / Y，让现有 TD `node_data`、MST 和视觉实时响应，同时保留 Mouse input 可回退。请先检查代码和 Git 实际状态，再给我分阶段、可直接发给 Codex 的方案。概念、空间装置和视觉 refinement 后续分别推进。
