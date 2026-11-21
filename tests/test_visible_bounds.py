import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame  # noqa: E402

from Particle_Manager import Particle_Manager  # noqa: E402


class VisibleBoundsTests(unittest.TestCase):
    def test_default_view_draws_one_outline_at_container_edges(self):
        manager = Particle_Manager(300, 250, 2, 5, 90, 70, False, True, True)
        surface = pygame.Surface((800, 600))
        rectangles = []
        with patch('pygame.draw.rect', side_effect=lambda *args, **kwargs: rectangles.append(args)):
            manager.render(surface, debug=False)
        self.assertEqual(len(rectangles), 1)
        self.assertEqual(rectangles[0][2], pygame.Rect(210, 180, 180, 140))
        self.assertGreater(rectangles[0][3], 0)


if __name__ == '__main__':
    unittest.main()
