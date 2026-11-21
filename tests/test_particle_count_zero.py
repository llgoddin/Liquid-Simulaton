import unittest

from Particle_Manager import Particle_Manager


class ParticleCountTests(unittest.TestCase):
    def test_removal_can_reach_zero_and_is_safe_when_empty(self):
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, False, True, True)
        manager.delete_particle()
        self.assertEqual(manager.num_particles, 0)
        self.assertEqual(manager.particles, [])
        manager.delete_particle()
        self.assertEqual(manager.num_particles, 0)
        manager.advance(1 / 120)
        self.assertEqual(manager.particles, [])

    def test_model_is_not_limited_to_the_interactive_cap(self):
        manager = Particle_Manager(0, 0, 201, 2, 1000, 1000, False, False, True)
        self.assertEqual(manager.num_particles, 201)
        self.assertEqual(len(manager.particles), 201)


if __name__ == '__main__':
    unittest.main()
