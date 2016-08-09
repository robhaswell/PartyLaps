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

        self.cells = [[]]

        self._initialise()


    def _initialise(self):
        """
        Initialise the data storage array and label array. We are required to
        store cell data so that the cell information can be retrieved when
        redrawing due to a font size change.
        """
        self.data = [[None]*self.nColumns]*self.nRows

        if self.ac is None:
            return

        # Delete all existing labels
        for row in self.cells:
            for label in row:
                self.ac.removeLabel(label)

        self.cells = [
                [ self.ac.addLabel(self.window, 0) for i in xrange(self.nColumns) ]
            for j in xrange(self.nRows) ]


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


    def _cellPosition(self, iCol, iRow):
        """
        Return the (x,y) co-ordinates for a cell at position iCol,iRow.
        """
        x = self.paddingX + (sum(self.columnWidths[:iCol]) * self.fontSize) + (iCol * self.spacing)
        y = self.paddingY + (iRow * self.fontSize) + (max(0, iRow-1) * self.spacing)
        return (x, y)
