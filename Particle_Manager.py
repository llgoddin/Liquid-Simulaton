from Particle import Particle
from New_Vector2D import Vector2D
import math, pygame, random

class Particle_Manager():

    def __init__(self, x, y, num_particles, radius, x_bounds, y_bounds, gravity, repulse, vertical_spawn):
        self.GRAVITY = gravity
        self.REPULSE = repulse

        self.particles = []
        self.num_particles = num_particles
        self.particle_radius = radius

        self.x, self.y = x, y

        self.X_BOUND = x_bounds
        self.Y_BOUND = y_bounds

        for _ in range(num_particles):
            self.particles.append(Particle(x=0, y=0, radius=radius))

        square = round(math.ceil(math.sqrt(num_particles)), 0)

        buffer = 10

        i = 0

        self.update_bounds(x_bounds, y_bounds)

        for x in range(square):
            for y in range(square):

                if i < len(self.particles):
                    if vertical_spawn:
                        self.particles[i].x = (buffer + radius) * x
                        self.particles[i].y = (buffer + radius) * y
                    else:
                        self.particles[i].x = (buffer + radius) * y
                        self.particles[i].y = (buffer + radius) * x
                else:
                    continue

                i += 1
    
    # Update methods
    def spawn_particle(self):

        new_particle = Particle(random.randint(-5,5), random.randint(-5,5), self.particle_radius)

        new_particle.bind_x(self.X_BOUND, -self.X_BOUND)
        new_particle.bind_y(self.Y_BOUND, -self.Y_BOUND)
        
        self.particles.append(new_particle)
        self.num_particles += 1

    def delete_particle(self):
        if len(self.particles) > 1:
            self.num_particles -= 1
            self.particles.pop()

    def increase_container_width(self):
        self.update_bounds(self.X_BOUND + 1, self.Y_BOUND)

    def decrease_container_width(self):
        self.update_bounds(self.X_BOUND - 1, self.Y_BOUND)

    def increase_container_height(self):
        self.update_bounds(self.X_BOUND, self.Y_BOUND + 1)

    def decrease_container_height(self):
        self.update_bounds(self.X_BOUND, self.Y_BOUND - 1)

    def update_bounds(self, x_bound, y_bound):
        self.X_BOUND = x_bound
        self.Y_BOUND = y_bound

        for particle in self.particles:
            particle.bind_x(x_bound, -x_bound)
            particle.bind_y(y_bound, -y_bound)
    
    def update_coordinate_grid(self, screen):
        # X_OFFSET = screen.get_width()/2
        # Y_OFFSET = -screen.get_height()/2
        
        # RENDER_X = particle.x + X_OFFSET
        # RENDER_Y = screen.get_height() - particle.y + Y_OFFSET
        return 0

    def apply_mouse_force(self, pos, negative=False):
        local_pos = (-(self.x - pos[0]), self.y - pos[1])

        for particle in self.particles:
            particle.force_towards_mouse(local_pos, negative)

    # Render Methods
    def render_bounds(self, screen):
        RENDER_X = -self.X_BOUND + self.x
        RENDER_Y = -self.Y_BOUND + self.y

        pygame.draw.rect(screen, (40, 170, 40), pygame.Rect(RENDER_X, RENDER_Y, self.X_BOUND * 2, self.Y_BOUND * 2), 3)

    def render_particle(self, screen, particle):
        RENDER_X = particle.x + self.x
        RENDER_Y = -particle.y + self.y

        pygame.draw.circle(screen, particle.color, (RENDER_X, RENDER_Y), particle.radius)

    def render_particle_influence(self, screen, particle):
        RENDER_X = particle.x + self.x
        RENDER_Y = -particle.y + self.y

        influence_color = (240, 220, 220)
        pygame.draw.circle(screen, influence_color, (RENDER_X, RENDER_Y), particle.influence_radius)
        
    def render_particle_velocity(self, screen, particle):
        RENDER_X = particle.x + self.x
        RENDER_Y = -particle.y + self.y

        if abs(particle.velocity.x) > particle.influence_radius:
            line_x = particle.influence_radius * (abs(particle.velocity.x)/particle.velocity.x)
        else:
            line_x = particle.velocity.x
        if abs(particle.velocity.y) > particle.influence_radius:
            line_y = particle.influence_radius * (abs(particle.velocity.y)/particle.velocity.y)
        else:
            line_y = particle.velocity.y

        pygame.draw.line(screen, (255, 0, 0), (RENDER_X, RENDER_Y), (RENDER_X + line_x, RENDER_Y - line_y), 2)

    def update(self, screen, dt):
        # Calculate
        for i in range(len(self.particles)):
            if self.REPULSE:
                for c in range(len(self.particles)):
                    if i == c:
                        continue

                    r_force = self.particles[i].repulsion_force(self.particles[c])

                    self.particles[i].apply_force(r_force)

            if self.GRAVITY:
                gravity = Vector2D(0, -10 * self.particles[i].mass)
                self.particles[i].apply_force(gravity)

        # Move
        for particle in self.particles:
            particle.move(dt)

        # Render Layer 1
        for particle in self.particles:
            self.render_bounds(screen)
            self.render_particle_influence(screen, particle)

        # Render Layer 2
        for particle in self.particles:
            self.render_particle_velocity(screen, particle)

        # Render Layer 3
        for particle in self.particles:
            self.render_particle(screen, particle)

    # Getters    
    def get_gravity(self):
        return self.GRAVITY

    def get_repulse(self):
        return self.REPULSE
    

    # Setters
    def set_gravity(self, value=False):
        if value == True or value == False:
            self.GRAVITY = value

    def set_repulse(self, value=False):
        if value == True or value == False:
            self.REPULSE = value
    