# python -m unittest test_ACTable

import unittest
from ACTable import ACTable

class TestCellPositions(unittest.TestCase):
    """
    Tests for cell positioning.
    """

    def setUp(self):
        """
        Make a 3x4 table with 5+5 padding and 3+3 spacing. The three column
        widths are 5, 6, and 7.
        """
        self.table = ACTable(None, None)
        self.table.setSize(3, 4)
        self.table.setTablePadding(5, 5)
        self.table.setCellSpacing(3, 3)
        self.table.setColumnWidths(5, 6, 7)
        self.table.setFontSize(18)
        self.table.draw()


    def testTopLeft(self):
        result = self.table._cellPosition(0, 0)
        expected = (5, 5)
        self.assertEqual(result, expected)


    def testTopMiddle(self):
        result = self.table._cellPosition(1, 0)
        expected = (5 + (5 * 18) + 3, 5)
        self.assertEqual(result, expected)


    def testTopRight(self):
        result = self.table._cellPosition(2, 0)
        expected = (5 + (5 * 18) + 3 + (6 * 18) + 3, 5)
        self.assertEqual(result, expected)


    def testSecondRow(self):
        result = self.table._cellPosition(0, 1)
        expected = (5, 5 + 18 + 3)
        self.assertEqual(result, expected)


    def testThirdRow(self):
        result = self.table._cellPosition(0, 2)
        expected = (5, 5 + 18 + 3 + 18 + 3)
        self.assertEqual(result, expected)
