import os
import unittest
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
from Button import Button
from Text_Label import Text_Label


class DashboardTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_repeated_render_does_not_reload_font(self):
        original = pygame.font.Font
        for cls in (Button, Text_Label):
            with self.subTest(widget=cls.__name__), patch('pygame.font.Font', wraps=original) as font:
                widget = cls(1, 2, 100, 30, (0, 0, 200), text='hello')
                screen = pygame.Surface((160, 80))
                for _ in range(4):
                    widget.render(screen)
                self.assertLessEqual(font.call_count, 1)

    def test_unchanged_text_is_not_rasterized_again(self):
        original = pygame.font.Font
        for cls in (Button, Text_Label):
            with self.subTest(widget=cls.__name__):
                real_font = original('freesansbold.ttf', 15)
                from unittest.mock import Mock
                font = Mock(wraps=real_font)
                with patch('pygame.font.Font', return_value=font):
                    widget = cls(1, 2, 100, 30, (0, 0, 200), text='hello')
                    screen = pygame.Surface((160, 80))
                    widget.render(screen)
                    widget.render(screen)
                    self.assertEqual(font.render.call_count, 1)
                    widget.text = 'changed'
                    widget.render(screen)
                    self.assertEqual(font.render.call_count, 2)
                    widget.render(screen)
                    self.assertEqual(font.render.call_count, 2)

    def test_pixels_match_original_render_for_updates_and_distinct_styles(self):
        for cls in (Button, Text_Label):
            widgets = [cls(3, 5, 100, 30, (0, 0, 200), text='Gravity'),
                       cls(12, 8, 127, 38, (80, 30, 200), text='Repulse')]
            widgets[0].set_parent_coords((7, 4))
            widgets[1].set_parent_coords((2, 9))
            for value in ('FPS: 1', 'FPS: 1', 'Particles: 200', '', 42):
                for index, widget in enumerate(widgets):
                    value = value if index == 0 else f'other {value}'
                    if isinstance(widget, Text_Label):
                        widget.set_text(value)
                    else:
                        widget.text = value
                    actual = pygame.Surface((180, 100))
                    expected = pygame.Surface((180, 100))
                    actual.fill((13, 14, 15))
                    expected.fill((13, 14, 15))
                    font = pygame.font.Font('freesansbold.ttf', 15)
                    text = font.render(f'{value}', True, (255, 255, 255))
                    rect = text.get_rect()
                    rect.center = (widget.parent_x + widget.x + widget.width / 2,
                                   widget.parent_y + widget.y + widget.height / 2)
                    if isinstance(widget, Button):
                        pygame.draw.rect(expected, widget.color, pygame.Rect(
                            widget.parent_x + widget.x, widget.parent_y + widget.y,
                            widget.width, widget.height))
                    expected.blit(text, rect)
                    widget.render(actual)
                    self.assertEqual(pygame.image.tostring(actual, 'RGBA'),
                                     pygame.image.tostring(expected, 'RGBA'))
