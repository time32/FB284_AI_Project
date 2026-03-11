# Bug/Regression Report - 2026-03-11

## Scope
- Project: `FB284_AI_Project`
- Focus: Oscilloscope performance and stability after `draw.py` optimization
- Environment: Linux (offscreen Qt), Python 3.13

## Dependencies Prepared
Installed with user-site pip:
- `pandas`
- `numpy`
- `pyqtgraph`
- `PyQt5`

Note:
- `pywin32` not installed in this Linux environment (expected). Word COM decrypt path is Windows-only and guarded by fallback logic.

## Test Method
1. Syntax checks: `python3 -m py_compile FB284calculate_AI.py gui_AI.py draw.py`
2. Runtime regression (offscreen):
   - Initialize `QApplication`
   - Instantiate `ProOscilloscope`
   - Simulate load/first render with synthetic data (`60000 x 8` float32)
   - Toggle core interactions: separate-axis, crosshair, measure
   - Trigger on-demand dots cache and wait for worker completion
   - Close and cleanup

## Results
- PASS | QApplication init
- PASS | Load+first render | `0.032s` for `60000x8`
- PASS | Render+interaction toggles
- PASS | On-demand dots cache | `0.529s`
- PASS | Close cleanup

## Confirmed Improvements
- First render no longer waits for dot-cache preprocessing.
- Dot cache generation is now on-demand.
- Large-data plotting uses capped render points (`MAX_RENDER_POINTS`) to reduce interaction stutter.
- Crosshair/stat table path uses cached arrays, reducing per-event overhead.

## Remaining Risks / Gaps
1. Windows-only Word decrypt path was not executed in this test run (no `pywin32` on Linux).
2. Real hardware/user CSV traces may expose edge cases not covered by synthetic data.
3. Tkinter monitor module runtime interaction (`gui_AI.py`) not fully exercised in headless mode.

## Next Suggested Validation (Windows target)
1. Import a real large CSV/TXT (>100k rows) and compare first-paint time before/after.
2. Repeated toggle stress (separate-axis / dots / crosshair / measure) for 20 cycles.
3. Word-protected file fallback check (with `pywin32` installed) to verify decrypt path.
