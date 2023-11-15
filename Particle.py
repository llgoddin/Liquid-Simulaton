from New_Vector2D import Vector2D
import math

class Particle():
    def __init__(self, x, y, radius):
        self.MAX_X = None
        self.MIN_X = None
        self.MAX_Y = None
        self.MIN_Y = None

        self.mass = 100
        self.bounciness = .9

        self.influence_radius = 50

        self.net_force = Vector2D(0, 0)

        self.velocity = Vector2D(0, 0)
        self.acceleration = Vector2D(0, 0)

        self.velocity_decay = .99

        self.x = x
        self.y = y

        self.radius = radius
        self.color = (0, 0, 255)

    def __str__(self):
        return f'Coords = ({self.x}, {self.y}) V = ({self.velocity}), A = ({self.acceleration})'

    def move(self, dt, verbose=False):
        self.acceleration = self.net_force / self.mass

        self.net_force = Vector2D(0, 0)

        if verbose:
            print(self)

        self.velocity = self.velocity + self.acceleration

        self.x += self.velocity.x * dt
        self.y += self.velocity.y * dt

        self.velocity.x = self.velocity.x * self.velocity_decay
        self.velocity.y = self.velocity.y * self.velocity_decay

        self.check_bounds()

        if verbose:
            print(self)

    def bind_x(self, max, min):
        self.MAX_X = max
        self.MIN_X = min

    def bind_y(self, max, min):
        self.MAX_Y = max
        self.MIN_Y = min

    def check_bounds(self):
        BOUNCE = True

        if self.MAX_Y and self.y > self.MAX_Y:
            if BOUNCE:

                self.velocity.y = self.velocity.y * -1 * self.bounciness
            self.y = self.MAX_Y

        elif self.MIN_Y and self.y < self.MIN_Y:
            if BOUNCE:
                self.velocity.y = self.velocity.y * -1 * self.bounciness
            self.y = self.MIN_Y


        if self.MAX_X and self.x > self.MAX_X:
            if BOUNCE:
                self.velocity.x = self.velocity.x * -1 * self.bounciness
            self.x = self.MAX_X

        elif self.MIN_X and self.x < self.MIN_X:
            if BOUNCE:
                self.velocity.x = self.velocity.x * -1 * self.bounciness
            self.x = self.MIN_X

    def repulsion_force(self, object2):
        MAX_FORCE = 10
        FORCE_MULTIPLIER = 5

        dist = self.get_distance(object2)

        x_dist = self.x - object2.x
        y_dist = self.y - object2.y

        if y_dist != 0:
            y_direc = y_dist/abs(y_dist)
        else:
            y_direc = 0

        if x_dist != 0:
            x_direc = x_dist/abs(x_dist)
        else:
            x_direc = 0

        if (dist > self.influence_radius):
            return Vector2D(0,0)

        force_value = (self.influence_radius * 2 - dist) * FORCE_MULTIPLIER

        r_force = Vector2D(force_value * x_direc, force_value * y_direc)

        return r_force

    def force_towards_mouse(self, pos, negative=False):
        MOUSE_FORCE = 1000

        mouse_pos = Vector2D(pos[0], pos[1])
        my_pos = Vector2D(self.x, self.y)

        x_dist = self.x - pos[0]
        y_dist = self.y - pos[1]

        if y_dist != 0:
            y_direc = y_dist/abs(y_dist)
        else:
            y_direc = 0

        if x_dist != 0:
            x_direc = x_dist/abs(x_dist)
        else:
            x_direc = 0

        force = -Vector2D(MOUSE_FORCE * x_direc, MOUSE_FORCE * y_direc)
        
        if negative:
            force = -force

        self.apply_force(force)

    def get_distance(self, object2):
        x = self.x - object2.x
        y = self.y - object2.y

        return math.sqrt(x**2 + y**2)

    def apply_force(self, force_vector):
        self.net_force = self.net_force + force_vector



    
        
