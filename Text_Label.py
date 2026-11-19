import pygame

from GUI_Element import GUI_Element


class Text_Label(GUI_Element):
    def __init__(self, x, y, width, height, color, text='Label 1', function_str='None'):
        super().__init__(x, y, width, height, color, function_str)

        self.text = text

    def render(self, screen):
        if not hasattr(self, '_text_font'):
            self._text_font = pygame.font.Font('freesansbold.ttf', 15)
        text = f'{self.text}'
        if getattr(self, '_rendered_text', None) != text:
            self._text_surface = self._text_font.render(text, True, (255, 255, 255))
            self._rendered_text = text
        my_text = self._text_surface

        text_rect = my_text.get_rect()

        text_rect.center = (self.parent_x + self.x + self.width / 2, self.parent_y + self.y + self.height / 2)
        screen.blit(my_text, text_rect)

    def set_text(self, text):
        self.text = text

    def get_clicked(self):
        return True


