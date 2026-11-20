import math
import random
import unittest

import sph
from New_Vector2D import Vector2D
from Particle import Particle
from Particle_Manager import FIXED_DT, Particle_Manager


class SPHStabilityQualificationTests(unittest.TestCase):
    def test_gravity_uses_physical_acceleration_under_reference_rate_integrator(self):
        manager = Particle_Manager(0, 0, 1, 1, 500, 400, True, False, True)
        particle = manager.particles[0]
        particle.velocity_decay = 1.0

        manager.step(FIXED_DT)

        self.assertAlmostEqual(particle.velocity.y, -10.0 * FIXED_DT)
        self.assertAlmostEqual(particle.pos.y, -10.0 * FIXED_DT**2)

    def test_mirror_boundary_samples_restore_planar_wall_density_support(self):
        particles = []
        for x_index in range(10):
            for y_index in range(-5, 6):
                particles.append(Particle(5 + 10 * x_index, 10 * y_index, 1))
        near_wall = min(particles, key=lambda p: abs(p.pos.x - 5) + abs(p.pos.y))
        interior = min(particles, key=lambda p: abs(p.pos.x - 55) + abs(p.pos.y))

        raw_density = sph.solve(particles)[0]
        boundary = sph.mirror_boundary_particles(particles, x_bounds=(0, 200))
        supported_density = sph.solve(particles, boundary_particles=boundary)[0]
        raw_ratio = raw_density[particles.index(near_wall)] / raw_density[particles.index(interior)]
        supported_ratio = supported_density[particles.index(near_wall)] / supported_density[particles.index(interior)]

        self.assertLess(raw_ratio, 0.8)
        self.assertGreater(supported_ratio, 0.9)
        self.assertLess(abs(supported_ratio - 1.0), abs(raw_ratio - 1.0))

    def test_mirror_boundary_reflects_particle_position_and_normal_velocity(self):
        particle = Particle(5, 0, 1)
        particle.velocity = Vector2D(-3, 4)

        boundary = sph.mirror_boundary_particles([particle], x_bounds=(0, 100))

        ghost = boundary[0]
        self.assertEqual((ghost.pos.x, ghost.pos.y), (-5, 0))
        self.assertEqual((ghost.velocity.x, ghost.velocity.y), (3, 4))

    def test_circular_obstacle_mirrors_restore_density_without_large_bias(self):
        particles = []
        obstacle_radius = 30.0
        contact_radius = obstacle_radius + 1.0
        for gap in (5.0, 15.0, 25.0, 35.0, 45.0, 55.0):
            radial_distance = contact_radius + gap
            count = round(2 * math.pi * radial_distance / 10.0)
            for index in range(count):
                angle = 2 * math.pi * index / count
                particles.append(Particle(
                    radial_distance * math.cos(angle),
                    radial_distance * math.sin(angle),
                    1,
                ))
        near = min(range(len(particles)), key=lambda i: (
            (math.hypot(particles[i].pos.x, particles[i].pos.y) - contact_radius - 5) ** 2
            + particles[i].pos.y**2
        ))
        interior = min(range(len(particles)), key=lambda i: (
            (math.hypot(particles[i].pos.x, particles[i].pos.y) - contact_radius - 45) ** 2
            + particles[i].pos.y**2
        ))
        obstacle = (0.0, 0.0, obstacle_radius)
        boundary = sph.mirror_boundary_particles(particles, obstacle=obstacle)
        densities = sph.solve(particles, boundary_particles=boundary)[0]

        ratio = densities[near] / densities[interior]
        self.assertGreater(ratio, 0.9)
        self.assertLess(ratio, 1.1)

    def test_circular_mirror_is_translation_and_rotation_invariant(self):
        obstacle_radius = 35.0
        particle_radius = 5.0
        pitch = 15
        contact_radius = obstacle_radius + particle_radius
        extent = math.ceil((contact_radius + 75) / pitch) * pitch
        points = [
            (x, y)
            for x in range(-extent, extent + 1, pitch)
            for y in range(-extent, extent + 1, pitch)
            if contact_radius < math.hypot(x, y) < contact_radius + 75
        ]
        angle = math.radians(37.0)

        def solve_transformed(center_x, center_y, rotation):
            cosine, sine = math.cos(rotation), math.sin(rotation)
            particles = [
                Particle(
                    center_x + cosine * x - sine * y,
                    center_y + sine * x + cosine * y,
                    particle_radius,
                )
                for x, y in points
            ]
            boundary = sph.mirror_boundary_particles(
                particles,
                obstacle=(center_x, center_y, obstacle_radius),
            )
            return particles, sph.solve(particles, boundary_particles=boundary)

        _, (base_density, _, base_forces) = solve_transformed(0.0, 0.0, 0.0)
        _, (moved_density, _, moved_forces) = solve_transformed(250.0, -180.0, angle)

        for base, moved in zip(base_density, moved_density, strict=True):
            self.assertAlmostEqual(base, moved, delta=1e-12)
        for (base_x, base_y), (moved_x, moved_y) in zip(base_forces, moved_forces, strict=True):
            rotated_x = math.cos(angle) * base_x - math.sin(angle) * base_y
            rotated_y = math.sin(angle) * base_x + math.cos(angle) * base_y
            self.assertAlmostEqual(rotated_x, moved_x, delta=1e-10)
            self.assertAlmostEqual(rotated_y, moved_y, delta=1e-10)

    def test_circle_mirror_restores_density_on_full_square_annulus(self):
        obstacle_radius = 30.0
        particle_radius = 1.0
        pitch = 10
        contact_radius = obstacle_radius + particle_radius
        extent = math.ceil((contact_radius + 75) / pitch) * pitch
        particles = [
            Particle(x, y, particle_radius)
            for x in range(-extent, extent + 1, pitch)
            for y in range(-extent, extent + 1, pitch)
            if contact_radius < math.hypot(x, y) < contact_radius + 75
        ]
        gaps = [
            math.hypot(particle.pos.x, particle.pos.y) - contact_radius
            for particle in particles
        ]
        band = pitch * 0.55
        near = [i for i, gap in enumerate(gaps) if abs(gap - 5) < band]
        interior = [i for i, gap in enumerate(gaps) if abs(gap - 45) < band]
        raw = sph.solve(particles)[0]
        boundary = sph.mirror_boundary_particles(
            particles, obstacle=(0.0, 0.0, obstacle_radius)
        )
        supported = sph.solve(particles, boundary_particles=boundary)[0]
        raw_ratio = (
            sum(raw[i] for i in near) / len(near)
            / (sum(raw[i] for i in interior) / len(interior))
        )
        supported_ratio = (
            sum(supported[i] for i in near) / len(near)
            / (sum(supported[i] for i in interior) / len(interior))
        )

        self.assertLess(abs(supported_ratio - 1.0), abs(raw_ratio - 1.0))
        self.assertGreater(supported_ratio, 0.9)
        self.assertLess(supported_ratio, 1.1)

    def test_project_default_circle_wall_support_on_square_annulus(self):
        obstacle_radius = 35.0
        particle_radius = 5.0
        pitch = 15
        contact_radius = obstacle_radius + particle_radius
        extent = math.ceil((contact_radius + 75) / pitch) * pitch
        particles = [
            Particle(x, y, particle_radius)
            for x in range(-extent, extent + 1, pitch)
            for y in range(-extent, extent + 1, pitch)
            if contact_radius < math.hypot(x, y) < contact_radius + 75
        ]
        gaps = [
            math.hypot(particle.pos.x, particle.pos.y) - contact_radius
            for particle in particles
        ]
        band = pitch * 0.55
        near = [i for i, gap in enumerate(gaps) if abs(gap - 5) < band]
        interior = [i for i, gap in enumerate(gaps) if abs(gap - 45) < band]
        raw = sph.solve(particles)[0]
        boundary = sph.mirror_boundary_particles(
            particles, obstacle=(0.0, 0.0, obstacle_radius)
        )
        supported = sph.solve(particles, boundary_particles=boundary)[0]
        raw_ratio = (
            sum(raw[i] for i in near) / len(near)
            / (sum(raw[i] for i in interior) / len(interior))
        )
        supported_ratio = (
            sum(supported[i] for i in near) / len(near)
            / (sum(supported[i] for i in interior) / len(interior))
        )

        self.assertLess(abs(supported_ratio - 1.0), abs(raw_ratio - 1.0))
        self.assertGreater(supported_ratio, 0.9)
        self.assertLess(supported_ratio, 1.1)

    def test_seeded_spawned_trajectory_is_reproducible(self):
        original_random_state = random.getstate()
        try:
            def run(seed):
                random.seed(seed)
                manager = Particle_Manager(0, 0, 0, 5, 200, 100, True, True, True)
                for _ in range(24):
                    manager.spawn_particle()
                for _ in range(60):
                    manager.step(FIXED_DT)
                return tuple(
                    (p.pos.x, p.pos.y, p.velocity.x, p.velocity.y)
                    for p in manager.particles
                )

            same_seed = run(6021)
            self.assertEqual(same_seed, run(6021))
            self.assertNotEqual(same_seed, run(6022))
        finally:
            random.setstate(original_random_state)

    def test_long_run_qualification_rejects_invalid_metrics(self):
        from scripts.qualify_sph import qualification_failures

        metrics = {
            "finite_state": True,
            "max_obstacle_penetration_px": 0.0,
            "max_speed_px_per_s": 61.0,
            "clamp_activations": {"force": 0, "velocity": 0, "dt": 0},
        }
        self.assertEqual(qualification_failures(metrics), [])
        cases = (
            ({"finite_state": False}, "non-finite state"),
            ({"max_obstacle_penetration_px": 0.01}, "obstacle penetration"),
            ({"max_speed_px_per_s": 501.0}, "speed limit"),
            ({"clamp_activations": {"force": 1, "velocity": 0, "dt": 0}}, "force clamp"),
        )
        for updates, expected in cases:
            with self.subTest(expected=expected):
                changed = {**metrics, **updates}
                failures = qualification_failures(changed)
                self.assertTrue(any(expected in failure for failure in failures))

    def test_two_second_trajectory_changes_little_when_timestep_is_halved(self):
        def make_column():
            manager = Particle_Manager(0, 0, 0, 5, 200, 100, True, True, True)
            manager.particles = [
                Particle(x, y, 5)
                for y in (-85, -70, -55, -40, -25, -10, 5, 20)
                for x in (-67.5, -52.5, -37.5, -22.5, -7.5, 7.5, 22.5, 37.5, 52.5, 67.5)
            ]
            manager.num_particles = len(manager.particles)
            manager.update_bounds(200, 100)
            return manager

        reference = make_column()
        refined = make_column()
        for _ in range(240):
            reference.step(FIXED_DT)
        for _ in range(480):
            refined.step(FIXED_DT / 2)

        position_errors = [
            math.hypot(a.pos.x - b.pos.x, a.pos.y - b.pos.y)
            for a, b in zip(reference.particles, refined.particles, strict=True)
        ]
        velocity_errors = [
            math.hypot(a.velocity.x - b.velocity.x, a.velocity.y - b.velocity.y)
            for a, b in zip(reference.particles, refined.particles, strict=True)
        ]
        self.assertLess(max(position_errors), 0.1)
        self.assertLess(max(velocity_errors), 0.1)

    def test_particle_resting_on_circle_does_not_jitter_under_gravity(self):
        manager = Particle_Manager(0, 0, 1, 5, 500, 400, True, True, True)
        manager.set_obstacle(0, 0, 35)
        particle = manager.particles[0]
        particle.pos = Vector2D(0, 40)
        particle.velocity_decay = 1.0
        for _ in range(1200):
            manager.step(FIXED_DT)

        self.assertAlmostEqual(particle.pos.x, 0.0, delta=1e-12)
        self.assertAlmostEqual(particle.pos.y, 40.0, delta=1e-12)
        self.assertAlmostEqual(math.hypot(particle.velocity.x, particle.velocity.y), 0.0, delta=1e-12)
        self.assertEqual(manager.clamp_activations["velocity"], 0)

    def test_gravity_column_has_higher_pressure_at_the_bottom(self):
        manager = Particle_Manager(0, 0, 0, 5, 200, 100, True, True, True)
        manager.particles = [
            Particle(x, y, 5)
            for y in (-85, -70, -55, -40, -25, -10, 5, 20)
            for x in (-67.5, -52.5, -37.5, -22.5, -7.5, 7.5, 22.5, 37.5, 52.5, 67.5)
        ]
        manager.num_particles = len(manager.particles)
        manager.update_bounds(200, 100)
        for _ in range(600):
            manager.step(FIXED_DT)

        layer_pressure = {}
        for particle, pressure in zip(manager.particles, manager.pressures, strict=True):
            layer = int((particle.pos.y + 100) // 25)
            layer_pressure.setdefault(layer, []).append(pressure)
        bottom = min(layer_pressure)
        top = max(layer_pressure)
        mean_bottom = sum(layer_pressure[bottom]) / len(layer_pressure[bottom])
        mean_top = sum(layer_pressure[top]) / len(layer_pressure[top])
        self.assertGreater(mean_bottom, mean_top)
        self.assertEqual(manager.clamp_activations["velocity"], 0)

    def test_default_gravity_run_stays_finite_without_velocity_guard(self):
        manager = Particle_Manager(0, 0, 200, 5, 500, 400, True, True, True)
        manager.set_obstacle(0, 0, 35)

        for _ in range(120):
            manager.step(FIXED_DT)
            state = [value for particle in manager.particles for value in (
                particle.pos.x, particle.pos.y, particle.velocity.x, particle.velocity.y
            )]
            self.assertTrue(all(math.isfinite(value) for value in state))

        self.assertEqual(manager.clamp_activations["velocity"], 0)


if __name__ == "__main__":
    unittest.main()
