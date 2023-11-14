import pygame
from GUI_Element import GUI_Element

class Dashboard(GUI_Element):
    def __init__(self, x, y, width, height):
        super().__init__()

        self.x, self.y = x, y
        self.width, self.height = width, height

        self.color = (100, 100, 100)
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)

        element.set_parent_coords((self.x, self.y))

    def get_elements(self):
        return self.elements

    def check_click(self, pos):
        for element in self.elements:
            element.set_clicked(element.contains(pos))

    def reset_clicked_elements(self):
        for element in self.elements:
            element.set_clicked(False)

    def render(self, screen):
        #draw background first
        pygame.draw.rect(screen, self.color, pygame.Rect(self.x, self.y, self.width, self.height))

        for element in self.elements:
            element.render(screen)
