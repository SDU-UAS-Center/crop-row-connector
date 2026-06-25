import unittest

import numpy as np

from crop_row_connector import HungarianAlgorithm


class TestHungarianAlgorithm(unittest.TestCase):
    def test_init(self) -> None:
        hun = HungarianAlgorithm()
        res = hun.hungarian_algorithm(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))
        np.testing.assert_almost_equal(res, np.array([[0, 0], [1, 1], [2, 2]]))
