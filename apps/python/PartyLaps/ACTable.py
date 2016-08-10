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

        self.data = {}
        self.cells = {}


    def initialize(self):
        """
        Initialise the data storage array and label array. We are required to
        store cell data so that the cell information can be retrieved when
        redrawing due to a font size change.
        """
        self.data = {}

        # if self.ac is unavailable then we must be in a test and cannot
        # proceed.
        if self.ac is None:
            return

        # Delete all existing labels
        for label in self.cells.items():
            raise Exception("There were cells that needed to be removed.") # TODO

        self.cells = {}

        for i in range(self.nColumns):
            for j in range(self.nRows):
                label = self.ac.addLabel(self.window, "")
                self.ac.setSize(label, self.columnWidths[i] * self.fontSize, self.fontSize)
                self.ac.setPosition(label, *self._cellPosition(i, j))
                self.ac.setFontSize(label, self.fontSize)
                self.ac.setFontAlignment(label, self.columnAlignments[i])
                self.cells[(i, j)] = label


    def setFontSize(self, fontSize):
        self.fontSize = fontSize


    def setTablePadding(self, paddingX, paddingY):
        """
        Set the pixel amount of padding at the top and left of the table.
        """
        self.paddingX = paddingX
        self.paddingY = paddingY


    def setCellSpacing(self, spacingX, spacingY):
        """
        Set the pixel amount of spacing between each cell.
        """
        self.spacingX = spacingX
        self.spacingY = spacingY


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
        #self.ac.log(" ".join(map(str, [type(iX), type(iY), type(self.fontSize), type(self.spacing)])))
        #self.ac.log(repr(self.columnWidths))
        x = self.paddingX + (sum(self.columnWidths[:iX]) * self.fontSize) + (iX * self.spacingX)
        y = self.paddingY + iY * (self.fontSize + self.spacingY)
        return (x, y)


    def setCellValue(self, text, iX, iY):
        """
        Set the cell text at position iX,iY.
        """
        self.ac.setText(self.getCellLabel(iX, iY), text)
        self.data[(iX, iY)] = text

    
    def setFontColor(self, r, g, b, s, iX, iY):
        """
        Set the font color of the cell at iX,iY.
        """
        self.ac.setFontColor(self.getCellLabel(iX, iY), r, g, b, s)


    def getCellLabel(self, iX, iY):
        return self.cells[(iX, iY)]


    def addOnClickedListener(self, iX, iY, callback):
        self.ac.addOnClickedListener(self.getCellLabel(iX, iY), callback)
