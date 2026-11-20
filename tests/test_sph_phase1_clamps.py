import math
import unittest

from Particle_Manager import Particle_Manager


class PhaseOneClampTests(unittest.TestCase):
    def test_default_force_limit_is_effective(self):
        manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
        manager.particles[0].net_force.x = 100
        manager.step(1 / 120)
        self.assertAlmostEqual(manager.particles[0].velocity.x, 49.5)
        self.assertEqual(manager.clamp_activations["force"], 1)

    def test_default_velocity_limit_is_effective(self):
        manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
        manager.particles[0].velocity.x = 600
        manager.step(1 / 120)
        self.assertAlmostEqual(math.hypot(manager.particles[0].velocity.x, manager.particles[0].velocity.y), 500)
        self.assertEqual(manager.clamp_activations["velocity"], 1)

    def test_default_timestep_limit_is_one_fixed_step(self):
        manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
        manager.particles[0].velocity.x = 12
        manager.step(2 / 120)
        self.assertAlmostEqual(manager.particles[0].pos.x, 0.1)
        self.assertEqual(manager.clamp_activations["dt"], 1)

    def test_negative_timestep_is_rejected(self):
        manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
        manager.particles[0].velocity.x = 12
        manager.step(-1 / 120)
        self.assertEqual(manager.particles[0].pos.x, 0)
        self.assertEqual(manager.clamp_activations["dt"], 1)

    def test_nonfinite_timestep_is_rejected(self):
        manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
        manager.particles[0].velocity.x = 12
        manager.step(math.nan)
        self.assertEqual(manager.particles[0].pos.x, 0)
        self.assertEqual(manager.particles[0].velocity.x, 12)
        self.assertEqual(manager.clamp_activations["dt"], 1)

    def test_solver_clamps_force_velocity_and_timestep(self):
        manager = Particle_Manager(0, 0, 2, 1, 10000, 10000, False, True, True)
        manager.max_force = 1.0
        manager.max_velocity = 2.0
        manager.max_dt = 0.01
        manager.particles[0].velocity.x = 100
        manager.particles[1].velocity.x = -100
        manager.step(0.1)
        self.assertTrue(all(math.hypot(p.velocity.x, p.velocity.y) <= 2.0 + 1e-12 for p in manager.particles))
        self.assertEqual(manager.clamp_activations["force"], 2)
        self.assertEqual(manager.clamp_activations["velocity"], 2)
        self.assertEqual(manager.clamp_activations["dt"], 1)


if __name__ == "__main__":
    unittest.main()
