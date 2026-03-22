# 数值计算与杂项 SOP
> 数值积分、收敛研究、参数优化、时间步进、Zarr
> 包含 8 个 OpenClaw skill 的压缩迁移。

---

### convergence-study
**用途**: Spatial and temporal convergence analysis with Richardson extrapolation and Grid Convergence Index (GCI) for solution verification
```
Do you have 3+ refinement levels?
+-- YES --> Run h_refinement.py or dt_refinement.py
|           +-- Observed order matches expected? --> Solution verified
|           +-- Order too low? --> Check: pre-asymptotic, coding error, insufficient resolution
|           +-- Order too high? --> Check: superconvergence or cancellation effects
+-- NO (only 2 levels) --> Use richardson_extrapolation.py with assumed order
                           (less reliable without order verification)
```

### differentiation-schemes
**用途**: Select and apply numerical differentiation schemes for PDE/ODE discretization. Use when choosing finite difference/volume/spectral schemes, building stencils, handling boundaries, estimating trunca...
```
python3 scripts/stencil_generator.py --order 2 --accuracy 4 --scheme central --json
```
**限制**: **Boundary handling**: Stencil generator provides interior stencils; boundaries need special treatment; **Nonuniform grids**: Standard stencils assume uniform spacing

### numerical-integration
**用途**: Select and configure time integration methods for ODE/PDE simulations. Use when choosing explicit/implicit schemes, setting error tolerances, adapting time steps, diagnosing integration accuracy, p...
```
python3 scripts/integrator_selector.py --stiff --jacobian-available --accuracy high --json
```
**限制**: **No automatic stiffness detection**: Use stiffness_detector from numerical-stability; **Splitting assumes separability**: Terms must be cleanly separable

### numerical-stability
**用途**: Analyze and enforce numerical stability for time-dependent PDE simulations. Use when selecting time steps, choosing explicit/implicit schemes, diagnosing numerical blow-up, checking CFL/Fourier cri...
```
python3 scripts/cfl_checker.py --dx 0.01 --dt 1e-4 --diffusivity 1e-3 --dimensions 2 --json
```
**限制**: **Explicit schemes only** for CFL/Fourier checks (implicit is unconditionally stable); **Von Neumann analysis** assumes linear, constant-coefficient, periodic BCs

### parameter-optimization
**用途**: Explore and optimize simulation parameters via design of experiments (DOE), sensitivity analysis, and optimizer selection. Use for calibration, uncertainty studies, parameter sweeps, LHS sampling, ...
```
python3 scripts/doe_generator.py --params 2 --budget 30 --method lhs --json
```
**限制**: **Not for real-time optimization**: Scripts provide recommendations, not live optimization loops; **Surrogate is a placeholder**: `surrogate_builder.py` computes basic metrics; replace with actual model for production

### post-processing
**用途**: Extract, analyze, and visualize simulation output data. Use for field extraction, time series analysis, line profiles, statistical summaries, derived quantity computation, result comparison to refe...
```
# List available fields and timesteps
python scripts/field_extractor.py --input results/ --list --json
```

### time-stepping
**用途**: Plan and control time-step policies for simulations. Use when coupling CFL/physics limits with adaptive stepping, ramping initial transients, scheduling outputs/checkpoints, or planning restart str...
```
python3 scripts/checkpoint_planner.py --run-time 36000 --checkpoint-cost 120 --max-lost-time 1800 --json
```
**限制**: **Not adaptive control**: Plans static schedules, not runtime adaptation; **Assumes constant physics**: If parameters change, re-plan

### zarr-python
**用途**: Chunked N-D arrays for cloud storage. Compressed arrays, parallel I/O, S3/GCS integration, NumPy/Dask/Xarray compatible, for large-scale scientific computing pipelines.
```
uv pip install zarr
```
