"""Measure circular SPH wall support on radial and square sample layouts."""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sph  # noqa: E402
from Particle import Particle  # noqa: E402

DEFAULT_OBSTACLE_RADIUS = 35.0
DEFAULT_PARTICLE_RADIUS = 5.0
DEFAULT_PITCH = 15.0


def compare(particles, near_indices, interior_indices, obstacle_radius):
    raw, _, raw_forces = sph.solve(particles)
    ghosts = sph.mirror_boundary_particles(
        particles, obstacle=(0.0, 0.0, obstacle_radius)
    )
    supported, _, forces = sph.solve(particles, boundary_particles=ghosts)
    raw_near = sum(raw[i] for i in near_indices) / len(near_indices)
    raw_interior = sum(raw[i] for i in interior_indices) / len(interior_indices)
    supported_near = sum(supported[i] for i in near_indices) / len(near_indices)
    supported_interior = sum(supported[i] for i in interior_indices) / len(interior_indices)
    return {
        "particle_count": len(particles),
        "ghost_count": len(ghosts),
        "near_sample_count": len(near_indices),
        "interior_sample_count": len(interior_indices),
        "raw_near_to_interior_density_ratio": raw_near / raw_interior,
        "ghost_near_to_interior_density_ratio": supported_near / supported_interior,
        "ghost_near_radial_force_mean": sum(
            (forces[i][0] * particles[i].pos.x
             + forces[i][1] * particles[i].pos.y)
            / math.hypot(particles[i].pos.x, particles[i].pos.y)
            for i in near_indices
        ) / len(near_indices),
        "raw_near_radial_force_mean": sum(
            (raw_forces[i][0] * particles[i].pos.x
             + raw_forces[i][1] * particles[i].pos.y)
            / math.hypot(particles[i].pos.x, particles[i].pos.y)
            for i in near_indices
        ) / len(near_indices),
    }


def radial_rings(obstacle_radius, particle_radius, pitch):
    contact_radius = obstacle_radius + particle_radius
    particles = []
    for gap in (5.0, 15.0, 25.0, 35.0, 45.0, 55.0):
        radius = contact_radius + gap
        count = round(2 * math.pi * radius / pitch)
        for index in range(count):
            angle = 2 * math.pi * index / count
            particles.append(Particle(
                radius * math.cos(angle), radius * math.sin(angle), particle_radius
            ))
    near = min(range(len(particles)), key=lambda i: (
        (math.hypot(particles[i].pos.x, particles[i].pos.y)
         - contact_radius - 5) ** 2 + particles[i].pos.y ** 2
    ))
    interior = min(range(len(particles)), key=lambda i: (
        (math.hypot(particles[i].pos.x, particles[i].pos.y)
         - contact_radius - 45) ** 2 + particles[i].pos.y ** 2
    ))
    return compare(particles, [near], [interior], obstacle_radius)


def square_annulus(obstacle_radius, particle_radius, pitch):
    contact_radius = obstacle_radius + particle_radius
    extent = int(math.ceil((contact_radius + 75) / pitch) * pitch)
    particles = [
        Particle(x, y, particle_radius)
        for x in range(-extent, extent + 1, int(pitch))
        for y in range(-extent, extent + 1, int(pitch))
        if contact_radius < math.hypot(x, y) < contact_radius + 75
    ]
    gaps = [math.hypot(p.pos.x, p.pos.y) - contact_radius for p in particles]
    band = pitch * 0.55
    near = [i for i, gap in enumerate(gaps) if abs(gap - 5) < band]
    interior = [i for i, gap in enumerate(gaps) if abs(gap - 45) < band]
    return compare(particles, near, interior, obstacle_radius)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    default = (DEFAULT_OBSTACLE_RADIUS, DEFAULT_PARTICLE_RADIUS, DEFAULT_PITCH)
    small = (30.0, 1.0, 10.0)
    print(json.dumps({
        "project_default_geometry": {
            "obstacle_radius": default[0],
            "particle_radius": default[1],
            "pitch": default[2],
            "h": sph.H,
            "radial_ring": radial_rings(*default),
            "square_annulus": square_annulus(*default),
        },
        "small_particle_stress_geometry": {
            "obstacle_radius": small[0],
            "particle_radius": small[1],
            "pitch": small[2],
            "h": sph.H,
            "radial_ring": radial_rings(*small),
            "square_annulus": square_annulus(*small),
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
