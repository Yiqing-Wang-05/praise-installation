# Mutual Illumination — Thermal Input Checkpoint

> **Checkpoint date: 2026-10-09**
> **Milestone: First real heat-source data successfully reaches TouchDesigner and drives an isolated visualization.**
> This document supplements, and does not replace, `PROJECT_HANDOFF_2026-09-19.md`.

## 1. Outcome

The first end-to-end real thermal-input path is working:

```text
Tea candle / real heat source
→ MLX90640 32×24 thermal frame
→ ESP32-S3 single-source tracking
→ USB serial, COM5 at 115200 baud
→ TouchDesigner Serial DAT
→ parser
→ hotspot_state
→ OUT_PREVIEW moving dot
```

Verified behavior:

- ESP32-S3 communicates with the Windows computer through `COM5`.
- MLX90640 frames are read successfully over I²C at 32×24 resolution.
- A real heat source appears and moves in the isolated TouchDesigner preview.
- Real left/right and near/far movement matches the moving dot on screen.
- Presence, stable position, serial parsing, and preview visibility all work for one source.

This is the first verified instance of physical heat data entering the project and becoming a live TouchDesigner visual response. It is an input-pipeline milestone, not yet an integration with the artwork's node network.

## 2. Single-source tracking

The Arduino implementation no longer uses a single hottest pixel. Each frame now follows this pipeline:

```text
frame median background estimate
→ adaptive seed/grow temperature thresholds
→ 8-neighbor region growing from the hottest seed
→ reject undersized regions
→ capped temperature-weighted centroid
→ presence/loss frame confirmation
→ EMA smoothing
→ sensor-pixel dead zone
→ canonical normalized u/v
```

Current default parameters:

| Parameter | Value | Purpose |
| --- | ---: | --- |
| Minimum contrast | 4.0 °C | Reject frames without a clear source above the median background |
| Seed threshold | `background + max(3.0, contrast × 0.45)` | Require a strong hot seed |
| Grow threshold | `background + clamp(contrast × 0.20, 1.5, 5.0)` | Collect the connected hot region |
| Minimum region area | 3 pixels | Reject isolated single-pixel noise |
| Centroid weight | `clamp(temp - threshold, 0.5, 5.0)` | Favor warmer pixels without allowing one pixel to dominate |
| EMA alpha | 0.35 | Reduce frame-to-frame centroid jitter |
| Dead zone | 0.45 sensor pixel | Hold a stationary source at a stable published position |
| Presence confirmation | 3 consecutive frames | Prevent instant appearance from one noisy frame |
| Loss confirmation | 5 consecutive frames | Prevent instant disappearance from a brief miss |
| Sensor refresh setting | 8 Hz | Improve continuity over the earlier 4 Hz plus fixed delay test |
| I²C clock | 400 kHz | Support the current stable frame-read path |

The sketch keeps MLX90640 Chess mode and 18-bit ADC resolution. The former `delay(500)` on the successful frame path has been removed. Actual measured `fps` is included in every serial record and should be evaluated during physical tests rather than assuming the configured rate is always achieved.

## 3. Fixed sensor-mount coordinate mapping

Raw centroid coordinates retain their sensor meaning for debugging:

```text
centroid_x / cx: sensor x, 0–31
centroid_y / cy: sensor y, 0–23
```

The fixed physical mounting orientation is converted to canonical table coordinates only when producing normalized output:

```text
u = centroid_y / 23.0
v = 1.0 - (centroid_x / 31.0)
```

Canonical meaning:

```text
u: real-world left 0 → real-world right 1
v: audience side / screen bottom 0 → far side / screen top 1
```

TouchDesigner does not apply another flip or axis swap. It consumes the canonical `u/v` values sent by the ESP32.

## 4. Serial protocol

The ESP32 sends one fixed, machine-readable record per successfully processed frame:

```text
THERMAL|p=1|u=0.4348|v=0.4516|cx=17.000|cy=10.000|area=12|bg=24.71|max=32.54|thr=26.27|fps=7.9|seq=123
```

Fields:

| Field | Meaning |
| --- | --- |
| `p` | Stable presence state: `1` present, `0` absent |
| `u`, `v` | Canonical normalized position consumed by TouchDesigner |
| `cx`, `cy` | Stable centroid in raw sensor axes, retained for debugging |
| `area` | Current detected connected-region size in pixels |
| `bg` | Frame median background temperature |
| `max` | Frame maximum temperature |
| `thr` | Region-growing threshold used for the frame |
| `fps` | Smoothed measured frame-processing rate |
| `seq` | Successful-frame sequence number |

When `p=0`, the last stable position remains in the diagnostic fields, but TouchDesigner hides the preview dot.

## 5. TouchDesigner test boundary

The current thermal input remains isolated under:

```text
/project1/mutual_illumination/thermal_serial_test
```

Current test chain:

```text
serial_in
→ serial_parser
→ hotspot_state
→ moving_dot
→ OUT_PREVIEW
```

The thermal test does **not** currently connect to or modify:

- mouse input or its fallback behavior;
- `data/node_data`;
- MST / `graph/edge_data`;
- `render_nodes` or `render_connections`;
- Mycelium, Glow, Breathing, Growth/Fade, Ripple, or Ambient effects;
- `visual_controls`;
- `reset_all_system`;
- `output/FINAL_OUT`.

The local experimental file `TD/TD_visual_prototype_v07_thermal.toe` is present in the working tree as the current thermal test project. It remains an uncommitted binary checkpoint at the time of this document and was not modified while creating this checkpoint.

## 6. Thermal-related files

### Repository files created during this milestone

- `code/thermal_pipeline/arduino/thermal_single_source/thermal_single_source.ino`
  Independent ESP32-S3/MLX90640 single-source tracker and serial publisher.
- `TD/thermal_serial_test_builder.py`
  Incrementally creates or upgrades only the isolated `thermal_serial_test` area; never saves the TOE.

### Existing repository files extended during this milestone

- `code/thermal_pipeline/coordinates.py`
  Adds sensor-axis swapping and the fixed mounting mapping reference.
- `code/thermal_pipeline/__init__.py`
  Exports the fixed thermal-mount mapping.
- `code/thermal_pipeline/test_coordinates.py`
  Covers raw normalization, flips, swapping, clamping, and mounting orientation.

### Preserved reference

- `C:\Users\Maipe\Documents\Arduino\I2C_test\I2C_test.ino`
  Earlier verified hottest-pixel test sketch outside the repository. It was deliberately not overwritten.

Validation completed before this checkpoint:

- Coordinate mapping: 8 unit tests passing.
- ESP32-S3 sketch: compiles successfully for `esp32:esp32:esp32s3`.
- TouchDesigner parser: present, absent, and malformed-line cases pass offline checks.
- Physical validation: one real heat source successfully controls `OUT_PREVIEW` with the correct canonical movement directions.

## 7. Current limitations

- One connected hot region / one source only.
- Threshold, smoothing, dead zone, and presence timing have working defaults but are not finally tuned for installation distance and ambient conditions.
- The configured 8 Hz path is working, but final sustained refresh-rate optimization is still pending.
- No thermal-to-artwork node lifecycle has been defined yet.
- No multiple-source separation, stable multi-source IDs, merge/split handling, or occlusion recovery.
- No projector/table spatial calibration or homography.
- No final installation-scale test under projector lighting and real table geometry.

## 8. Next stages

Proceed incrementally and keep mouse input available as a fallback until thermal control is fully verified.

1. **Replace the mouse fake input with a selectable thermal input adapter.**
   Define explicit Mouse/Thermal ownership so both sources never write the node table simultaneously.
2. **Connect thermal presence and canonical position to the existing `node_data` lifecycle.**
   Reuse the existing MST, transitions, Reset All, and visual effects instead of rebuilding them.
3. **Extend detection to multiple candles / heat sources.**
   Add connected-component extraction, stable IDs, temporal association, and merge/split behavior.
4. **Tune acquisition and tracking.**
   Measure actual FPS and adjust refresh rate, threshold fractions, minimum region area, EMA alpha, dead zone, and presence/loss frame counts using the real installation distance.
5. **Calibrate projector and table coordinates.**
   Add spatial calibration or homography only after source tracking and artwork integration are stable.

## 9. Git handling for this checkpoint

The repository contains unrelated and historical uncommitted TD/OSC work. Any future commit for this milestone should use explicit paths and should not broadly stage `TD/` or `code/`.

Recommended code-and-document commit scope:

```text
docs/PROJECT_CHECKPOINT_2026-10-09_THERMAL_INPUT.md
code/thermal_pipeline/__init__.py
code/thermal_pipeline/coordinates.py
code/thermal_pipeline/test_coordinates.py
code/thermal_pipeline/arduino/thermal_single_source/thermal_single_source.ino
TD/thermal_serial_test_builder.py
```

Exclude from that commit:

```text
TD/TD_visual_prototype_v02.toe
TD/TD_visual_prototype_v05.toe
TD/TD_visual_prototype_v06_OSC.toe
TD/TD_visual_prototype_v07_thermal.toe
TD/osc_mvp_builder.py
code/osc_mvp/
```

If the validated v07 thermal TOE should later be archived, first reopen and manually verify it, then place it in a separate explicit binary-checkpoint commit. Do not mix it into the source-code checkpoint by accident.
