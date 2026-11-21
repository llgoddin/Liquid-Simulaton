import os
import runpy
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame  # noqa: E402

from Particle_Manager import Particle_Manager  # noqa: E402


class SimulatorControlIntegrationTests(unittest.TestCase):
    def run_frames(self, frames, position, start_count=1):
        class Clock:
            def tick(self, fps):
                pass

            def get_fps(self):
                return 10

        managers = []
        def make_manager(**kwargs):
            kwargs['num_particles'] = start_count
            manager = Particle_Manager(**kwargs)
            manager.step = lambda dt: None
            managers.append(manager)
            return manager

        with patch('pygame.time.Clock', return_value=Clock()), \
             patch('pygame.event.get', side_effect=frames), \
             patch('pygame.mouse.get_pos', return_value=position), \
             patch('time.monotonic', side_effect=[1 + i / 10 for i in range(len(frames))]), \
             patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
            runpy.run_path('Graphics.py', run_name='__main__')
        return managers[0]

    def test_default_scene_starts_with_a_visible_group_of_particles(self):
        observed = []
        class Clock:
            def tick(self, fps):
                pass

            def get_fps(self):
                return 120

        def make_manager(**kwargs):
            observed.append(kwargs['num_particles'])
            return Particle_Manager(**kwargs)

        with patch('pygame.time.Clock', return_value=Clock()), \
             patch('pygame.event.get', return_value=[pygame.event.Event(pygame.QUIT)]), \
             patch('time.monotonic', return_value=1), \
             patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
            runpy.run_path('Graphics.py', run_name='__main__')
        self.assertGreaterEqual(observed[0], 25)
        self.assertLessEqual(observed[0], 200)

    def test_sph_is_active_without_mouse_gestures(self):
        manager = self.run_frames([[pygame.event.Event(pygame.QUIT)]], (0, 0))
        self.assertTrue(manager.REPULSE)

    def test_mouse_toggle_does_not_disable_sph_and_disables_mouse_force(self):
        class Clock:
            def tick(self, fps):
                pass

            def get_fps(self):
                return 120

        managers, inputs = [], []
        def make_manager(**kwargs):
            manager = Particle_Manager(**kwargs)
            manager.advance = lambda dt, forces=(): inputs.append(list(forces))
            managers.append(manager)
            return manager

        frames = [
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(620, 160))],
            [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(620, 160))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 300))],
            [],
            [pygame.event.Event(pygame.QUIT)],
        ]
        with patch('pygame.time.Clock', return_value=Clock()), \
             patch('pygame.event.get', side_effect=frames), \
             patch('pygame.mouse.get_pos', return_value=(400, 300)), \
             patch('time.monotonic', side_effect=[1 + i / 120 for i in range(len(frames))]), \
             patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
            runpy.run_path('Graphics.py', run_name='__main__')
        self.assertTrue(managers[0].REPULSE)
        self.assertTrue(all(not forces for forces in inputs))

    def test_dragging_obstacle_and_dragging_fluid_are_distinct(self):
        class Clock:
            def tick(self, fps):
                pass

            def get_fps(self):
                return 120

        moves, inputs = [], []
        def make_manager(**kwargs):
            manager = Particle_Manager(**kwargs)
            manager.advance = lambda dt, forces=(): inputs.append(list(forces))
            def move(x, y):
                moves.append((x, y))
                manager.obstacle = (x, y, manager.obstacle[2])
            manager.move_obstacle = move
            return manager

        frames = [
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(300, 300))],
            [pygame.event.Event(pygame.MOUSEMOTION, pos=(380, 300), rel=(80, 0), buttons=(1, 0, 0))],
            [pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(380, 300))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 300))],
            [],
            [pygame.event.Event(pygame.QUIT)],
        ]
        with patch('pygame.time.Clock', return_value=Clock()), \
             patch('pygame.event.get', side_effect=frames), \
             patch('pygame.mouse.get_pos', return_value=(200, 300)), \
             patch('time.monotonic', side_effect=[1 + i / 120 for i in range(len(frames))]), \
             patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
            runpy.run_path('Graphics.py', run_name='__main__')
        self.assertEqual(moves, [(80, 0)])
        self.assertFalse(any(inputs[1:3]))
        self.assertIn(((200, 300), False), inputs[4])

    def test_mouse_force_radius_and_container_controls_change_their_values(self):
        quit_event = pygame.event.Event(pygame.QUIT)
        for position, attribute, expected in [
            ((715, 210), 'mouse_strength', 11),
            ((715, 310), 'mouse_radius', 160),
            ((620, 310), 'X_BOUND', 101),
            ((620, 410), 'Y_BOUND', 101),
        ]:
            with self.subTest(control=attribute):
                down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)
                up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=position)
                manager = self.run_frames([[down], [up], [quit_event]], position)
                self.assertEqual(getattr(manager, attribute), expected)

    def test_count_hold_repeats_slowly_and_stops_on_release(self):
        down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
        up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1)
        quit_event = pygame.event.Event(pygame.QUIT)
        manager = self.run_frames([[down], [], [], [], [], [], [up], [], [], [quit_event]], (620, 210))
        self.assertEqual(manager.num_particles, 3)

    def test_queued_additions_check_cap_when_they_execute(self):
        class Clock:
            def tick(self, fps):
                pass

            def get_fps(self):
                return 240

        managers = []
        def make_manager(**kwargs):
            kwargs['num_particles'] = 199
            manager = Particle_Manager(**kwargs)
            manager.step = lambda dt: None
            managers.append(manager)
            return manager

        down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(620, 210))
        up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(620, 210))
        frames = [[], [down, up, down], [], [up], [pygame.event.Event(pygame.QUIT)]]
        with patch('pygame.time.Clock', return_value=Clock()), \
             patch('pygame.event.get', side_effect=frames), \
             patch('pygame.mouse.get_pos', return_value=(620, 210)), \
             patch('time.monotonic', side_effect=[1 + i / 240 for i in range(len(frames))]), \
             patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
            runpy.run_path('Graphics.py', run_name='__main__')
        self.assertEqual(managers[0].num_particles, 200)
        self.assertEqual(len(managers[0].particles), 200)

    def test_queued_interactive_additions_never_exceed_200(self):
        down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
        up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1)
        quit_event = pygame.event.Event(pygame.QUIT)
        manager = self.run_frames([[down], [], [], [], [], [], [], [up], [quit_event]], (620, 210), 199)
        self.assertEqual(manager.num_particles, 200)


if __name__ == '__main__':
    unittest.main()
