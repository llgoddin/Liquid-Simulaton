from GUI_Element import GUI_Element
import pygame

class Text_Label(GUI_Element):
    def __init__(self, x, y, width, height, color, text='Label 1', function_str='None'):
        super().__init__(x, y, width, height, color, function_str)

        self.text = text

    def render(self, screen):
        my_font = pygame.font.Font('freesansbold.ttf', 15)
        my_text = my_font.render(f'{self.text}', True, (255, 255, 255))

        text_rect = my_text.get_rect()

        text_rect.center = (self.parent_x + self.x + self.width / 2, self.parent_y + self.y + self.height / 2)
        screen.blit(my_text, text_rect)

    def set_text(self, text):
        self.text = text

    def get_clicked(self):
        return True
    

