# python -m unittest test_ACTable

import unittest
from ACTable import ACTable

class TestInit(unittest.TestCase):
    """
    Tests for initialisation.
    """

    def testDataArraySimple(self):
        """
        We can initialise a 1x1 data array.
        """
        table = ACTable(None, 1, 1)
        self.assertEqual(table.data, [[None]])


    def testDataArrayLarge(self):
        """
        We can initialise a 3x4 data array.
        """
        table = ACTable(None, 3, 4)
        self.assertEqual(table.data, [
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, None, None]])

