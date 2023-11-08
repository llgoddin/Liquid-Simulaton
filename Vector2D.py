import math

class Vector2D:
        
    def __init__(self, magnitude, direction):
        self.magnitude = magnitude
        self.direction = direction % 360
        self.x_vel = magnitude * math.sin(math.radians(direction))
        self.y_vel = magnitude * math.cos(math.radians(direction))

    def __add__(self, object2):
        if isinstance(object2, Vector2D):
            self.x_vel = self.x_vel + object2.x_vel
            self.y_vel = self.y_vel + object2.y_vel
    
            mag_2 = self.x_vel**2 + self.y_vel**2
    
            self.magnitude = math.sqrt(mag_2)
    
            self.direction = math.atan(self.y_vel/self.x_vel)

        elif isinstance(object2, int):
            self.magnitude = self.magnitude + object2
            self.x_vel = self.magnitude * math.sin(math.radians(self.direction))
            self.y_vel = self.magnitude * math.cos(math.radians(self.direction))
            self.direction = math.atan(self.y_vel/self.x_vel)


        

    def __mul__(self, object2):
        if isinstance(object2, Vector2D):
            self.x_vel = math.abs(self.x_vel) * math.abs(object2.x_vel)
            self.y_vel = math.abs(self.y_vel) * math.abs(object2.y_vel)

            mag_2 = self.x_vel**2 + self.y_vel**2

            self.magnitude = math.sqrt(mag_2)

            self.direction = math.atan(self.y_vel/self.x_vel)

        elif isinstance(object2, int):
            self.magnitude = self.magnitude * int
            self.x_vel = self.magnitude * math.sin(math.radians(self.direction))
            self.y_vel = self.magnitude * math.cos(math.radians(self.direction))
            self.direction = math.atan(self.y_vel/self.x_vel)
            

        

    




