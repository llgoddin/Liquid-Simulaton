import math
import random
from collections import deque

import pygame

import sph
from New_Vector2D import Vector2D
from Particle import Particle

FIXED_DT = 1 / 120
MAX_SUBSTEPS = 8
MAX_PENDING_CONTROLS = 256
# Safety guards, not SPH tuning parameters: force is in the legacy per-step
# impulse channel; the velocity cap is a broad runaway bound; direct steps may
# never exceed the solver's fixed timestep.
MAX_FORCE = 50.0
MAX_VELOCITY = 500.0
MAX_DT = FIXED_DT
PHYSICAL_FORCE_TO_LEGACY = 120.0
GRAVITY_ACCELERATION = 10.0
# Per-step gravity was previously a 10-unit velocity impulse, not acceleration.
# A contact whose inward normal speed does not exceed this is treated as a
# resting contact: the inward component is removed rather than reflected, so a
# particle sitting on the obstacle does not jitter. Genuine impacts exceed it.
REST_SPEED = 10.0

class Particle_Manager:

    def __init__(self, x, y, num_particles, radius, x_bounds, y_bounds, gravity, repulse, vertical_spawn):
        self.GRAVITY = gravity
        self.REPULSE = repulse
        self.mouse_radius = 150.0
        self.mouse_strength = 10.0
        self.mouse_pos = None
        self.accumulator = 0.0
        self.dropped_time = 0.0
        self.pending_controls = deque()
        self.rejected_controls = 0
        self.max_force = MAX_FORCE
        self.max_velocity = MAX_VELOCITY
        self.max_dt = MAX_DT
        self.clamp_activations = {"force": 0, "velocity": 0, "dt": 0}
        self.sph_h = sph.H
        self.sph_rest_density = sph.REST_DENSITY
        self.sph_stiffness = sph.STIFFNESS
        self.sph_viscosity = sph.VISCOSITY
        self.densities = []
        self.pressures = []
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
        for particle in self.particles:
            self._separate_from_obstacle(particle, x, y, radius)

    def _separate_from_obstacle(self, particle, x, y, radius):
        contact = radius + particle.radius
        xmin, xmax = -self.X_BOUND + particle.radius, self.X_BOUND - particle.radius
        ymin, ymax = -self.Y_BOUND + particle.radius, self.Y_BOUND - particle.radius
        particle.pos.x = min(xmax, max(xmin, particle.pos.x))
        particle.pos.y = min(ymax, max(ymin, particle.pos.y))
        dx, dy = particle.pos.x - x, particle.pos.y - y
        distance = math.hypot(dx, dy)
        if distance >= contact - 1e-10:
            return
        base = math.atan2(dy, dx) if distance else 0.0
        angles = [base, 0, math.pi / 2, math.pi, 3 * math.pi / 2]
        for edge in (xmin, xmax):
            ratio = (edge - x) / contact
            if abs(ratio) <= 1:
                a = math.acos(ratio)
                angles.extend((a, -a))
        for edge in (ymin, ymax):
            ratio = (edge - y) / contact
            if abs(ratio) <= 1:
                a = math.asin(ratio)
                angles.extend((a, math.pi - a))
        candidates = []
        for angle in angles:
            px, py = x + contact * math.cos(angle), y + contact * math.sin(angle)
            if xmin - 1e-9 <= px <= xmax + 1e-9 and ymin - 1e-9 <= py <= ymax + 1e-9:
                candidates.append(((px - particle.pos.x) ** 2 + (py - particle.pos.y) ** 2, px, py))
        if candidates:
            _, particle.pos.x, particle.pos.y = min(candidates)

    def move_obstacle(self, x, y):
        """Move the circular obstacle in manager-local coordinates.

        The center is clamped so the obstacle fits within the container. Particles
        intersecting the swept disk are displaced to its exterior; obstacle
        motion is kinematic (it does not impart a velocity impulse).
        """
        if self.obstacle is None:
            return
        old_x, old_y, radius = self.obstacle
        limit_x = max(0, self.X_BOUND - radius)
        limit_y = max(0, self.Y_BOUND - radius)
        new_x = min(limit_x, max(-limit_x, x))
        new_y = min(limit_y, max(-limit_y, y))
        dx, dy = new_x - old_x, new_y - old_y
        distance_sq = dx * dx + dy * dy
        for particle in self.particles:
            t = 0.0 if distance_sq == 0 else min(1.0, max(0.0,
                ((particle.pos.x - old_x) * dx + (particle.pos.y - old_y) * dy) / distance_sq))
            cx, cy = old_x + t * dx, old_y + t * dy
            contact = radius + particle.radius
            px, py = particle.pos.x - cx, particle.pos.y - cy
            distance = math.hypot(px, py)
            if distance < contact and distance_sq:
                # Carry an intersected particle to the front of the moving disk,
                # retaining its lateral offset. At a wall, separation slides it
                # around the obstacle instead of pushing it outside the box.
                length = math.sqrt(distance_sq)
                ux, uy = dx / length, dy / length
                lateral = -px * uy + py * ux
                forward = math.sqrt(max(0.0, contact * contact - lateral * lateral))
                particle.pos = Vector2D(new_x + ux * forward - uy * lateral,
                                        new_y + uy * forward + ux * lateral)
        self.obstacle = (new_x, new_y, radius)
        for particle in self.particles:
            self._separate_from_obstacle(particle, new_x, new_y, radius)

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

        if self.obstacle is not None:
            self._separate_from_obstacle(new_particle, *self.obstacle)

        self.particles.append(new_particle)
        self.num_particles += 1

    def delete_particle(self):
        if self.particles:
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
        if self.obstacle is not None:
            ox, oy, radius = self.obstacle
            ox = min(x_bound - radius, max(-x_bound + radius, ox))
            oy = min(y_bound - radius, max(-y_bound + radius, oy))
            self.obstacle = (ox, oy, radius)
            for particle in self.particles:
                self._separate_from_obstacle(particle, ox, oy, radius)

    def update_coordinate_grid(self, screen):
        # X_OFFSET = screen.get_width()/2
        # Y_OFFSET = -screen.get_height()/2

        # RENDER_X = particle.pos.x + X_OFFSET
        # RENDER_Y = screen.get_height() - particle.pos.y + Y_OFFSET
        return 0

    def apply_mouse_force(self, pos, negative=False, weight=1.0):
        local_pos = (-(self.x - pos[0]), self.y - pos[1])
        self.mouse_pos = local_pos

        for particle in self.particles:
            particle.force_towards_mouse(local_pos, negative, weight, self.mouse_radius, self.mouse_strength)

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
        if not math.isfinite(dt) or dt < 0:
            dt = 0.0
            self.clamp_activations["dt"] += 1
        elif dt > self.max_dt:
            dt = self.max_dt
            self.clamp_activations["dt"] += 1
        # Calculate all SPH terms from one immutable pre-move snapshot.
        if self.REPULSE:
            boundary_particles = sph.mirror_boundary_particles(
                self.particles,
                x_bounds=(-self.X_BOUND, self.X_BOUND),
                y_bounds=(-self.Y_BOUND, self.Y_BOUND),
                obstacle=self.obstacle,
                h=self.sph_h,
            )
            self.densities, self.pressures, sph_forces = sph.solve(
                self.particles, self.sph_h, self.sph_rest_density,
                self.sph_stiffness, self.sph_viscosity,
                boundary_particles=boundary_particles,
            )
            # SPH forces use physical units; convert through the same legacy
            # 120 Hz channel used by Particle.move.
            for particle, (force_x, force_y) in zip(self.particles, sph_forces, strict=True):
                particle.apply_force(Vector2D(
                    force_x / PHYSICAL_FORCE_TO_LEGACY,
                    force_y / PHYSICAL_FORCE_TO_LEGACY,
                ))
        if self.GRAVITY:
            # Gravity is a physical acceleration (px/s^2), unlike the original
            # per-step velocity impulse. Convert its force once for the legacy
            # Particle.move integration channel.
            for particle in self.particles:
                particle.apply_force(Vector2D(
                    0,
                    -GRAVITY_ACCELERATION * particle.mass / PHYSICAL_FORCE_TO_LEGACY,
                ))
        # Move
        for particle in self.particles:
            previous_pos = Vector2D(particle.pos.x, particle.pos.y)
            force = particle.net_force
            force_magnitude = math.hypot(force.x, force.y)
            if force_magnitude > self.max_force:
                particle.net_force = force * (self.max_force / force_magnitude)
                self.clamp_activations["force"] += 1
            particle.move(dt)
            speed = math.hypot(particle.velocity.x, particle.velocity.y)
            if speed > self.max_velocity:
                particle.velocity = particle.velocity * (self.max_velocity / speed)
                self.clamp_activations["velocity"] += 1
            self.resolve_obstacle(particle, previous_pos)

    def render_mouse_influence(self, screen):
        if self.mouse_pos is None or self.mouse_radius <= 0 or math.isinf(self.mouse_radius):
            return

        RENDER_X = self.mouse_pos[0] + self.x
        RENDER_Y = -self.mouse_pos[1] + self.y

        pygame.draw.circle(screen, (120, 120, 255), (int(RENDER_X), int(RENDER_Y)), int(self.mouse_radius), 1)

    def render(self, screen, debug=False):
        # The container is essential context, not a diagnostic overlay.
        self.render_bounds(screen)
        if debug:
            # Render Layer 1 (debug)
            for particle in self.particles:
                self.render_particle_influence(screen, particle)

        # The obstacle is part of the simulation, not a diagnostic, so it is
        # drawn by default. It sits above the influence discs so it stays visible.
        self.render_obstacle(screen)

        if debug:
            # Render Layer 2 (debug)
            for particle in self.particles:
                self.render_particle_velocity(screen, particle)

        # Render Layer 3 — the simulation itself, always drawn.
        for particle in self.particles:
            self.render_particle(screen, particle)

        # Render influence ring at the cursor so the radius is visible.
        self.render_mouse_influence(screen)

    # Getters
    def get_gravity(self):
        return self.GRAVITY

    def get_repulse(self):
        return self.REPULSE


    # Setters
    def set_gravity(self, value=False):
        if isinstance(value, bool):
            self.GRAVITY = value

    def set_repulse(self, value=False):
        if isinstance(value, bool):
            self.REPULSE = value
