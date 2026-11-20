# Liquid-Simulaton

Liquid-Simulaton is an experimental 2D particle-fluid simulation written in
Python and pygame. It uses Smoothed Particle Hydrodynamics (SPH) for particle
interactions. The staged Phase 1 candidate has boundedness and wall-support evidence only for the documented cases; it is not a general physics qualification. The Python implementation misses the recorded 200-particle/30-fps target, and the current wall-support candidate is slower still. Lucas has decided further Python optimization belongs to Phase 2's Rust rewrite. Phase 1 remains in progress pending final review and a PR to `main`.

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
simulation time can lag wall-clock time under sustained overload. Existing mouse-force values remain calibrated as velocity increments at a 120 Hz reference rate, not SI units. SPH forces and gravity use physical units and are converted once through `Particle_Manager.PHYSICAL_FORCE_TO_LEGACY` before entering `Particle.move`'s legacy channel. Gravity is now 10 px/s²; the former `-10` per-step velocity impulse represented 1,200 px/s² and repeatedly activated the speed guard in the 200-particle stress run. This intentionally changes the gravity toggle's strength to make it consistent with the SPH equations. Runaway guards cap the net legacy force magnitude at 50, speed at 500 px/s, and a direct physics step at 1/120 s; negative or non-finite durations are treated as zero. The force and timestep limits remain broad safety bounds, not stability criteria.

SPH wall support uses reflected ghost samples within the kernel radius at the four container planes and at the circular obstacle. Ghost velocities reflect their wall-normal component; the circular mapping weights ghost mass by its 2D radial Jacobian. Geometry projection remains the final non-penetration safeguard. This is an approximate boundary condition, not a general free-surface or arbitrary-geometry solver. At the application's default circle geometry, static near-wall density ratios were brought within 6.3% of the interior reference; the dynamic 5-second comparison showed a mixed density response. The circle treatment is qualified only for the documented cases, not general use (see [SPH.md](SPH.md)).

| Measured run | Median step | p95 step | 200-particle frame median | Frame p95 |
|---|---:|---:|---:|---:|
| Earlier optional NumPy full-app candidate | 5.84 ms | 8.97 ms | 45.02 ms | 69.05 ms |
| Merged main before ghost samples (pure Python, 30 Hz) | — | — | 87.745 ms | 104.875 ms |
| Staged wall-support candidate (pure Python, 30 Hz) | — | — | 232.800 ms | 238.146 ms |

The earlier full-app benchmark used the optional experimental NumPy solver, 200 particles, a 30 Hz cap, and 300 warmup steps. Over 4.07 seconds it produced 82 frames: mean 48.54 ms, median 45.02 ms, p95 69.05 ms, and maximum 101.24 ms. It processed 467 physics steps (5.63 per frame) and dropped 0.0800 seconds of simulation time.

The force, velocity and timestep guards did not activate in that benchmark; the measured maximum speed was 6.39 px/s and density ranged from 0.01749 to 0.10762 against rest density 0.004444. That earlier optional-NumPy run missed the 33.33 ms budget. Lucas has decided further Python performance optimization belongs to Phase 2's Rust rewrite, so the miss is documented rather than optimized in this phase. It predates the current wall-support candidate and is not a measurement of that candidate.

A separate headless full-app comparison used a scratch-only real-clock harness on macOS 15.8.3 (x86_64, Intel i9-9880H), Python 3.12.0 and pygame 2.5.2. It ran the pure-Python solver, 200 particles, gravity and SPH enabled, the default 200 × 200 container and radius-30 obstacle, no mouse input, 300 fixed-step warmup steps, then an 8-second wall-clock sample at 30 Hz. The merged `origin/main` baseline produced 87 frames (8.07 s): median 87.745 ms, p95 104.875 ms, 696 steps (7.909/frame), and 2.1428 s of dropped simulation time. The staged wall-support candidate produced 35 frames (8.25 s): median 232.800 ms, p95 238.146 ms, 280 steps (7.778/frame), and 5.6594 s dropped. The candidate is 2.65× slower at the median than merged main and 6.98× the 33.33 ms target budget. This is a material additional performance miss, measured on the current staged source; no further Python optimization is included, consistent with the Phase 2 deferral. The full-app wall-clock result and the separate 60-second physics-only boundedness result answer different questions and must not be conflated.

The staged candidate's reproducible physics-only qualification, `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .env/bin/python scripts/qualify_sph.py --seconds 60`, ran 7,200 steps over 60 simulated seconds. It remained finite, with density at 0.3183–2.9107 times rest density, maximum speed 61.008 px/s, no obstacle penetration and zero force/velocity/timestep clamp activations. The latest rerun averaged 7.50 ms per physics step and took 54.00 wall seconds; earlier repeats took 55.20 seconds (7.67 ms/step) and 72.99 seconds (10.14 ms/step), so wall time varies while the physics metrics remained the same. This physics-only runner omits rendering and the dashboard; it does not qualify current full-app FPS. See [SPH.md](SPH.md) for wall tests and limits.

The NumPy solver remains experimental and is not a runtime dependency; `requirements.txt` is still pygame-only. An earlier 60 Hz full-app run also missed its 16.67 ms budget (median 29.82 ms, p95 45.93 ms). The pure-Python baseline was slower: 101.49 ms median frame time and 1.206 seconds dropped over about four seconds.

## References

- [Smoothed-particle hydrodynamics](https://en.wikipedia.org/wiki/Smoothed-particle_hydrodynamics)
- [Coding Adventure: Simulating Fluids — Sebastian Lague](https://youtu.be/rSKMYc1CQHE)

## Author and licence

Lucas Goddin. Contributions are accepted under the [MIT licence](LICENSE).
