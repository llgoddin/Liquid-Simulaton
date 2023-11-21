from GUI_Element import GUI_Element
import pygame

class Button(GUI_Element):
    def __init__(self, x, y, width=100, height=100, color=(0, 0, 200), text='Button 1', active=False, function_str='None'):
        super().__init__(x, y, width, height, color, function_str)

        self.text = text

        self.active = active

    def render(self, screen):

        my_font = pygame.font.Font('freesansbold.ttf', 15)
        my_text = my_font.render(f'{self.text}', True, (255, 255, 255))

        text_rect = my_text.get_rect()

        text_rect.center = (self.parent_x + self.x + self.width / 2, self.parent_y + self.y + self.height / 2)

        pygame.draw.rect(screen, self.color, pygame.Rect(self.parent_x + self.x, self.parent_y + self.y, self.width, self.height))
        
        screen.blit(my_text, text_rect)

    def set_clicked(self, value):
        if self.clicked != value:
            self.clicked = value
            if value == True:
                self.active = False if self.active else True

    def get_clicked(self):
        return self.clicked            

    def get_active(self):
        return self.active