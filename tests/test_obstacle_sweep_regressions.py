import math
import unittest

from New_Vector2D import Vector2D
from Particle_Manager import Particle_Manager


class ObstacleSweepRegressionTests(unittest.TestCase):
    def test_open_sweep_pushes_a_particle_ahead_of_the_obstacle(self):
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, False, False, True)
        manager.set_obstacle(-30, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(0, 0)
        manager.move_obstacle(30, 0)
        self.assertGreaterEqual(particle.pos.x, 42 - 1e-9)
        self.assertGreaterEqual(math.hypot(particle.pos.x - 30, particle.pos.y), 12 - 1e-9)

    def test_shrinking_box_clamps_unrelated_particle_to_nearest_wall(self):
        manager = Particle_Manager(0, 0, 1, 2, 50, 50, False, False, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(40, 40)
        manager.update_bounds(30, 30)
        self.assertAlmostEqual(particle.pos.x, 28)
        self.assertAlmostEqual(particle.pos.y, 28)

    def test_obstacle_can_reach_the_actual_box_edge(self):
        manager = Particle_Manager(0, 0, 1, 2, 50, 40, False, False, True)
        manager.set_obstacle(0, 0, 10)
        manager.move_obstacle(100, -100)
        self.assertEqual(manager.obstacle, (40, -30, 10))


if __name__ == '__main__':
    unittest.main()
