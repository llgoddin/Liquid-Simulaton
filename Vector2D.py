import math

class Vector2D:
        
    def __init__(self, magnitude, direction):
        self.magnitude = magnitude
        self.direction = math.radians(direction % 360)
        self.x = magnitude * math.sin(math.radians(direction))
        self.y = magnitude * math.cos(math.radians(direction))

    def __str__(self):
        output_string = f'{self.magnitude} @ {math.degrees(self.direction)} Degrees'

        return output_string

    def __add__(self, object2):
        result = Vector2D(0, 0)

        if isinstance(object2, Vector2D):
            result.x = self.x + object2.x
            result.y = self.y + object2.y
    
            mag_2 = result.x**2 + result.y**2
    
            result.magnitude = math.sqrt(mag_2)
    
            if result.x != 0:
                result.direction = math.atan(result.y/result.x)
            else:
                result.direction = 0


        elif isinstance(object2, int):
            result.magnitude = self.magnitude + object2
            result.x = self.magnitude * math.sin(math.radians(self.direction))
            result.y = self.magnitude * math.cos(math.radians(self.direction))
            
            if result.x != 0:
                result.direction = math.atan(result.y/result.x)
            else:
                result.direction = 0


        return result
    
    def __mul__(self, object2):
        if isinstance(object2, Vector2D):
            self.x = math.abs(self.x) * math.abs(object2.x)
            self.y = math.abs(self.y) * math.abs(object2.y)

            mag_2 = self.x**2 + self.y**2

            self.magnitude = math.sqrt(mag_2)

            if self.x != 0:
                self.direction = math.atan(self.y/self.x)
            else:
                self.direction = 0
            
        elif isinstance(object2, int):
            self.magnitude = self.magnitude * int
            self.x = self.magnitude * math.sin(math.radians(self.direction))
            self.y = self.magnitude * math.cos(math.radians(self.direction))

            if self.x != 0:
                self.direction = math.atan(self.y/self.x)
            else:
                self.direction = 0
            

        

    




