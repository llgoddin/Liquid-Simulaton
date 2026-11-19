"""Phase 1: debug overlays behind a toggle, and the bounds redraw fix.

Roadmap requirement:
  "The debug overlays are behind a toggle, so the default view is the
   simulation rather than the diagnostics."

The three diagnostics are the 50 px influence disc, the red velocity line
and the container rectangle. The rectangle was also drawn once per *particle*
per frame (it sat inside the per-particle loop); it must be drawn once per
frame.
"""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame  # noqa: E402

from Particle_Manager import Particle_Manager  # noqa: E402

INFLUENCE_COLOR = (240, 220, 220)
BOUNDS_COLOR = (40, 170, 40)
OBSTACLE_FILL = (110, 110, 110)
OBSTACLE_EDGE = (40, 40, 40)
RING_COLOR = (120, 120, 255)


class DebugOverlayRenderTests(unittest.TestCase):
    """Render() places the diagnostics behind a flag."""

    def setUp(self):
        pygame.display.init()
        self.surface = pygame.Surface((800, 600))

    def _capture(self, manager, **kwargs):
        circles, lines, rects = [], [], []
        with patch('pygame.draw.circle', side_effect=lambda *a, **k: circles.append(a)), \
             patch('pygame.draw.line', side_effect=lambda *a, **k: lines.append(a)), \
             patch('pygame.draw.rect', side_effect=lambda *a, **k: rects.append(a)):
            manager.render(self.surface, **kwargs)
        return circles, lines, rects

    def test_default_view_draws_only_particles(self):
        manager = Particle_Manager(0, 0, 3, 5, 100, 100, False, False, True)
        circles, lines, rects = self._capture(manager)
        # Every circle is a particle body; no influence disc.
        self.assertEqual(len(circles), 3)
        self.assertTrue(all(call[3] == 5 for call in circles), circles)
        self.assertEqual(lines, [])
        self.assertEqual(rects, [])

    def test_default_view_ignores_explicit_false(self):
        manager = Particle_Manager(0, 0, 2, 5, 100, 100, False, False, True)
        circles, lines, rects = self._capture(manager, debug=False)
        self.assertEqual(len(circles), 2)
        self.assertEqual(lines, [])
        self.assertEqual(rects, [])

    def test_debug_view_draws_all_diagnostics(self):
        manager = Particle_Manager(0, 0, 3, 5, 100, 100, False, False, True)
        circles, lines, rects = self._capture(manager, debug=True)
        influence = [c for c in circles if c[1] == INFLUENCE_COLOR]
        bodies = [c for c in circles if c[1] == (0, 0, 255)]
        self.assertEqual(len(influence), 3)
        self.assertEqual(len(bodies), 3)
        self.assertEqual(len(lines), 3)
        self.assertEqual(len(rects), 1)

    def test_bounds_rect_drawn_once_per_frame_not_per_particle(self):
        manager = Particle_Manager(0, 0, 25, 5, 100, 100, False, False, True)
        _, _, rects = self._capture(manager, debug=True)
        self.assertEqual(len(rects), 1)
        self.assertEqual(rects[0][1], BOUNDS_COLOR)

    def test_obstacle_and_mouse_ring_are_not_diagnostics(self):
        # The obstacle and the mouse influence ring are part of the simulation,
        # so the default view still draws them. Only the container rectangle,
        # the influence disc and the velocity line are diagnostics.
        manager = Particle_Manager(0, 0, 3, 5, 100, 100, False, False, True)
        manager.set_obstacle(0, 0, 30)
        manager.mouse_pos = (0.0, 0.0)
        manager.mouse_radius = 50.0
        circles, lines, rects = self._capture(manager)
        colours = [call[1] for call in circles]
        self.assertIn(OBSTACLE_FILL, colours)
        self.assertIn(OBSTACLE_EDGE, colours)
        self.assertIn(RING_COLOR, colours)
        # The default view still carries no diagnostics.
        self.assertEqual(lines, [])
        self.assertEqual(rects, [])


class DebugToggleIntegrationTests(unittest.TestCase):
    """The keyboard toggle sits on the main (fixed-step) loop."""

    def _run_frames(self, frames, key):
        import runpy
        from unittest.mock import patch

        from Particle_Manager import Particle_Manager

        class Clock:
            def tick(self, fps): pass
            def get_fps(self): return 120

        rendered = []

        def make_manager(**kwargs):
            manager = Particle_Manager(0, 0, 1, 1, 100, 100, False, False, True)

            def record(screen=None, debug=False):
                rendered.append(debug)

            manager.render = record
            return manager

        events = []
        for kind in frames:
            if kind == 'keydown':
                events.append([pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode='')])
            elif kind == 'quit':
                events.append([pygame.event.Event(pygame.QUIT)])
            else:
                events.append([])

        with patch.dict(os.environ, {'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}), \
             patch('pygame.time.Clock', return_value=Clock()), \
             patch('pygame.event.get', side_effect=events), \
             patch('pygame.mouse.get_pos', return_value=(0, 0)), \
             patch('time.monotonic', side_effect=[1 + i / 120 for i in range(len(events) + 1)]), \
             patch('Particle_Manager.Particle_Manager', side_effect=make_manager):
            runpy.run_path('Graphics.py', run_name='__main__')
        return rendered

    def test_first_frame_is_simulation_only(self):
        # The QUIT frame still runs the loop body once, so it renders too.
        rendered = self._run_frames(['none', 'quit'], key=pygame.K_d)
        self.assertEqual(rendered, [False, False])

    def test_debug_key_toggles_overlays_on_and_off(self):
        rendered = self._run_frames(
            ['none', 'keydown', 'none', 'keydown', 'quit'],
            key=pygame.K_d,
        )
        self.assertEqual(rendered, [False, True, True, False, False])


if __name__ == '__main__':
    unittest.main()
