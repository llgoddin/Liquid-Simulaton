"""Compare circular SPH wall images on/off in a deterministic drop test."""

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sph  # noqa: E402
from Particle import Particle  # noqa: E402
from Particle_Manager import FIXED_DT, Particle_Manager  # noqa: E402


def run(seconds, include_obstacle_ghosts):
    manager = Particle_Manager(0, 0, 0, 5, 500, 400, True, True, True)
    manager.particles = [
        Particle(x, y, 5)
        for y in range(80, 300, 11)
        for x in range(-55, 55, 11)
    ]
    manager.num_particles = len(manager.particles)
    manager.update_bounds(500, 400)
    manager.set_obstacle(0, 0, 35)
    steps = round(seconds / FIXED_DT)
    original_mirror = sph.mirror_boundary_particles

    if not include_obstacle_ghosts:
        def mirror_container_only(particles, x_bounds=None, y_bounds=None,
                                  obstacle=None, h=sph.H):
            return original_mirror(
                particles, x_bounds=x_bounds, y_bounds=y_bounds,
                obstacle=None, h=h,
            )
        sph.mirror_boundary_particles = mirror_container_only

    started = time.perf_counter()
    finite = True
    max_penetration = 0.0
    max_speed = 0.0
    try:
        for _ in range(steps):
            manager.step(FIXED_DT)
            for particle, density, pressure in zip(
                manager.particles, manager.densities, manager.pressures, strict=True
            ):
                finite = finite and math.isfinite(density) and math.isfinite(pressure)
                finite = finite and all(math.isfinite(value) for value in (
                    particle.pos.x, particle.pos.y,
                    particle.velocity.x, particle.velocity.y,
                ))
                max_speed = max(
                    max_speed,
                    math.hypot(particle.velocity.x, particle.velocity.y),
                )
                max_penetration = max(
                    max_penetration,
                    max(0.0, 35 + particle.radius
                        - math.hypot(particle.pos.x, particle.pos.y)),
                )
    finally:
        sph.mirror_boundary_particles = original_mirror
    wall_seconds = time.perf_counter() - started

    near, far = [], []
    for particle, density in zip(manager.particles, manager.densities, strict=True):
        gap = math.hypot(particle.pos.x, particle.pos.y) - (35 + particle.radius)
        ratio = density / manager.sph_rest_density
        if 0 <= gap < manager.sph_h:
            near.append(ratio)
        elif gap >= manager.sph_h and abs(particle.pos.x) < 400 and abs(particle.pos.y) < 300:
            far.append(ratio)

    return {
        "obstacle_ghosts": include_obstacle_ghosts,
        "simulated_seconds": steps * FIXED_DT,
        "steps": steps,
        "wall_seconds": wall_seconds,
        "near_wall_count": len(near),
        "near_wall_density_over_rest_min": min(near) if near else None,
        "near_wall_density_over_rest_mean": sum(near) / len(near) if near else None,
        "near_wall_density_over_rest_max": max(near) if near else None,
        "interior_count": len(far),
        "interior_density_over_rest_mean": sum(far) / len(far) if far else None,
        "max_speed_px_per_s": max_speed,
        "max_obstacle_penetration_px": max_penetration,
        "clamp_activations": manager.clamp_activations,
        "finite_state": finite,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    print(json.dumps({
        "scenario": "200 particles released above a radius-35 circular obstacle; gravity and SPH on",
        "without_obstacle_ghosts": run(args.seconds, False),
        "with_obstacle_ghosts": run(args.seconds, True),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
