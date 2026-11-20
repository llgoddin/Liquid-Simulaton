"""Run a deterministic fixed-step SPH stability qualification scenario."""

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Particle_Manager import FIXED_DT, MAX_VELOCITY, Particle_Manager  # noqa: E402


def qualification_failures(metrics):
    """Return failed bounded-run criteria; do not infer physical accuracy."""
    failures = []
    if not metrics.get("finite_state", False):
        failures.append("non-finite state")
    if metrics.get("max_obstacle_penetration_px", math.inf) > 1e-9:
        failures.append("obstacle penetration")
    if metrics.get("max_speed_px_per_s", math.inf) >= MAX_VELOCITY:
        failures.append("speed limit reached")
    for name, count in metrics.get("clamp_activations", {}).items():
        if count:
            failures.append(f"{name} clamp activation")
    return failures


def run(seconds):
    manager = Particle_Manager(
        0, 0, 200, 5, 500, 400, True, True, True
    )
    manager.set_obstacle(0, 0, 35)
    steps = round(seconds / FIXED_DT)
    min_density_ratio = math.inf
    max_density_ratio = 0.0
    max_speed = 0.0
    max_obstacle_penetration = 0.0
    finite = True
    started = time.perf_counter()

    for _ in range(steps):
        manager.step(FIXED_DT)
        ratios = [density / manager.sph_rest_density for density in manager.densities]
        finite = finite and all(math.isfinite(value) for value in (
            *ratios, *manager.pressures
        ))
        min_density_ratio = min(min_density_ratio, min(ratios))
        max_density_ratio = max(max_density_ratio, max(ratios))
        max_speed = max(
            max_speed,
            max(math.hypot(p.velocity.x, p.velocity.y) for p in manager.particles),
        )
        max_obstacle_penetration = max(
            max_obstacle_penetration,
            max(
                max(
                    0.0,
                    35 + particle.radius
                    - math.hypot(particle.pos.x, particle.pos.y),
                )
                for particle in manager.particles
            ),
        )
        finite = finite and all(
            math.isfinite(value)
            for particle in manager.particles
            for value in (
                particle.pos.x,
                particle.pos.y,
                particle.velocity.x,
                particle.velocity.y,
            )
        )

    wall_seconds = time.perf_counter() - started
    return {
        "scenario": "deterministic 200-particle constructor lattice; gravity and SPH on; circular obstacle",
        "simulated_seconds": steps * FIXED_DT,
        "physics_steps": steps,
        "wall_seconds": wall_seconds,
        "mean_step_ms": wall_seconds * 1000 / steps,
        "finite_state": finite,
        "density_over_rest_min": min_density_ratio,
        "density_over_rest_max": max_density_ratio,
        "max_speed_px_per_s": max_speed,
        "max_obstacle_penetration_px": max_obstacle_penetration,
        "clamp_activations": manager.clamp_activations,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=60.0)
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    result = run(args.seconds)
    failures = qualification_failures(result)
    result["qualification_pass"] = not failures
    result["failed_criteria"] = failures
    print(json.dumps(result, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
