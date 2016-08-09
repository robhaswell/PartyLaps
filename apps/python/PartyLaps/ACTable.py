"""
A table drawing utility for Assetto Corsa.
"""

class ACTable(object):

    def __init__(self, ac, window, nColumns, nRows):
        self.ac = ac
        self.window = window
        self.paddingX = 0
        self.paddingY = 0
        self.nColumns = nColumns
        self.nRows = nRows

        self.data = [[]]
        self.cells = [[]]


    def initialize(self):
        """
        Initialise the data storage array and label array. We are required to
        store cell data so that the cell information can be retrieved when
        redrawing due to a font size change.
        """
        self.data = [[None]*self.nColumns]*self.nRows

        # if self.ac is unavailable then we must be in a test and cannot
        # proceed.
        if self.ac is None:
            return

        # Delete all existing labels
        for row in self.cells:
            for label in row:
                self.ac.removeLabel(label)

        self.cells = [[None]*self.nColumns]*self.nRows
        for i in xrange(self.nColumns):
            for j in xrange(self.nRows):
                label = self.ac.addLabel(self.window, 0)
                self.ac.setSize(label, self.columnWidths[i] * self.fontSize, self.fontSize)
                self.ac.setPosition(label, *self._cellPosition(i, j))
                self.ac.setFontSize(label, self.fontSize)
                self.ac.setFontAlignment(label, self.columnAlignments[i])
                self.cells[j][i] = label


    def setFontSize(self, fontSize):
        self.fontSize = fontSize


    def setTablePadding(self, paddingX, paddingY):
        """
        Set the pixel amount of padding at the top and left of the table.
        """
        self.paddingX = paddingX
        self.paddingY = paddingY


    def setCellSpacing(self, spacing):
        """
        Set the pixel amount of spacing between each cell.
        """
        self.spacing = spacing


    def setColumnWidths(self, *columnWidths):
        """
        Set the width of each column. The width is given in multiples of the font size.
        """
        if len(columnWidths) != self.nColumns:
            raise ValueError("The number of provided column width entries does "
                    "not match the expected number of columns.")
        self.columnWidths = columnWidths


    def setColumnAlignments(self, *columnAlignments):
        """
        Set the alignments of each column, possible values are 'left', 'right'
        and 'center'.
        """
        if len(columnAlignments) != self.nColumns:
            raise ValueError("The number of provided column alignment entries "
                    "does not match the expected number of columns.")
        self.columnAlignments = columnAlignments


    def _cellPosition(self, iX, iY):
        """
        Return the (x,y) co-ordinates for a cell at position iX,iY.
        """
        x = self.paddingX + (sum(self.columnWidths[:iX]) * self.fontSize) + (iX * self.spacing)
        y = self.paddingY + (iY * self.fontSize) + (iY * self.spacing)
        return (x, y)


    def setCellValue(self, text, iX, iY):
        """
        Set the cell text at position iX,iY.
        """
        self.ac.setText(self.cells[iY][iX], text)


    def getCellLabel(self, iX, iY):
        return self.cells[iX][iY]
