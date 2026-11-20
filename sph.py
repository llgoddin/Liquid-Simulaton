"""Two-dimensional weakly-compressible SPH kernels and snapshot solver.

Kernel constants follow Bindel's 2D derivation. Pressure uses the symmetric
conservative force form of Becker and Teschner; viscosity uses Bindel's 2D
Laplacian. This explicit combination is documented in SPH.md.
"""
import math
from types import SimpleNamespace

from New_Vector2D import Vector2D

H = 30.0
REST_DENSITY = 1 / 225
STIFFNESS = 2500.0
VISCOSITY = 1.0


def poly6(r, h):
    if r < 0 or h <= 0 or r >= h:
        return 0.0
    return 4 / (math.pi * h**8) * (h * h - r * r) ** 3


def spiky(r, h):
    if r < 0 or h <= 0 or r >= h:
        return 0.0
    return 10 / (math.pi * h**5) * (h - r) ** 3


def spiky_gradient(x, y, h):
    r = math.hypot(x, y)
    if h <= 0 or r == 0 or r >= h:
        return 0.0, 0.0
    scale = -30 / (math.pi * h**5) * (h - r) ** 2 / r
    return scale * x, scale * y


def viscosity_laplacian(r, h):
    if r < 0 or h <= 0 or r >= h:
        return 0.0
    return 40 / (math.pi * h**5) * (h - r)


def mirror_boundary_particles(particles, x_bounds=None, y_bounds=None, obstacle=None, h=H):
    """Create mirrored ghost samples within h of container/obstacle walls.

    ``obstacle`` is ``(x, y, radius)``; each particle's collision radius is
    included when locating its fluid-side contact surface. Ghost velocity
    reflects the normal component, giving a no-penetration symmetry condition.
    """
    ghosts = []

    def reflect(particle, x, y, nx, ny, mass_scale=1.0):
        normal_velocity = particle.velocity.x * nx + particle.velocity.y * ny
        ghosts.append(SimpleNamespace(
            mass=particle.mass * mass_scale,
            pos=Vector2D(x, y),
            velocity=Vector2D(
                particle.velocity.x - 2 * normal_velocity * nx,
                particle.velocity.y - 2 * normal_velocity * ny,
            ),
        ))

    for particle in particles:
        x, y = particle.pos.x, particle.pos.y
        x_faces = []
        y_faces = []
        if x_bounds is not None:
            low, high = x_bounds
            if 0 <= x - low < h:
                x_faces.append(low)
                reflect(particle, 2 * low - x, y, 1.0, 0.0)
            if 0 <= high - x < h:
                x_faces.append(high)
                reflect(particle, 2 * high - x, y, -1.0, 0.0)
        if y_bounds is not None:
            low, high = y_bounds
            if 0 <= y - low < h:
                y_faces.append(low)
                reflect(particle, x, 2 * low - y, 0.0, 1.0)
            if 0 <= high - y < h:
                y_faces.append(high)
                reflect(particle, x, 2 * high - y, 0.0, -1.0)
        # Corner images restore support missing beyond two intersecting walls.
        for x_face in x_faces:
            for y_face in y_faces:
                ghosts.append(SimpleNamespace(
                    mass=particle.mass,
                    pos=Vector2D(2 * x_face - x, 2 * y_face - y),
                    velocity=Vector2D(-particle.velocity.x, -particle.velocity.y),
                ))
        if obstacle is not None:
            ox, oy, radius = obstacle
            dx, dy = x - ox, y - oy
            distance = math.hypot(dx, dy)
            contact_radius = radius + particle.radius
            gap = distance - contact_radius
            if 0 <= gap < min(h, contact_radius) and distance > 0:
                nx, ny = dx / distance, dy / distance
                ghost_distance = contact_radius - gap
                # Radial reflection compresses the represented area on the
                # obstacle side; apply the 2D polar-coordinate Jacobian.
                mass_scale = ghost_distance / distance
                reflect(
                    particle,
                    ox + ghost_distance * nx,
                    oy + ghost_distance * ny,
                    nx,
                    ny,
                    mass_scale,
                )
    return ghosts


def solve(particles, h=H, rest_density=REST_DENSITY, stiffness=STIFFNESS,
          viscosity=VISCOSITY, boundary_particles=()):
    """Return fluid density, nonnegative pressure and fluid pair forces.

    Boundary particles are static mirror samples: they contribute to fluid
    density and force, but only the input fluid's values are returned. Every
    result is computed from unchanged particle positions and velocities.
    """
    fluid_count = len(particles)
    all_particles = list(particles) + list(boundary_particles)
    count = len(all_particles)
    if h <= 0:
        raise ValueError("support radius must be positive")
    densities = [p.mass * poly6(0, h) for p in all_particles]
    pairs = []
    h2 = h * h
    density_factor = 4 / (math.pi * h**8)
    for i, a in enumerate(all_particles):
        for j in range(i + 1, count):
            b = all_particles[j]
            x, y = a.pos.x - b.pos.x, a.pos.y - b.pos.y
            r2 = x * x + y * y
            if r2 < h2:
                r = math.sqrt(r2)
                weight = density_factor * (h2 - r2) ** 3
                densities[i] += b.mass * weight
                densities[j] += a.mass * weight
                pairs.append((i, j, x, y, r))
    pressures = [max(0.0, stiffness * (rho - rest_density)) for rho in densities]
    forces = [[0.0, 0.0] for _ in all_particles]
    grad_factor = -30 / (math.pi * h**5)
    lap_factor = 40 / (math.pi * h**5)
    for i, j, x, y, r in pairs:
        a, b = all_particles[i], all_particles[j]
        mass_product = a.mass * b.mass
        if r:
            scale = -mass_product * (pressures[i] / densities[i]**2 + pressures[j] / densities[j]**2) * grad_factor * (h-r)**2 / r
            fx, fy = scale * x, scale * y
        else:
            fx = fy = 0.0
        visc = viscosity * mass_product / (densities[i] * densities[j]) * lap_factor * (h-r)
        fx += visc * (b.velocity.x-a.velocity.x)
        fy += visc * (b.velocity.y-a.velocity.y)
        forces[i][0] += fx
        forces[i][1] += fy
        forces[j][0] -= fx
        forces[j][1] -= fy
    return densities[:fluid_count], pressures[:fluid_count], [tuple(force) for force in forces[:fluid_count]]
