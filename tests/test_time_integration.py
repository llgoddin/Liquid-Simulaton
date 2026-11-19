import unittest

from New_Vector2D import Vector2D
from Particle import Particle


class FixedStepTests(unittest.TestCase):
    def test_near_boundary_stall_never_exceeds_step_cap(self):
        from Particle_Manager import FIXED_DT, MAX_SUBSTEPS, Particle_Manager
        manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
        # Pin the velocity-weighted (distance-independent) force so this
        # timestep test does not depend on the radial falloff profile.
        manager.mouse_radius = float('inf')
        particle = manager.particles[0]
        particle.velocity_decay = 1
        before = FIXED_DT - 1.000002e-12
        self.assertEqual(manager.advance(before), 0)
        applied = []
        manager.queue_control(lambda: applied.append('once'))
        self.assertEqual(manager.advance(FIXED_DT * MAX_SUBSTEPS, [((10000, 0), False)]), MAX_SUBSTEPS)
        self.assertEqual(applied, ['once'])
        self.assertAlmostEqual(manager.accumulator, before, places=11)
        self.assertAlmostEqual(manager.dropped_time, 0)
        self.assertAlmostEqual(particle.velocity.x, 70, places=7)
        self.assertEqual(manager.advance(2e-12), 1)
        self.assertAlmostEqual(particle.velocity.x, 80, places=7)
        self.assertEqual(applied, ['once'])

    def test_control_queue_is_bounded_fifo_and_drains_at_boundary(self):
        from Particle_Manager import FIXED_DT, MAX_PENDING_CONTROLS, Particle_Manager
        manager = Particle_Manager(0, 0, 1, 1, 100, 100, False, False, True)
        observed = []
        manager.advance(FIXED_DT / 2)
        for i in range(MAX_PENDING_CONTROLS):
            self.assertTrue(manager.queue_control(lambda i=i: observed.append(i)))
        self.assertFalse(manager.queue_control(lambda: observed.append('rejected')))
        self.assertEqual(manager.rejected_controls, 1)
        self.assertEqual(observed, [])
        manager.advance(FIXED_DT * 2.5)
        self.assertEqual(observed, list(range(MAX_PENDING_CONTROLS)))
        self.assertEqual(len(manager.pending_controls), 0)
        self.assertTrue(manager.queue_control(lambda: observed.append('immediate')))
        self.assertEqual(observed[-1], 'immediate')

    @staticmethod
    def recording_step(snapshots, manager):
        original_step = manager.step
        def record_step(dt):
            snapshots.append((manager.GRAVITY, manager.num_particles, manager.X_BOUND))
            original_step(dt)
        return record_step

    def test_dashboard_changes_wait_for_fractional_step_boundary(self):
        import os
        import runpy
        from unittest.mock import patch

        import pygame

        from Particle_Manager import Particle_Manager

        class Clock:
            def tick(self, fps): pass
            def get_fps(self): return 240

        snapshots = []
        for position, old, new in [
            ((620, 110), (True, 1, 100), (False, 1, 100)),
            ((620, 210), (True, 1, 100), (True, 2, 100)),
            ((620, 310), (True, 1, 100), (True, 1, 101)),
        ]:
            with self.subTest(position=position):
                snapshots.clear()
                def make_manager(**kwargs):
                    manager = Particle_Manager(0, 0, 1, 1, 100, 100, True, False, True)
                    manager.step = self.recording_step(snapshots, manager)
                    return manager
                frames = [[], [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)],
                          [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1)],
                          [], [], [], [pygame.event.Event(pygame.QUIT)]]
                with patch.dict(os.environ, {'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}), \
                     patch('pygame.time.Clock', return_value=Clock()), \
                     patch('pygame.event.get', side_effect=frames), \
                     patch('pygame.mouse.get_pos', return_value=position), \
                     patch('time.monotonic', side_effect=[1 + i / 240 for i in range(len(frames))]), \
                     patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
                    runpy.run_path('Graphics.py', run_name='__main__')
                self.assertEqual(snapshots, [old, new, new])

    def test_dashboard_changes_do_not_rewrite_elapsed_steps(self):
        import os
        import runpy
        from unittest.mock import patch

        import pygame

        from Particle_Manager import Particle_Manager

        class Clock:
            def tick(self, fps): pass
            def get_fps(self): return 120

        snapshots = []
        for position, old, new in [
            ((620, 110), (True, 1, 100), (False, 1, 100)),
            ((620, 210), (True, 1, 100), (True, 2, 100)),
            ((620, 310), (True, 1, 100), (True, 1, 101)),
        ]:
            with self.subTest(position=position):
                snapshots.clear()
                def make_manager(**kwargs):
                    manager = Particle_Manager(0, 0, 1, 1, 100, 100, True, False, True)
                    manager.step = self.recording_step(snapshots, manager)
                    return manager
                frames = [[], [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)],
                          [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1)],
                          [pygame.event.Event(pygame.QUIT)]]
                with patch.dict(os.environ, {'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}), \
                     patch('pygame.time.Clock', return_value=Clock()), \
                     patch('pygame.event.get', side_effect=frames), \
                     patch('pygame.mouse.get_pos', return_value=position), \
                     patch('time.monotonic', side_effect=[1 + i / 120 for i in range(4)]), \
                     patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
                    runpy.run_path('Graphics.py', run_name='__main__')
                self.assertEqual(snapshots, [old, new, new])

    def run_mouse_frames(self, frames):
        import os
        import runpy
        from unittest.mock import patch

        import pygame

        from Particle_Manager import Particle_Manager

        class Clock:
            def tick(self, fps): pass
            def get_fps(self): return 240

        frames = [[pygame.event.Event(kind, button=1)] if kind else [] for kind in frames]
        frames.append([pygame.event.Event(pygame.QUIT)])
        managers = []
        def make_manager(**kwargs):
            manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
            manager.mouse_radius = float('inf')
            managers.append(manager)
            return manager

        with patch.dict(os.environ, {'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}), \
             patch('pygame.time.Clock', return_value=Clock()), \
             patch('pygame.event.get', side_effect=frames), \
             patch('pygame.mouse.get_pos', return_value=(100, 0)), \
             patch('time.monotonic', side_effect=[1 + i / 240 for i in range(len(frames))]), \
             patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
            runpy.run_path('Graphics.py', run_name='__main__')
        return managers[0].particles[0].velocity.x

    def test_short_click_through_main_loop_is_not_overapplied(self):
        import pygame
        velocity = self.run_mouse_frames([None, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, None])
        self.assertAlmostEqual(velocity, 5 * .99 * .99)

    def test_short_click_through_main_loop_is_not_lost(self):
        import pygame
        velocity = self.run_mouse_frames([None, None, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, None])
        self.assertAlmostEqual(velocity, 5 * .99)

    def test_fractional_backlog_survives_capped_stall(self):
        from Particle_Manager import FIXED_DT, MAX_SUBSTEPS, Particle_Manager
        manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
        manager.mouse_radius = float('inf')
        particle = manager.particles[0]
        particle.velocity_decay = 1
        self.assertEqual(manager.advance(FIXED_DT / 2, [((100, 0), False)]), 0)
        self.assertEqual(manager.advance(1), MAX_SUBSTEPS)
        self.assertAlmostEqual(manager.dropped_time, 1 - MAX_SUBSTEPS * FIXED_DT)
        self.assertAlmostEqual(manager.accumulator, FIXED_DT / 2)
        self.assertAlmostEqual(particle.velocity.x, 5)
        self.assertEqual(manager.advance(FIXED_DT / 2), 1)
        self.assertAlmostEqual(particle.velocity.x, 5)
        self.assertAlmostEqual(manager.accumulator, 0)

    def test_stall_is_capped_and_dropped_time_recorded(self):
        from Particle_Manager import FIXED_DT, MAX_SUBSTEPS, Particle_Manager
        manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, True, False, True)
        self.assertEqual(manager.advance(1), MAX_SUBSTEPS)
        self.assertAlmostEqual(manager.dropped_time, 1 - MAX_SUBSTEPS * FIXED_DT)
        self.assertEqual(manager.advance(0), 0)

    def test_mouse_force_is_applied_per_simulation_step(self):
        from Particle_Manager import Particle_Manager
        results = []
        for fps in (30, 60, 120, 240):
            manager = Particle_Manager(0, 0, 1, 1, 10000, 10000, False, False, True)
            manager.mouse_radius = float('inf')
            for _ in range(fps):
                manager.advance(1 / fps, [((10000, 0), False)])
            results.append((manager.particles[0].pos.x, manager.particles[0].velocity.x))
        for position, velocity in results[1:]:
            self.assertAlmostEqual(position, results[0][0])
            self.assertAlmostEqual(velocity, results[0][1])

    def test_reference_step_matches_original_order(self):
        particle = Particle(0, 0, 1)
        particle.velocity = Vector2D(7, 0)
        particle.apply_force(Vector2D(10, 0))
        particle.move(1 / 120)
        self.assertAlmostEqual(particle.pos.x, 17 / 120)
        self.assertAlmostEqual(particle.velocity.x, 17 * .99)

    def test_render_schedules_produce_same_particle_state(self):
        import Particle_Manager
        self.assertTrue(hasattr(Particle_Manager.Particle_Manager, 'advance'))
        states = []
        for fps in (30, 60, 120, 240):
            manager = Particle_Manager.Particle_Manager(0, 0, 1, 1, 10000, 10000, True, False, True)
            for _ in range(fps):
                manager.advance(1 / fps)
            p = manager.particles[0]
            states.append((p.pos.y, p.velocity.y))
        for position, velocity in states[1:]:
            self.assertAlmostEqual(position, states[0][0])
            self.assertAlmostEqual(velocity, states[0][1])


class ParticleTimeTests(unittest.TestCase):
    def test_damping_depends_on_elapsed_time(self):
        particle = Particle(0, 0, 1)
        particle.velocity = Vector2D(100, 0)
        particle.move(1 / 240)
        self.assertAlmostEqual(particle.velocity.x, 100 * 0.99 ** 0.5)

    def test_half_reference_step_scales_acceleration_once(self):
        particle = Particle(0, 0, 1)
        particle.velocity_decay = 1
        particle.apply_force(Vector2D(12, 0))
        particle.move(1 / 240)
        self.assertAlmostEqual(particle.velocity.x, 6)
        self.assertAlmostEqual(particle.pos.x, 6 / 240)


if __name__ == '__main__':
    unittest.main()
