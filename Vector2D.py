import math

class Vector2D:
        
    def __init__(self, magnitude, direction):
        self.length = magnitude
        self.direction = math.radians(direction % 360)
        self.x = round(magnitude * math.cos(self.direction), 5)
        self.y = round(magnitude * math.sin(self.direction), 5)

    def __str__(self):
        output_string = f'{self.length} @ {math.degrees(self.direction)} Degrees'

        return output_string

    def __neg__(self):
        self.x = self.x * -1
        self.y = self.y * -1
        self.direction = math.radians(math.degrees(self.direction) + 180)

        return self

    def __add__(self, object2):
        result = Vector2D(0, 0)

        if isinstance(object2, Vector2D):
            result.x = round(self.x, 5) + round(object2.x, 5)
            result.y = round(self.y, 5) + round(object2.y, 5)
    
            mag_2 = result.x**2 + result.y**2
    
            result.length = round(math.sqrt(mag_2), 5)
    
            if result.x != 0:
                result.direction = math.atan(result.y/result.x)
            else:
                result.direction = 0


        elif isinstance(object2, int):
            result.length = self.length + object2
            result.x = round(self.length * math.cos(math.radians(self.direction)), 5)
            result.y = round(self.length * math.sin(math.radians(self.direction)), 5)
            
            if result.x != 0:
                result.direction = math.atan(result.y/result.x)
            else:
                result.direction = 0

        return result
    
    def __mul__(self, object2):
        result = Vector2D(0, 0)

        # This implimentation of vector mulitiplication is broken and needs to be updated
        if isinstance(object2, Vector2D):
            print('ERROR')
            # result.x = round(abs(self.x) * abs(object2.x), 5)
            # result.y = round(abs(self.y) * abs(object2.y), 5)

            # mag_2 = result.x**2 + result.y**2

            # result.length = round(math.sqrt(mag_2), 5)

            # if result.x != 0:
            #     result.direction = math.atan(self.y/self.x)
            # else:
            #     result.direction = 0
            
        elif isinstance(object2, int):
            result.length = self.length * object2
            result.x = round(self.length * math.cos(math.radians(self.direction)), 5)
            result.y = round(self.length * math.sin(math.radians(self.direction)), 5)

            if result.x != 0:
                result.direction = math.atan(self.y/self.x)
            else:
                result.direction = 0

        return result
            
    def __truediv__(self, object2):
        result = Vector2D(0, 0)
        
        if isinstance(object2, int):
            result.x = round(self.x / object2, 5)
            result.y = round(self.y / object2, 5)

            mag_2 = result.x**2 + result.y**2
    
            result.length = math.sqrt(mag_2)
    
            if result.x != 0:
                result.direction = math.atan(result.y/result.x)
            else:
                result.direction = 0

        return result
        

    




