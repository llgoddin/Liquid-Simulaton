from Particle import Particle
from New_Vector2D import Vector2D
import math, pygame

class Particle_Manager():

    def __init__(self, num_particles, radius, x_bounds, y_bounds, gravity, repulse, vertical_spawn):
        self.GRAVITY = gravity
        self.REPULSE = repulse
        self.particles = []
        
        for _ in range(num_particles):
            self.particles.append(Particle(x=0, y=0, radius=radius))

        square = round(math.ceil(math.sqrt(num_particles)), 0)

        buffer = 10

        i = 0

        for x in range(square):
            for y in range(square):

                if i < len(self.particles):
                    self.particles[i].bind_x(x_bounds, -x_bounds)
                    self.particles[i].bind_y(y_bounds, -y_bounds)

                    if vertical_spawn:
                        self.particles[i].x = (buffer + radius) * x
                        self.particles[i].y = (buffer + radius) * y
                    else:
                        self.particles[i].x = (buffer + radius) * y
                        self.particles[i].y = (buffer + radius) * x
                else:
                    continue

                i += 1
    
    def render_particle(self, screen, particle):
        X_OFFSET = screen.get_width()/2
        Y_OFFSET = -screen.get_height()/2
        
        RENDER_X = particle.x + X_OFFSET
        RENDER_Y = screen.get_height() - particle.y + Y_OFFSET

        pygame.draw.circle(screen, particle.color, (RENDER_X, RENDER_Y), particle.radius)

    def render_particle_influence(self, screen, particle):
        X_OFFSET = screen.get_width()/2
        Y_OFFSET = -screen.get_height()/2
        
        RENDER_X = particle.x + X_OFFSET
        RENDER_Y = screen.get_height() - particle.y + Y_OFFSET

        influence_color = (240, 220, 220)
        pygame.draw.circle(screen, influence_color, (RENDER_X, RENDER_Y), particle.influence_radius)
        
    def render_particle_velocity(self, screen, particle):
        X_OFFSET = screen.get_width()/2
        Y_OFFSET = -screen.get_height()/2
        
        RENDER_X = particle.x + X_OFFSET
        RENDER_Y = screen.get_height() - particle.y + Y_OFFSET

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
        X_OFFSET = screen.get_width()/2
        Y_OFFSET = -screen.get_height()/2

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
            self.render_particle_influence(screen, particle)

        # Render Layer 2
        for particle in self.particles:
            self.render_particle_velocity(screen, particle)

        # Render Layer 3
        for particle in self.particles:
            self.render_particle(screen, particle)
        