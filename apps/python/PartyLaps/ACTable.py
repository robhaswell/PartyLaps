"""
A table drawing utility for Assetto Corsa.
"""

class ACTable(object):

    def __init__(self, ac, nColumns, nRows):
        self.ac = ac
        self.paddingX = 0
        self.paddingY = 0
        self.nColumns = nColumns
        self.nRows = nRows

        self._initDataArray()


    def _initDataArray(self):
        """
        Initialise the data storage array. We are required to do this so that
        the cell information can be stored when redrawing due to a font size
        change.
        """
        self.data = [[None]*self.nColumns]*self.nRows


    def setFontSize(self, fontSize):
        self.fontSize = fontSize


    def setTablePadding(self, paddingX, paddingY):
        """
        Set the pixel amount of padding at the top and left of the table.
        """
        self.paddingX = paddingX
        self.padding = paddingY


    def setCellSpacing(self, spacing):
        """
        Set the pixel amount of spacing between each cell.
        """
        self.spacing = spacing


    def setColumnWidths(self, *columnWidths):
        """
        Set the width of each column. The width is given in multiples of the font size.
        """
        self.columnWidths = columnWidths


    def setColumnAlignments(self, columnAlignments):
        self.columnAlignments = columnAlignments
