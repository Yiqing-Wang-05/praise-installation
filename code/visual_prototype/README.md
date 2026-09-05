# Mutual Illumination — visual prototype

A small, visual-first py5 sketch for exploring warm, organic relationships between
glowing nodes. It is intentionally independent from the TouchDesigner files in
this repository.

## Run

Requirements: Python 3.10+ and Java 17+ (Java 21 recommended).

```powershell
cd code/visual_prototype
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

## Interaction

- Click empty space: create a node (up to the configured maximum)
- Drag a node: move it
- `A`: toggle automatic movement
- `R`: reset the automatic composition
- `Esc`: exit

All visual tuning lives in `visual_prototype/config.py`.

