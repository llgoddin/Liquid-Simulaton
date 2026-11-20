import math
import unittest

import sph
from New_Vector2D import Vector2D
from Particle import Particle


class KernelTests(unittest.TestCase):
    def test_poly6_is_normalized_over_two_dimensional_support(self):
        h = 2.0
        steps = 20000
        dr = h / steps
        integral = sum(2 * math.pi * (i + 0.5) * dr * sph.poly6(i * dr, h) * dr for i in range(steps))
        self.assertAlmostEqual(integral, 1.0, delta=1e-4)

    def test_kernels_are_zero_at_and_outside_support(self):
        for kernel in (sph.poly6, sph.spiky, sph.viscosity_laplacian):
            self.assertEqual(kernel(3.0, 3.0), 0.0)
            self.assertEqual(kernel(4.0, 3.0), 0.0)

    def test_spiky_gradient_matches_finite_difference(self):
        x, y, h, epsilon = 4.0, 3.0, 10.0, 1e-5
        gx, gy = sph.spiky_gradient(x, y, h)
        dx = (sph.spiky(math.hypot(x + epsilon, y), h) - sph.spiky(math.hypot(x - epsilon, y), h)) / (2 * epsilon)
        dy = (sph.spiky(math.hypot(x, y + epsilon), h) - sph.spiky(math.hypot(x, y - epsilon), h)) / (2 * epsilon)
        self.assertAlmostEqual(gx, dx, places=10)
        self.assertAlmostEqual(gy, dy, places=10)


class SolverTests(unittest.TestCase):
    def particles(self, positions, masses=None):
        masses = masses or [1.0] * len(positions)
        result = []
        for (x, y), mass in zip(positions, masses, strict=True):
            p = Particle(x, y, 1)
            p.mass = mass
            result.append(p)
        return result

    def test_density_includes_self_and_unequal_neighbor_mass(self):
        particles = self.particles([(0, 0), (2, 0)], [2, 3])
        rho, pressure, forces = sph.solve(particles, h=5, rest_density=1)
        self.assertAlmostEqual(rho[0], 2 * sph.poly6(0, 5) + 3 * sph.poly6(2, 5))
        self.assertAlmostEqual(rho[1], 3 * sph.poly6(0, 5) + 2 * sph.poly6(2, 5))
        self.assertTrue(all(p >= 0 for p in pressure))
        self.assertEqual(forces, [(0.0, 0.0), (0.0, 0.0)])

    def test_compressed_pair_has_symmetric_repulsive_pressure_forces(self):
        particles = self.particles([(0, 0), (2, 1)])
        _, pressure, forces = sph.solve(particles, h=10, rest_density=0.001, stiffness=10, viscosity=0)
        self.assertGreater(pressure[0], 0)
        self.assertLess(forces[0][0], 0)
        self.assertLess(forces[0][1], 0)
        self.assertAlmostEqual(forces[0][0], -forces[1][0])
        self.assertAlmostEqual(forces[0][1], -forces[1][1])

    def test_viscosity_reduces_relative_velocity_without_net_force(self):
        particles = self.particles([(0, 0), (1, 0)])
        particles[0].velocity = Vector2D(-1, 0)
        particles[1].velocity = Vector2D(1, 0)
        _, _, forces = sph.solve(particles, h=4, rest_density=100, viscosity=1)
        self.assertGreater(forces[0][0], 0)
        self.assertAlmostEqual(forces[0][0], -forces[1][0])

    def test_coincident_particles_have_finite_forces(self):
        particles = self.particles([(0, 0), (0, 0)])
        rho, pressure, forces = sph.solve(particles, h=4)
        self.assertTrue(all(math.isfinite(v) for v in rho + pressure + [c for f in forces for c in f]))


class IntegrationTests(unittest.TestCase):
    def test_manager_applies_sph_forces_from_a_shared_snapshot(self):
        from Particle_Manager import Particle_Manager

        manager = Particle_Manager(0, 0, 2, 1, 1000, 1000, False, True, True)
        manager.particles[0].pos = Vector2D(0, 0)
        manager.particles[1].pos = Vector2D(10, 0)
        manager.sph_h = 30
        manager.sph_rest_density = 0.00001
        manager.sph_stiffness = 100
        manager.sph_viscosity = 0
        manager.step(1 / 120)
        self.assertLess(manager.particles[0].pos.x, manager.particles[1].pos.x)
        self.assertAlmostEqual(manager.particles[0].velocity.x, -manager.particles[1].velocity.x, places=10)
        self.assertTrue(all(math.isfinite(p.pos.x) and math.isfinite(p.velocity.x) for p in manager.particles))

    def test_repulse_disabled_preserves_non_sph_motion(self):
        from Particle_Manager import Particle_Manager

        manager = Particle_Manager(0, 0, 2, 1, 1000, 1000, False, False, True)
        manager.step(1 / 120)
        self.assertEqual([p.pos.x for p in manager.particles], [0, 0])
