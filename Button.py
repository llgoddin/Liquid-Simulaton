import pygame

from GUI_Element import GUI_Element


class Button(GUI_Element):
    def __init__(self, x, y, width=100, height=100, color=(0, 0, 200), text='Button 1', active=False, function_str='None'):
        super().__init__(x, y, width, height, color, function_str)

        self.text = text

        self.active = active

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

        pygame.draw.rect(screen, self.color, pygame.Rect(self.parent_x + self.x, self.parent_y + self.y, self.width, self.height))

        screen.blit(my_text, text_rect)

    def set_clicked(self, value):
        if self.clicked != value:
            self.clicked = value
            if value is True:
                self.active = False if self.active else True

    def get_clicked(self):
        return self.clicked

    def get_active(self):
        return self.active
