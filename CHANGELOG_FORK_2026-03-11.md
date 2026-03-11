# Fork Change Summary (2026-03-11)

Base upstream: `time32/FB284_AI_Project`
Branch: `perf/oscilloscope-speedup-20260311`

## What changed

### 1) Oscilloscope performance optimization (`draw.py`)
- Added render cap `MAX_RENDER_POINTS = 200000` to reduce large-data draw pressure.
- Switched heavy plot path to sampled render data while keeping data analysis logic intact.
- Introduced array/cache fields:
  - `df_values`
  - `col_index_map`
  - `visible_cols_cache`
- Reduced high-frequency overhead in crosshair/stats update path by using cached arrays.
- Removed hot-loop `QApplication.processEvents()` call from draw path.
- Changed dot-cache behavior to on-demand:
  - No longer precomputes dots immediately after load.
  - Computes only when "数据点" is enabled.

### 2) Stability adjustment (`draw.py`)
- Windows taskbar icon setup exception handling broadened from `ImportError` to `Exception`
  to avoid non-Windows runtime break in mixed environments.

### 3) Regression report added
- Added `BUG_REPORT_2026-03-11.md` with:
  - dependency prep notes
  - test procedure
  - pass/fail results
  - known gaps and next validation plan

## Compatibility / behavior notes
- Business semantics and core feature flows are unchanged.
- Word COM decrypt path remains Windows-specific (`pywin32` dependent).
- Linux/offscreen regression passed for import/load/render/interaction path.

## Files changed from upstream
- `draw.py`
- `BUG_REPORT_2026-03-11.md`
- `CHANGELOG_FORK_2026-03-11.md`
