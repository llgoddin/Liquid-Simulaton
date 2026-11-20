# Liquid-Simulaton

Liquid-Simulaton is an experimental 2D particle-fluid simulation written in
Python and pygame. It uses Smoothed Particle Hydrodynamics (SPH) for particle
interactions. The Python implementation does not reach the recorded 200-particle/30-fps target; Lucas has decided further performance optimization belongs to Phase 2's Rust rewrite. Phase 1 remains in progress pending physics qualification.

## Current features

- Fixed-step physics at 120 Hz, independent of render timing, with a maximum of
eight substeps per frame. Excess elapsed time is dropped and accumulated in
`Particle_Manager.dropped_time`.
- SPH particle interaction, controlled by the existing **Repulse** dashboard
toggle. The control retains its historical name; it enables the SPH solver.
- Gravity and particle-count controls, plus adjustable container dimensions.
- Radial mouse interaction: left and right mouse buttons apply opposite force
directions; the influence radius is shown around the cursor.
- A circular obstacle in the simulation container.
- Optional diagnostic overlays, toggled with **D**: container bounds,
per-particle influence discs and velocity lines. The particles, obstacle and
mouse influence ring remain visible in the normal view.
- Dashboard with particle count and FPS readouts.
- `unittest` coverage and GitHub Actions CI for tests and linting.

## Requirements and setup

Python 3.12 is the supported and CI-tested version. The sole runtime dependency
is pygame, pinned in `requirements.txt`; NumPy is not a runtime dependency. Python
and pygame are retained for this phase because they are the existing working
application stack, and the scope is to add/test the fluid model without replacing
the renderer or dashboard.

From the repository root:

```sh
python3.12 -m venv .env
.env/bin/python -m pip install -r requirements.txt
.env/bin/python Graphics.py
```

`Graphics.py` launches the interactive application. Use the dashboard to toggle
gravity or SPH interaction and change particle count or container dimensions.
Use the left and right mouse buttons over the simulation area to apply radial
mouse forces. Press **D** to toggle diagnostic overlays.

## Tests and lint

Run the test suite from the repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .env/bin/python -m unittest discover -s tests -v
```

The CI lint gate uses Ruff 0.17.5, installed separately rather than included in
runtime requirements:

```sh
python3.12 -m pip install ruff==0.17.5
ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution and local test guidance.

## Physics and performance status

The timestep is fixed at 1/120 second, with at most eight substeps processed in
a rendered frame. If the simulation falls behind, excess time is dropped; this
keeps the application from accumulating an unbounded backlog, but means
simulation time can lag wall-clock time under sustained overload. Existing
force values are calibrated as velocity increments at a 120 Hz reference rate,
not SI units. SPH forces are converted before entering that legacy force channel.
Runaway guards cap the legacy force magnitude at 50, speed at 500 px/s, and a
direct physics step at 1/120 s; negative or non-finite step durations are treated
as zero. These broad safety limits are not SPH calibration or stability criteria.

| NumPy candidate | Median step | p95 step | 200-particle frame median | Frame p95 |
|---|---:|---:|---:|---:|
| Current experimental candidate | 5.84 ms | 8.97 ms | 45.02 ms | 69.05 ms |

The latest full-app run used the optional experimental NumPy solver, 200 particles, a 30 Hz cap, and 300 warmup steps. Over 4.07 seconds it produced 82 frames: mean 48.54 ms, median 45.02 ms, p95 69.05 ms, and maximum 101.24 ms. It processed 467 physics steps (5.63 per frame) and dropped 0.0800 seconds of simulation time.

The force, velocity and timestep guards did not activate in the timed run; the measured maximum speed was 6.39 px/s and density ranged from 0.01749 to 0.10762 against rest density 0.004444. The run missed the 33.33 ms budget. Lucas has decided that further Python performance optimization belongs to Phase 2's Rust rewrite, so this gap is documented rather than optimized further in this phase. These measurements do not establish physical accuracy or stability. Phase 1 remains in progress pending physics qualification; no performance pass or phase completion is claimed.

The NumPy solver remains experimental and is not a runtime dependency; `requirements.txt` is still pygame-only. An earlier 60 Hz full-app run also missed its 16.67 ms budget (median 29.82 ms, p95 45.93 ms). The pure-Python baseline was slower: 101.49 ms median frame time and 1.206 seconds dropped over about four seconds.

## References

- [Smoothed-particle hydrodynamics](https://en.wikipedia.org/wiki/Smoothed-particle_hydrodynamics)
- [Coding Adventure: Simulating Fluids — Sebastian Lague](https://youtu.be/rSKMYc1CQHE)

## Author and licence

Lucas Goddin. Contributions are accepted under the [MIT licence](LICENSE).
