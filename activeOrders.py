from PySide6.QtWidgets import QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

def setup_active_orders_tab(self):
    # Create a vertical layout for the Active Orders tab
    layout = QVBoxLayout()

    # Initialize the QTableWidget
    self.active_orders_table = QTableWidget()
    self.active_orders_table.setColumnCount(7)
    self.active_orders_table.setHorizontalHeaderLabels([
        "Order ID", "Symbol", "Order Type", "Quantity", "Price", "Status", "Timestamp"
    ])
    self.active_orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    self.active_orders_table.setEditTriggers(QTableWidget.NoEditTriggers)
    self.active_orders_table.setSelectionBehavior(QTableWidget.SelectRows)
    self.active_orders_table.setSelectionMode(QTableWidget.SingleSelection)

    # Add the table to the layout
    layout.addWidget(self.active_orders_table)

    # Set the layout for the Active Orders tab
    self.active_orders_tab.setLayout(layout)
