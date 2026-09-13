from __future__ import annotations

import unittest

import numpy as np

from steam_cn_insights.analysis import bootstrap_median_difference


class AnalysisTests(unittest.TestCase):
    def test_bootstrap_median_difference_is_reproducible(self) -> None:
        first = np.array([0.2, 0.3, 0.4, 0.5])
        second = np.array([0.1, 0.2, 0.2, 0.3])
        result_one = bootstrap_median_difference(first, second, iterations=500, seed=7)
        result_two = bootstrap_median_difference(first, second, iterations=500, seed=7)
        self.assertEqual(result_one, result_two)
        self.assertAlmostEqual(result_one[0], 0.15)

    def test_bootstrap_requires_two_observations_per_group(self) -> None:
        with self.assertRaises(ValueError):
            bootstrap_median_difference(np.array([0.1]), np.array([0.2, 0.3]))


if __name__ == "__main__":
    unittest.main()
