
class GUI_Element():
    def __init__(self, x=0, y=0, width=100, height=100, color=(255, 0, 0)):
        self.x, self.y = x, y
        self.parent_x, self.parent_y = 0, 0

        self.width, self.height = width, height

        self.color = color

        self.clicked = False

    def contains(self, pos):
        if pos[0] - (self.parent_x + self.x) < self.width and pos[0] - (self.parent_x + self.x) >= 0:
            if pos[1] - (self.parent_y + self.y) < self.height and pos[1] - (self.parent_y + self.y) >= 0:
                return True
        
        return False
    
    def set_clicked(self, value):
        if self.clicked != value:
            self.clicked = value
            print(f'Set Clicked to {value}')

    def set_parent_x(self, value):
        self.parent_x = value

    def set_parent_y(self, value):
        self.parent_y = value

    def set_parent_coords(self, value):
        self.parent_x = value[0]
        self.parent_y = value[1]

    def render(self, screen):
        return 0
