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
        table = ACTable(None, None, 1, 1)
        self.assertEqual(table.data, [[None]])


    def testDataArrayLarge(self):
        """
        We can initialise a 3x4 data array.
        """
        table = ACTable(None, None, 3, 4)
        self.assertEqual(table.data, [
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, None, None]])



class TestCellPositions(unittest.TestCase):
    """
    Tests for cell positioning.
    """

    def setUp(self):
        """
        Make a 3x4 table with 5+5 padding and 3+3 spacing. The three column
        widths are 5, 6, and 7.
        """
        self.table = ACTable(None, None, 3, 4)
        self.table.setTablePadding(5, 5)
        self.table.setCellSpacing(3)
        self.table.setColumnWidths(5, 6, 7)
        self.table.setFontSize(18)

    def testTopLeft(self):
        result = self.table._cellPosition(0, 0)
        expected = (5, 5)
        self.assertEqual(result, expected)

    def testTopMiddle(self):
        result = self.table._cellPosition(1, 0)
        expected = (5 + (5 * 18) + 3, 5)
        self.assertEqual(result, expected)
