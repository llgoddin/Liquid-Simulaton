"""Optional NumPy-vectorized SPH solver; does not affect the pure-Python path."""


def solve(particles, h=30.0, rest_density=1 / 225, stiffness=2500.0, viscosity=1.0):
    """Compute the same snapshot SPH formulas as :func:`sph.solve`.

    NumPy is imported lazily so it remains an optional dependency. Pairwise
    matrices use O(N^2) memory; this is intended as a candidate, not default.
    """
    import numpy as np

    if h <= 0:
        raise ValueError("support radius must be positive")
    count = len(particles)
    positions = np.array([(p.pos.x, p.pos.y) for p in particles], dtype=np.float64).reshape(count, 2)
    velocities = np.array([(p.velocity.x, p.velocity.y) for p in particles], dtype=np.float64).reshape(count, 2)
    masses = np.array([p.mass for p in particles], dtype=np.float64)
    delta = positions[:, None, :] - positions[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", delta, delta)
    inside = r2 < h * h
    density_weights = 4 / (np.pi * h**8) * np.maximum(h * h - r2, 0) ** 3
    densities = (density_weights * inside) @ masses
    pressures = np.maximum(0.0, stiffness * (densities - rest_density))

    # Evaluate each directed interaction and reduce by source particle. This
    # avoids np.add.at's serial scatter (a major source of clump tail latency).
    radii = np.sqrt(r2)
    nonzero = inside & (radii != 0)
    pressure_term = pressures / densities**2
    pressure_sum = pressure_term[:, None] + pressure_term[None, :]
    pair_mass = masses[:, None] * masses[None, :]
    pressure_scale = np.zeros_like(r2)
    pressure_scale[nonzero] = (
        -pair_mass[nonzero]
        * pressure_sum[nonzero]
        * (-30 / (np.pi * h**5))
        * (h - radii[nonzero])**2 / radii[nonzero]
    )
    pair_force = pressure_scale[:, :, None] * delta
    visc_scale = np.zeros_like(r2)
    visc_scale[inside] = (
        viscosity
        * (masses[:, None] * masses[None, :])[inside]
        / (densities[:, None] * densities[None, :])[inside]
        * (40 / (np.pi * h**5))
        * (h - radii[inside])
    )
    pair_force += visc_scale[:, :, None] * (velocities[None, :, :] - velocities[:, None, :])
    forces = pair_force.sum(axis=1)
    return densities.tolist(), pressures.tolist(), [tuple(row) for row in forces]
