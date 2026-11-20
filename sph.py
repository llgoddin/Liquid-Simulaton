"""Two-dimensional weakly-compressible SPH kernels and snapshot solver.

Kernel constants follow Bindel's 2D derivation. Pressure uses the symmetric
conservative force form of Becker and Teschner; viscosity uses Bindel's 2D
Laplacian. This explicit combination is documented in SPH.md.
"""
import math

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


def solve(particles, h=H, rest_density=REST_DENSITY, stiffness=STIFFNESS, viscosity=VISCOSITY):
    """Return density, nonnegative pressure and equal/opposite pair forces.

    Every result is computed from unchanged particle positions and velocities.
    """
    count = len(particles)
    if h <= 0:
        raise ValueError("support radius must be positive")
    densities = [p.mass * poly6(0, h) for p in particles]
    pairs = []
    h2 = h * h
    density_factor = 4 / (math.pi * h**8)
    for i, a in enumerate(particles):
        for j in range(i + 1, count):
            b = particles[j]
            x, y = a.pos.x - b.pos.x, a.pos.y - b.pos.y
            r2 = x * x + y * y
            if r2 < h2:
                r = math.sqrt(r2)
                weight = density_factor * (h2 - r2) ** 3
                densities[i] += b.mass * weight
                densities[j] += a.mass * weight
                pairs.append((i, j, x, y, r))
    pressures = [max(0.0, stiffness * (rho - rest_density)) for rho in densities]
    forces = [[0.0, 0.0] for _ in particles]
    grad_factor = -30 / (math.pi * h**5)
    lap_factor = 40 / (math.pi * h**5)
    for i, j, x, y, r in pairs:
        a, b = particles[i], particles[j]
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
    return densities, pressures, [tuple(force) for force in forces]
