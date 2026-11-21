import unittest

from New_Vector2D import Vector2D
from Particle_Manager import Particle_Manager


class ObstacleTests(unittest.TestCase):
    def test_move_obstacle_clamps_center_to_container(self):
        manager = Particle_Manager(0, 0, 1, 2, 50, 40, False, False, True)
        manager.set_obstacle(0, 0, 10)
        manager.move_obstacle(100, -100)
        self.assertEqual(manager.obstacle, (40, -30, 10))

    def test_move_obstacle_clamps_after_container_shrinks(self):
        manager = Particle_Manager(0, 0, 1, 2, 50, 40, False, False, True)
        manager.set_obstacle(35, 25, 10)
        manager.update_bounds(20, 15)
        manager.move_obstacle(35, 25)
        self.assertEqual(manager.obstacle, (10, 5, 10))

    def test_move_obstacle_displaces_particle_instead_of_overlapping(self):
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, False, False, True)
        manager.set_obstacle(-30, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(0, 0)
        manager.move_obstacle(0, 0)
        self.assertGreaterEqual((particle.pos.x ** 2 + particle.pos.y ** 2) ** 0.5, 12 - 1e-9)

    def test_spawned_particle_is_resolved_from_obstacle(self):
        manager = Particle_Manager(0, 0, 0, 2, 100, 100, False, False, True)
        manager.set_obstacle(0, 0, 10)
        manager.spawn_particle()
        particle = manager.particles[0]
        self.assertGreaterEqual((particle.pos.x ** 2 + particle.pos.y ** 2) ** 0.5, 12 - 1e-9)

    def test_setting_obstacle_resolves_initial_particles_before_sph(self):
        from unittest.mock import patch
        manager = Particle_Manager(0, 0, 25, 2, 100, 100, False, True, True)
        manager.set_obstacle(0, 0, 10)
        def inspect_before_sph(particles, *args, **kwargs):
            for particle in particles:
                self.assertGreaterEqual((particle.pos.x ** 2 + particle.pos.y ** 2) ** 0.5, 12 - 1e-9)
            return [], [], [(0, 0)] * len(particles)
        with patch('sph.solve', side_effect=inspect_before_sph):
            manager.step(0)

    def test_swept_obstacle_motion_keeps_particles_in_container(self):
        manager = Particle_Manager(0, 0, 1, 2, 50, 50, False, False, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(45, 0)
        particle.velocity = Vector2D(0, 0)
        manager.move_obstacle(40, 0)
        self.assertLessEqual(abs(particle.pos.x) + particle.radius, manager.X_BOUND + 1e-9)
        self.assertLessEqual(abs(particle.pos.y) + particle.radius, manager.Y_BOUND + 1e-9)
        ox, oy, _ = manager.obstacle
        self.assertGreaterEqual(((particle.pos.x - ox) ** 2 + (particle.pos.y - oy) ** 2) ** 0.5, 12 - 1e-9)
        self.assertEqual((particle.velocity.x, particle.velocity.y), (0, 0))

    def test_corner_sweep_preserves_box_and_obstacle_exclusion(self):
        manager = Particle_Manager(0, 0, 1, 2, 50, 50, False, False, True)
        manager.set_obstacle(-30, -30, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(48, 48)
        particle.velocity = Vector2D(0, 0)
        manager.move_obstacle(40, 40)
        self.assertLessEqual(abs(particle.pos.x) + particle.radius, manager.X_BOUND + 1e-9)
        self.assertLessEqual(abs(particle.pos.y) + particle.radius, manager.Y_BOUND + 1e-9)
        ox, oy, _ = manager.obstacle
        self.assertGreaterEqual(((particle.pos.x - ox) ** 2 + (particle.pos.y - oy) ** 2) ** 0.5, 12 - 1e-9)

    def test_shrinking_bounds_reclamps_obstacle_immediately(self):
        manager = Particle_Manager(0, 0, 1, 2, 50, 40, False, False, True)
        manager.set_obstacle(35, 25, 10)
        manager.update_bounds(20, 15)
        self.assertEqual(manager.obstacle, (10, 5, 10))

    def test_particle_overlap_is_corrected_to_radius_aware_surface(self):
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, False, False, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(8, 0)
        manager.step(0)
        self.assertAlmostEqual(particle.pos.x, 12)
        self.assertAlmostEqual(particle.pos.y, 0)

    def test_inward_normal_reflects_and_tangent_is_preserved(self):
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, False, False, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(8, 0)
        particle.velocity = Vector2D(-30, 3)
        manager.step(0)
        self.assertAlmostEqual(particle.velocity.x, 27)
        self.assertAlmostEqual(particle.velocity.y, 3)

    def test_center_degeneracy_is_deterministic(self):
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, False, False, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(0, 0)
        particle.velocity = Vector2D(0, 0)
        manager.step(0)
        self.assertAlmostEqual(particle.pos.x, 12)
        self.assertAlmostEqual(particle.pos.y, 0)

    def test_resting_particle_does_not_jitter(self):
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, True, False, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(0, 12)
        particle.velocity = Vector2D(0, 0)
        for _ in range(240):
            manager.advance(1 / 120)
        self.assertAlmostEqual(particle.pos.y, 12)
        self.assertAlmostEqual(particle.velocity.y, 0)

    def test_high_speed_particle_cannot_tunnel_through(self):
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, False, True, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(0, -40)
        particle.velocity = Vector2D(0, 10000)
        manager.advance(1 / 120)
        self.assertAlmostEqual(particle.pos.y, -12)
        self.assertLessEqual(particle.velocity.y, 0)

    def test_particle_separates_from_surface_after_bounce(self):
        import math
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, False, False, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(0, -40)
        particle.velocity = Vector2D(0, 600)

        contact_radius = 10 + particle.radius
        distances = []
        for _ in range(20):
            manager.advance(1 / 120)
            distances.append(math.hypot(particle.pos.x, particle.pos.y))

        # The particle must never penetrate the obstacle.
        self.assertGreaterEqual(min(distances), contact_radius - 1e-6)
        # After the bounce it must actually leave the surface rather than being
        # captured on it: the gap must grow well beyond the contact radius.
        self.assertGreater(distances[-1], contact_radius + 5)
        self.assertLess(particle.pos.y, -20)

    def test_particle_never_penetrates_across_many_timesteps(self):
        import math
        manager = Particle_Manager(0, 0, 1, 2, 100, 100, True, False, True)
        manager.set_obstacle(0, 0, 10)
        particle = manager.particles[0]
        particle.pos = Vector2D(30, 20)
        particle.velocity = Vector2D(-50, 0)
        worst = 0
        for _ in range(600):
            manager.advance(1 / 120)
            gap = math.hypot(particle.pos.x, particle.pos.y) - (10 + particle.radius)
            worst = min(worst, gap)
        self.assertGreaterEqual(worst, -1e-9)


class ObstacleRenderTests(unittest.TestCase):
    def test_obstacle_is_drawn_at_its_world_position(self):
        import os
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        import pygame
        pygame.init()
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))
        manager = Particle_Manager(400, 300, 1, 2, 100, 100, False, False, True)
        manager.set_obstacle(0, 0, 30)
        manager.render_obstacle(surface)
        self.assertEqual(surface.get_at((400, 300))[:3], (110, 110, 110))
        self.assertEqual(surface.get_at((420, 300))[:3], (110, 110, 110))
        self.assertEqual(surface.get_at((431, 300))[:3], (0, 0, 0))

    def test_main_loop_fits_a_visible_obstacle_inside_the_container(self):
        import os
        import runpy
        from unittest.mock import patch

        import pygame

        class Clock:
            def tick(self, fps): pass
            def get_fps(self): return 120

        managers = []
        def make_manager(**kwargs):
            manager = Particle_Manager(0, 0, 1, 1, 100, 100, False, False, True)
            managers.append(manager)
            return manager

        with patch.dict(os.environ, {'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}), \
             patch('pygame.time.Clock', return_value=Clock()), \
             patch('pygame.event.get', side_effect=[[], [pygame.event.Event(pygame.QUIT)]]), \
             patch('time.monotonic', side_effect=[1, 1 + 1 / 120]), \
             patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
            runpy.run_path('Graphics.py', run_name='__main__')

        obstacle = managers[0].obstacle
        self.assertIsNotNone(obstacle)
        x, y, radius = obstacle
        self.assertEqual((x, y), (0, 0))
        self.assertGreater(radius, 0)
        self.assertLess(radius, managers[0].X_BOUND)
        self.assertLess(radius, managers[0].Y_BOUND)
