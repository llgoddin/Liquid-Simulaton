from Particle import Particle
from New_Vector2D import Vector2D
import math, pygame, random
from collections import deque

FIXED_DT = 1 / 120
MAX_SUBSTEPS = 8
MAX_PENDING_CONTROLS = 256
# Per-step gravity impulse at the reference rate (|a| * FIXED_DT * 120 = 10).
# A contact whose inward normal speed does not exceed this is treated as a
# resting contact: the inward component is removed rather than reflected, so a
# particle sitting on the obstacle does not jitter. Genuine impacts exceed it.
REST_SPEED = 10.0

class Particle_Manager():

    def __init__(self, x, y, num_particles, radius, x_bounds, y_bounds, gravity, repulse, vertical_spawn):
        self.GRAVITY = gravity
        self.REPULSE = repulse
        self.accumulator = 0.0
        self.dropped_time = 0.0
        self.pending_controls = deque()
        self.rejected_controls = 0
        self.obstacle = None

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
                        self.particles[i].pos.x = (buffer + radius) * x
                        self.particles[i].pos.y = (buffer + radius) * y
                    else:
                        self.particles[i].pos.x = (buffer + radius) * y
                        self.particles[i].pos.y = (buffer + radius) * x
                else:
                    continue

                i += 1
    
    # Update methods
    def set_obstacle(self, x, y, radius):
        self.obstacle = (x, y, radius)

    def resolve_obstacle(self, particle, previous_pos):
        if self.obstacle is None:
            return
        x, y, radius = self.obstacle
        contact_radius = radius + particle.radius

        # Swept test: find the first point along this step's motion where the
        # particle surface reaches the obstacle surface, so a fast particle
        # cannot pass through between two samples.
        sx, sy = previous_pos.x - x, previous_pos.y - y
        ex, ey = particle.pos.x - x, particle.pos.y - y
        dx, dy = ex - sx, ey - sy
        a = dx * dx + dy * dy
        hit_t = None
        if a > 0:
            b = 2 * (sx * dx + sy * dy)
            c = sx * sx + sy * sy - contact_radius * contact_radius
            if c <= 0:
                # Already touching or penetrating at the start of the step.
                # Treat it as a contact unless the step carries the particle
                # outward off the surface (c == 0 and moving away): a departing
                # particle must not be re-pinned to the surface, or it can
                # never separate after a bounce.
                if b < 0 or c < 0:
                    hit_t = 0.0
            else:
                discriminant = b * b - 4 * a * c
                if discriminant >= 0:
                    root = math.sqrt(discriminant)
                    t = (-b - root) / (2 * a)
                    if 0 <= t <= 1:
                        hit_t = t
        elif sx * sx + sy * sy < contact_radius * contact_radius:
            hit_t = 0.0  # stationary inside the obstacle

        if hit_t is None:
            return

        cx = sx + hit_t * dx
        cy = sy + hit_t * dy
        distance = math.hypot(cx, cy)
        nx, ny = (cx / distance, cy / distance) if distance else (1, 0)
        particle.pos = Vector2D(x + nx * contact_radius, y + ny * contact_radius)

        normal_speed = particle.velocity.x * nx + particle.velocity.y * ny
        if normal_speed < 0:
            if -normal_speed > REST_SPEED:
                normal_speed *= -particle.bounciness
            else:
                normal_speed = 0.0
            tangent = particle.velocity.x * (-ny) + particle.velocity.y * nx
            particle.velocity = Vector2D(normal_speed * nx - tangent * ny,
                                         normal_speed * ny + tangent * nx)

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
        
        # RENDER_X = particle.pos.x + X_OFFSET
        # RENDER_Y = screen.get_height() - particle.pos.y + Y_OFFSET
        return 0

    def apply_mouse_force(self, pos, negative=False, weight=1.0):
        local_pos = (-(self.x - pos[0]), self.y - pos[1])

        for particle in self.particles:
            particle.force_towards_mouse(local_pos, negative, weight)

    # Render Methods
    def render_bounds(self, screen):
        RENDER_X = -self.X_BOUND + self.x
        RENDER_Y = -self.Y_BOUND + self.y

        pygame.draw.rect(screen, (40, 170, 40), pygame.Rect(RENDER_X, RENDER_Y, self.X_BOUND * 2, self.Y_BOUND * 2), 3)

    def render_obstacle(self, screen):
        if self.obstacle is None:
            return
        x, y, radius = self.obstacle

        RENDER_X = x + self.x
        RENDER_Y = -y + self.y

        pygame.draw.circle(screen, (110, 110, 110), (RENDER_X, RENDER_Y), radius)
        pygame.draw.circle(screen, (40, 40, 40), (RENDER_X, RENDER_Y), radius, 3)

    def render_particle(self, screen, particle):
        RENDER_X = particle.pos.x + self.x
        RENDER_Y = -particle.pos.y + self.y

        pygame.draw.circle(screen, particle.color, (RENDER_X, RENDER_Y), particle.radius)

    def render_particle_influence(self, screen, particle):
        RENDER_X = particle.pos.x + self.x
        RENDER_Y = -particle.pos.y + self.y

        influence_color = (240, 220, 220)
        pygame.draw.circle(screen, influence_color, (RENDER_X, RENDER_Y), particle.influence_radius)
        
    def render_particle_velocity(self, screen, particle):
        RENDER_X = particle.pos.x + self.x
        RENDER_Y = -particle.pos.y + self.y

        if abs(particle.velocity.x) > particle.influence_radius:
            line_x = particle.influence_radius * (abs(particle.velocity.x)/particle.velocity.x)
        else:
            line_x = particle.velocity.x
        if abs(particle.velocity.y) > particle.influence_radius:
            line_y = particle.influence_radius * (abs(particle.velocity.y)/particle.velocity.y)
        else:
            line_y = particle.velocity.y

        pygame.draw.line(screen, (255, 0, 0), (RENDER_X, RENDER_Y), (RENDER_X + line_x, RENDER_Y - line_y), 2)

    def queue_control(self, action):
        if not self.accumulator and not self.pending_controls:
            action()
            return True
        if len(self.pending_controls) >= MAX_PENDING_CONTROLS:
            self.rejected_controls += 1
            return False
        self.pending_controls.append(action)
        return True

    def advance(self, dt, mouse_forces=()):
        # Discard excessive backlog rather than entering a spiral of death.
        accepted = min(max(dt, 0), FIXED_DT * MAX_SUBSTEPS)
        self.dropped_time += max(dt, 0) - accepted
        steps = 0
        # Store the time-weighted mouse contribution in each particle's net
        # force until its next step; no event queue or growing buffer is needed.
        remaining = accepted
        while remaining > 0 or self.accumulator >= FIXED_DT:
            if steps == MAX_SUBSTEPS:
                # Keep the accepted remainder, including its mouse contribution,
                # for the next call rather than performing a ninth step.
                for pos, negative in mouse_forces:
                    self.apply_mouse_force(pos, negative, remaining / FIXED_DT)
                self.accumulator += remaining
                break
            part = min(remaining, max(0.0, FIXED_DT - self.accumulator))
            for pos, negative in mouse_forces:
                self.apply_mouse_force(pos, negative, part / FIXED_DT)
            self.accumulator += part
            remaining -= part
            if self.accumulator + 1e-12 >= FIXED_DT:
                self.step(FIXED_DT)
                self.accumulator = 0.0
                steps += 1
                while self.pending_controls:
                    self.pending_controls.popleft()()
        return steps

    def step(self, dt):
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
            previous_pos = Vector2D(particle.pos.x, particle.pos.y)
            particle.move(dt)
            self.resolve_obstacle(particle, previous_pos)

    def render(self, screen):
        # Render Layer 1
        for particle in self.particles:
            self.render_bounds(screen)
            self.render_particle_influence(screen, particle)

        # The obstacle sits above the influence discs so it stays visible.
        self.render_obstacle(screen)

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
    