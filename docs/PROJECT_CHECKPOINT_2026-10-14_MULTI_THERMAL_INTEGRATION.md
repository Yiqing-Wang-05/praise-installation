# Mutual Illumination — Multi-Thermal Integration Checkpoint

> **Checkpoint date: 2026-10-14**
> **Milestone: Multiple real thermal sources successfully drive the full TouchDesigner visual system.**
> This checkpoint supplements, and does not replace, `PROJECT_HANDOFF_2026-09-19.md` or `PROJECT_CHECKPOINT_2026-10-09_THERMAL_INPUT.md`.

## Project milestone

The project has reached a verified physical-input milestone:

**Multiple real thermal sources successfully drive the full TouchDesigner visual system.**

Two to three real tea candles have been detected simultaneously, assigned stable thermal track IDs, converted into independent TouchDesigner nodes, and passed through the existing node graph and visual-effects chain. The real installation input is no longer limited to an isolated moving-dot preview.

## Current architecture

```text
MLX90640
→ ESP32-S3
→ multi-source connected-component detection
→ stable thermal track IDs
→ THERMAL2 serial snapshot
→ TouchDesigner parser
→ thermal node adapter
→ node_data
→ MST
→ Glow / Mycelium / Ripple / Grow-Fade
→ FINAL_OUT
```

The existing MST and visual systems remain authoritative. Thermal input supplies node lifecycle and canonical positions through the controlled `node_system` API; it does not duplicate or replace the graph or rendering algorithms.

## Hardware

- Thermal sensor: MLX90640, 32×24 pixels.
- Microcontroller: ESP32-S3.
- Windows serial port: `COM5`.
- I²C SDA: GPIO8.
- I²C SCL: GPIO9.
- Serial baud rate: 115200.
- MLX90640 configured refresh rate: 8 Hz.
- Sensor has been tested successfully from approximately 1 m or more above the table.

## Arduino implementation

### Preserved single-source checkpoint

`code/thermal_pipeline/arduino/thermal_single_source/thermal_single_source.ino` remains the stable historical single-source implementation. It records the first working region-centroid tracker and the original `THERMAL|key=value` protocol. It has not been overwritten by the multi-source work.

### Current multi-source MVP

`code/thermal_pipeline/arduino/thermal_multi_source/thermal_multi_source.ino` is the current presentation-oriented MVP.

Each 32×24 frame follows this path:

```text
valid-pixel scan
→ median background estimate
→ adaptive contrast/grow threshold
→ full-frame 8-neighbor connected-component scan
→ per-region weighted centroid, area, and peak temperature
→ nearest-neighbor track association
→ presence/loss stability
→ per-track EMA smoothing and dead zone
→ canonical normalized u/v
→ complete THERMAL2 snapshot
```

Current tracking configuration:

| Parameter | Value |
| --- | ---: |
| Maximum tracks | 8 |
| Minimum contrast | 4.0 °C |
| Minimum region area | 3 pixels |
| Match distance gate | 3.0 sensor pixels |
| Presence confirmation | 3 frames |
| Loss tolerance | 5 frames |
| EMA alpha | 0.35 |
| Dead zone | 0.45 sensor pixel |

Confirmed tracks receive monotonically increasing ESP32-side IDs. Existing confirmed tracks are matched before tentative tracks to reduce ID churn. A track remains published through short misses and is removed only after the loss tolerance is reached.

No strict absolute candle-temperature filter is currently active. Detection still uses the adaptive median-background and contrast logic, so hands, bodies, and other sufficiently warm regions can be accepted.

### Canonical coordinate mapping

Raw `centroid_x` / `cx` and `centroid_y` / `cy` retain their original sensor-axis meaning. The fixed sensor mounting is converted only when publishing canonical coordinates:

```text
u = cy / 23
v = 1 - cx / 31
```

Canonical meaning:

```text
u: physical left 0 → physical right 1
v: audience side / screen bottom 0 → far side / screen top 1
```

TouchDesigner consumes these final canonical values directly and applies no additional swap or flip.

## Serial protocol

The multi-source sketch publishes one complete newline-delimited snapshot per processed frame:

```text
THERMAL2|session=184762|seq=1042|count=2|bg=24.71|thr=29.10|fps=3.9|sources=12,0.5480,0.4350,17.000,10.000,6,42.50,1,0;13,0.7200,0.6100,12.090,16.560,5,41.80,1,0
```

Frame fields:

| Field | Meaning |
| --- | --- |
| `session` | ESP32 boot/session identifier; changes after restart |
| `seq` | Frame sequence number within the session |
| `count` | Number of confirmed tracks in this complete snapshot |
| `bg` | Median frame background temperature |
| `thr` | Connected-component pixel threshold |
| `fps` | Measured, smoothed processing rate |
| `sources` | Semicolon-separated source records |

Each source record has this fixed schema:

```text
track_id,u,v,cx,cy,area,peak_c,seen,miss
```

| Field | Meaning |
| --- | --- |
| `track_id` | Stable ESP32-side thermal track ID |
| `u`, `v` | Final canonical normalized coordinates |
| `cx`, `cy` | Stable centroid in raw sensor axes |
| `area` | Connected-region area in sensor pixels |
| `peak_c` | Region peak temperature |
| `seen` | `1` when matched to a region in this frame; otherwise `0` |
| `miss` | Current consecutive missing-frame count |

No-source frames are still complete snapshots:

```text
THERMAL2|session=184762|seq=1043|count=0|bg=24.70|thr=29.08|fps=3.9|sources=
```

Because the protocol sends full snapshots rather than one-off add/remove events, a dropped line can self-recover on the next valid frame.

## TouchDesigner integration

### Serial test/parser area

The isolated serial area remains at:

```text
/project1/mutual_illumination/thermal_serial_test
```

Important operators:

| Operator | Purpose |
| --- | --- |
| `serial_in` | Owns COM5 at 115200 baud |
| `serial_parser` | Validates complete `THERMAL2` snapshots transactionally |
| `thermal_frame_state` | Stores session, sequence, count, temperatures, FPS, and parse status |
| `thermal_sources` | Stores one row per confirmed thermal track |
| `OUT_PREVIEW` | Diagnostic multi-dot preview only |

Malformed or incomplete records do not partially replace `thermal_sources`. The last valid source table remains until a valid new snapshot arrives or the downstream stale timeout removes nodes.

### Thermal node adapter

The adapter is created at:

```text
/project1/mutual_illumination/input/thermal_node_input
```

It maintains:

```text
(session_id, thermal_track_id) → high TouchDesigner node ID
```

TouchDesigner node IDs begin at `1000000`, keeping external thermal nodes separate from ordinary mouse-created IDs. The adapter uses the controlled `node_system` API:

- `add_external_node(node_id, u, v)`
- `update_node(node_id, u, v)`
- `remove_node(node_id)`

Behavior:

- A newly confirmed thermal track creates one node and triggers Ripple once.
- Later snapshots update that same node without retriggering Ripple.
- A track missing from the confirmed snapshot is removed after Arduino-side loss tolerance.
- A new ESP32 session clears old thermal bindings.
- Approximately one second without a valid snapshot triggers stale cleanup.
- Reset All clears thermal nodes and suppresses already-present track IDs until they leave.

### Mouse / Thermal switch

Mouse remains the default input after installing the builder.

Switch to Thermal:

```python
op('/project1/mutual_illumination/input/thermal_node_input/thermal_node_manager').module.set_source('thermal')
```

Switch back to Mouse:

```python
op('/project1/mutual_illumination/input/thermal_node_input/thermal_node_manager').module.set_source('mouse')
```

Thermal mode disables the existing mouse frame execute. Returning to Mouse removes thermal-owned nodes and restores mouse input.

The adapter feeds the existing chain without changing its algorithms or visual parameters:

```text
thermal node adapter
→ node_data
→ existing MST / edge_data
→ existing Node Glow / Mycelium / Ripple / Grow-Fade
→ FINAL_OUT
```

## Confirmed working behavior

The following behavior has been physically verified:

- Multiple hands can produce `count=2` during diagnostics, confirming that independent hot regions are being separated and published.
- Two to three real tea candles successfully produce multiple simultaneous thermal tracks and multiple TouchDesigner nodes.
- Each candle corresponds to an independent thermal node when its hot region is spatially separated from the others.
- Thermal nodes automatically enter the existing MST and Mycelium connection system.
- Node Glow, Ripple, Grow/Fade, and connection behavior are reused successfully without visual-module changes.
- Moving a candle moves its corresponding node while retaining the same stable track/node binding under normal movement.
- Removing a source removes its node after the configured loss tolerance, allowing existing connection Fade behavior to run.
- Canonical left/right and near/far movement directions match the real table.
- Real physical thermal input now drives the full TouchDesigner visual chain through `FINAL_OUT`.
- Tea candles remain detectable with the sensor approximately 1 m or more above the table in the current test setup.

## Known limitations / next work

These items are recorded for later work and are not solved in this checkpoint:

- An absolute candle-temperature threshold is not implemented or tuned.
- Human hands and bodies can still be detected as thermal sources.
- Track positions can still jitter.
- Actual measured thermal FPS is currently around 3.9 despite the MLX90640 8 Hz configuration.
- Sensor mounting height and physical rig still need to be fixed.
- Sensor/table/projector coordinate mapping and calibration are still required.
- Closely spaced candles may merge into one connected component.
- Nearest-neighbor association may change IDs during unusually fast movement, merge/split events, or ambiguous crossings.
- Visual refinement remains necessary after the technical chain is stable.
- Projector testing and installation-scale testing remain outstanding.

## Immediate next phase

1. Prepare and deliver the SW progress presentation using the verified multi-source chain.
2. After the presentation, tune candle threshold, stability, jitter, and refresh rate.
3. Build a fixed sensor rig and confirm the final mounting height.
4. Calibrate sensor/table/projector coordinates and mapping.
5. Perform full installation and projector tests at final scale.

## Important operating notes

- Only one process can own `COM5` at a time.
- Close Arduino Serial Monitor before TouchDesigner activates its Serial DAT.
- If TouchDesigner thermal state freezes, toggle the Serial DAT `Active` parameter off and on.
- Pressing ESP32 `RST` can recover the stream if serial output stops.
- Arduino IDE does not need to remain open after a successful upload.
- Keep the TouchDesigner timeline playing so frame-start parser and adapter callbacks run.
- The updated builders must be run in this order: `thermal_serial_test_builder.py`, then `thermal_node_input_builder.py`.
- Neither builder automatically saves a `.toe`; save an explicitly named project manually only after visual verification.

## Milestone files and repository boundary

Thermal milestone source files:

```text
code/thermal_pipeline/__init__.py
code/thermal_pipeline/coordinates.py
code/thermal_pipeline/test_coordinates.py
code/thermal_pipeline/arduino/thermal_single_source/thermal_single_source.ino
code/thermal_pipeline/arduino/thermal_multi_source/thermal_multi_source.ino
TD/thermal_serial_test_builder.py
TD/thermal_node_input_builder.py
docs/PROJECT_CHECKPOINT_2026-10-09_THERMAL_INPUT.md
docs/PROJECT_CHECKPOINT_2026-10-14_MULTI_THERMAL_INTEGRATION.md
```

The current `.toe` files and OSC experiment files are deliberately outside this source checkpoint. Binary TouchDesigner project snapshots should be visually reopened and committed separately when a specific `.toe` is chosen as the next named baseline.
