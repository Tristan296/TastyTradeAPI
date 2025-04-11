from PySide6.QtWidgets import QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

def setup_current_positions_tab(self):
    # Create a vertical layout for the Current Positions tab
    layout = QVBoxLayout()

    # Initialize the QTableWidget
    self.current_positions_table = QTableWidget()
    self.current_positions_table.setColumnCount(7)
    self.current_positions_table.setHorizontalHeaderLabels([
        "Symbol", "Quantity", "Avg Price", "Current Price", "P&L", "P&L %", "Market Value"
    ])
    self.current_positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    self.current_positions_table.setEditTriggers(QTableWidget.NoEditTriggers)
    self.current_positions_table.setSelectionBehavior(QTableWidget.SelectRows)
    self.current_positions_table.setSelectionMode(QTableWidget.SingleSelection)

    # Add the table to the layout
    layout.addWidget(self.current_positions_table)

    # Set the layout for the Current Positions tab
    self.current_positions_tab.setLayout(layout)
