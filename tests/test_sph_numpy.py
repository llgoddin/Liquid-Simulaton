import importlib.util
import random
import unittest

import sph
import sph_numpy
from New_Vector2D import Vector2D
from Particle import Particle


@unittest.skipUnless(importlib.util.find_spec("numpy"), "optional NumPy candidate dependency is not installed")
class NumpyEquivalenceTests(unittest.TestCase):
    def test_seeded_snapshot_matches_reference(self):
        rng = random.Random(6021)
        particles = []
        for _ in range(200):
            particle = Particle(rng.uniform(-45, 45), rng.uniform(-45, 45), 1)
            particle.mass = rng.uniform(0.2, 2.0)
            particle.velocity = Vector2D(rng.uniform(-3, 3), rng.uniform(-3, 3))
            particles.append(particle)
        expected = sph.solve(particles)
        actual = sph_numpy.solve(particles)
        # Float64 vectorized reductions reorder sums; allow relative 2e-11,
        # absolute 1e-13 for density, pressure, and force components.
        for expected_values, actual_values in zip(expected, actual, strict=True):
            self.assertEqual(len(expected_values), len(actual_values))
            for expected_item, actual_item in zip(expected_values, actual_values, strict=True):
                if isinstance(expected_item, tuple):
                    for a, b in zip(expected_item, actual_item, strict=True):
                        self.assertAlmostEqual(a, b, delta=1e-13 + 2e-11 * abs(a))
                else:
                    self.assertAlmostEqual(expected_item, actual_item, delta=1e-13 + 2e-11 * abs(expected_item))

    def test_coincident_and_outside_pairs_match(self):
        particles = [Particle(0, 0, 1), Particle(0, 0, 1), Particle(30, 0, 1)]
        self.assertEqual(sph.solve(particles), sph_numpy.solve(particles))

    def test_dense_clump_snapshot_matches_reference(self):
        particles = []
        for index in range(200):
            particle = Particle((index % 20) * 0.25, (index // 20) * 0.25, 1)
            particle.velocity = Vector2D(index % 7 * 0.1, index % 11 * -0.1)
            particles.append(particle)
        expected = sph.solve(particles)
        actual = sph_numpy.solve(particles)
        for expected_values, actual_values in zip(expected, actual, strict=True):
            for expected_item, actual_item in zip(expected_values, actual_values, strict=True):
                pairs = zip(expected_item, actual_item, strict=True) if isinstance(expected_item, tuple) else [(expected_item, actual_item)]
                for a, b in pairs:
                    self.assertAlmostEqual(a, b, delta=1e-13 + 2e-11 * abs(a))


if __name__ == "__main__":
    unittest.main()
