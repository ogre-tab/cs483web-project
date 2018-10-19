import sys

from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QGridLayout,
                             QLabel, QListView, QPushButton, QTextEdit,
                             QWidget)
from whoosh.index import Index
from whoosh.qparser import MultifieldParser


class WhooshGui(QWidget):
    def __init__(self, indexer: Index):
        super().__init__()
        # our column names
        self.columns = ["name", "description", "alias", "application", "capability", "user", "limitation", "path"]
        # set the whoosh index
        self.indexer = indexer
        # the search box
        self.searchTextEdit = None
        # the list box
        self.resultsList = QListView()
        # the results of our last search
        self.results = None
        # a dictionary for our text widgets
        self.widgetDict = dict()
        # create the gui
        self.initUIWhoosh()

    def search(self, searchTerm):
        # check that we actually have an indexer
        if (self.indexer is None):
            return
        # NOTE: can add a different weighting system by adding the term to the searcher(weighting.here())
        with self.indexer.searcher() as searcher:
            # create our query that will be sent to the sercher
            query = MultifieldParser(self.columns, schema=self.indexer.schema).parse(searchTerm)
            # create a searcher with our query
            temp_results = searcher.search(query)
            # create a model for our list box
            model = QStandardItemModel(self.resultsList)
            # clear our last search results
            self.results = dict()
            # go through our new results
            for line in temp_results:
                # add the power name to our list box
                model.appendRow(QStandardItem(line["name"]))
                # create a new line of data for our results dictionary
                inner_dict = dict()
                for col in self.columns:
                    if (col == "path"):
                        inner_dict[col] = line["name"].replace(" ", "_")
                    else:
                        inner_dict[col] = line[col]
                # add the results to our dictionary
                self.results[line["name"]] = inner_dict
            # add our model to our list box
            self.resultsList.setModel(model)

    def resultChanged(self, index):
        # get the name of the clicked item
        powerName = self.resultsList.model().itemFromIndex(index).text()
        # get our power's data
        line = self.results[powerName]
        # don't modifiy the values of these columns
        ignore_columns = ["name", "description", "path"]
        # loop through each column name and set our widget's text
        for col in self.columns:
            if (col not in ignore_columns):
                clean_line = line[col].strip('"').replace('","', '\n')
                self.widgetDict[col].setPlainText(clean_line)
            else:
                self.widgetDict[col].setPlainText(line[col])

    def searchButtonClicked(self):
        # search for our term
        self.search(self.searchTextEdit.toPlainText())

    # build our ui
    def initUIWhoosh(self):
        # create a grid to add widgets
        grid = QGridLayout()
        # the widgets will have 4 pixels around them
        grid.setSpacing(4)
        # set our window's layout
        self.setLayout(grid)
        # set our list box to read only
        self.resultsList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # connect a click event to our list box
        self.resultsList.clicked.connect(self.resultChanged)
        # our text boxes will uses these values
        rowSpan = 1
        columnSpan = 2
        # add row 0 widgets, a text box and a button
        self.searchTextEdit = self.createTextEdit(False)
        grid.addWidget(self.searchTextEdit, 0, 0, rowSpan, columnSpan)

        searchPushButton = QPushButton("Search")
        searchPushButton.setFixedHeight(32)
        searchPushButton.setFixedWidth(64)
        searchPushButton.clicked.connect(self.searchButtonClicked)
        grid.addWidget(searchPushButton, 0, 2)

        # add row 1 widgets, our list box
        grid.addWidget(self.resultsList, 1, 0, 1, 3)

        # add row 2 through 9 widgets, the other text boxes
        rowCount = 2
        for col in self.columns:
            self.createRow(grid, col, rowCount, rowSpan, columnSpan)
            rowCount = rowCount + 1

    def createRow(self, grid: QGridLayout, text: str, row: int, rowSpan: int, columnSpan: int):
        # add a label to our window for this row
        grid.addWidget(self.createLabel(text.title()), row, 0)
        # create a read only text box
        textEdit = self.createTextEdit(True)
        # add the text bow to this row
        grid.addWidget(textEdit, row, 1, rowSpan, columnSpan)
        # store the widget in our dictionary for use later
        self.widgetDict[text] = textEdit

    def createTextEdit(self, readOnly: bool) -> QTextEdit:
        # create a text box and set some properties
        textEdit = QTextEdit()
        textEdit.setReadOnly(readOnly)
        textEdit.setFixedHeight(32)
        return textEdit

    def createLabel(self, text: str) -> QLabel:
        # create a label and set some properties
        label = QLabel(text)
        label.setFixedHeight(32)
        label.setFixedWidth(64)
        return label


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhooshGui(None)
    window.show()
    app.exec_()
