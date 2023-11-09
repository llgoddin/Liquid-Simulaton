from Vector2D import Vector2D

class Particle():
    def __init__(self, x, y, radius):
        self.MAX_X = None
        self.MIN_X = None
        self.MAX_Y = None
        self.MIN_Y = None

        self.mass = 1

        self.velocity = Vector2D(0, 0)

        self.x = x
        self.y = y

        self.radius = radius
        self.color = (0, 0, 255)
       

    def move(self, dt):

        grav_accel = Vector2D(9.81, 180)

        self.x += self.velocity.x * dt
        self.y += self.velocity.y * dt
        
        if self.MAX_X and self.x > self.MAX_X:
            self.x = self.MAX_X
        elif self.MIN_X and self.x < self.MIN_X:
            self.x = self.MIN_X


        if self.MAX_Y and self.y > self.MAX_X:
            self.y = self.MAX_Y
        elif self.MIN_Y and self.y < self.MIN_Y:
            self.y = self.MIN_Y

    def bind_x(self, max, min):
        self.MAX_X = max
        self.MIN_X = min

    def bind_y(self, max, min):
        self.MAX_Y = max
        self.MIN_Y = min

    def accelerate(self, acc_vector):
        self.velocity.x += acc_vector.x
        self.velocity.y += acc_vector.y


    
        
