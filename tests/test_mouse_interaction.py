import unittest

from Particle_Manager import Particle_Manager


class MouseInteractionTests(unittest.TestCase):
    def test_radius_limits_force_with_continuous_falloff(self):
        manager = Particle_Manager(0, 0, 1, 1, 1000, 1000, False, False, True)
        manager.mouse_radius = 100
        particle = manager.particles[0]
        forces = []
        for distance in (50, 99.999, 100, 101):
            particle.net_force.x = particle.net_force.y = 0
            manager.apply_mouse_force((distance, 0))
            forces.append(particle.net_force.x)
        self.assertGreater(forces[0], forces[1])
        self.assertGreater(forces[1], 0)
        self.assertLess(forces[1], 0.001)
        self.assertEqual(forces[2:], [0, 0])

    def test_force_follows_arbitrary_bearing(self):
        manager = Particle_Manager(0, 0, 1, 1, 1000, 1000, False, False, True)
        particle = manager.particles[0]
        manager.apply_mouse_force((30, -40))
        self.assertAlmostEqual(particle.net_force.x / particle.net_force.y, 30 / 40)
        self.assertGreater(particle.net_force.x, 0)
        self.assertGreater(particle.net_force.y, 0)

    def test_zero_distance_produces_no_force(self):
        manager = Particle_Manager(0, 0, 1, 1, 1000, 1000, False, False, True)
        particle = manager.particles[0]
        manager.apply_mouse_force((0, 0))
        self.assertEqual((particle.net_force.x, particle.net_force.y), (0, 0))

    def test_only_particles_inside_radius_are_affected(self):
        manager = Particle_Manager(0, 0, 2, 1, 1000, 1000, False, False, True)
        manager.mouse_radius = 100
        near, far = manager.particles
        far.pos.x = 500
        manager.apply_mouse_force((50, 0))
        self.assertGreater(near.net_force.x, 0)
        self.assertEqual((far.net_force.x, far.net_force.y), (0, 0))

    def test_strength_is_signed_and_scales_linearly(self):
        weak = Particle_Manager(0, 0, 1, 1, 1000, 1000, False, False, True)
        strong = Particle_Manager(0, 0, 1, 1, 1000, 1000, False, False, True)
        strong.mouse_strength = weak.mouse_strength * 3
        weak.apply_mouse_force((60, 0))
        strong.apply_mouse_force((60, 0))
        self.assertAlmostEqual(strong.particles[0].net_force.x,
                               3 * weak.particles[0].net_force.x)
        repel = Particle_Manager(0, 0, 1, 1, 1000, 1000, False, False, True)
        repel.apply_mouse_force((60, 0), negative=True)
        self.assertAlmostEqual(repel.particles[0].net_force.x,
                               -weak.particles[0].net_force.x)

    def test_radius_and_strength_are_tunable_after_construction(self):
        manager = Particle_Manager(0, 0, 1, 1, 1000, 1000, False, False, True)
        particle = manager.particles[0]
        probe = (120, 0)
        manager.mouse_radius = 100
        manager.apply_mouse_force(probe)
        self.assertEqual((particle.net_force.x, particle.net_force.y), (0, 0))
        manager.mouse_radius = 200
        manager.apply_mouse_force(probe)
        at_200 = particle.net_force.x
        self.assertGreater(at_200, 0)
        manager.mouse_radius = 400
        particle.net_force.x = particle.net_force.y = 0
        manager.apply_mouse_force(probe)
        self.assertGreater(particle.net_force.x, at_200)

    def test_mouse_force_is_time_weighted_across_partitions(self):
        from Particle_Manager import FIXED_DT
        mouse = ((80, 0), False)
        results = []
        for partitions in (12, (4, 3, 5), (1,) * 12):
            manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
            if partitions == 12:
                for _ in range(12):
                    manager.advance(FIXED_DT, [mouse])
            else:
                for count in partitions:
                    for _ in range(count):
                        manager.advance(FIXED_DT, [mouse])
            p = manager.particles[0]
            results.append((p.pos.x, p.velocity.x))
        for pos, vel in results[1:]:
            self.assertAlmostEqual(pos, results[0][0])
            self.assertAlmostEqual(vel, results[0][1])

    def test_influence_ring_is_rendered_at_cursor(self):
        import os
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
        from unittest.mock import patch

        import pygame
        manager = Particle_Manager(0, 0, 1, 1, 1000, 1000, False, False, True)
        manager.mouse_radius = 123
        surface = pygame.Surface((800, 600))
        manager.apply_mouse_force((321, 250))
        calls = []
        with patch('pygame.draw.circle', side_effect=lambda *a, **k: calls.append(a)):
            manager.render(surface)
        ring = [c for c in calls if c[2] == (321, 250) and c[3] == 123]
        self.assertEqual(len(ring), 1)
