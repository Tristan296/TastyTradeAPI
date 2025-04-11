import sys
from tastytrade import DXLinkStreamer, Session
from tastytrade.dxfeed import Greeks, Quote
from tastytrade.instruments import get_option_chain
from typing import Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from qasync import QEventLoop
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QMessageBox,
    QVBoxLayout, QWidget, QHeaderView, QPushButton, QInputDialog, QTabWidget
)
import asyncio
from helpers import get_tasty_daily
from canvas import ProfitLossCanvas
from trade_assister import * 
import os

# import modern themes:
from qdarkstyle import load_stylesheet
os.environ["QT_FONT_DPI"] = "96"  # Adjust for High DPI scaling

def get_session(session: Session) -> DXLinkStreamer:
    return(DXLinkStreamer(session, reconnect_args=(session,)))
    
def reformat_model(model: Dict[str, Any]) -> Dict[str, Any]:
    reformatted = model.copy()
    try:
        if 'volatility' in reformatted and reformatted['volatility'] is not None:
            reformatted['volatility'] = float(reformatted['volatility']) * 100

        for greek in ['delta', 'gamma', 'theta', 'vega', 'rho']:
            if greek in reformatted and reformatted[greek] is not None:
                reformatted[greek] = float(reformatted[greek]) * 100

        for key, value in reformatted.items():
            if isinstance(value, Decimal):
                reformatted[key] = float(value)

        if 'time' in reformatted and reformatted['time'] is not None:
            timestamp_ms = int(reformatted['time'])
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            reformatted['time'] = dt.isoformat() + 'Z'
    except (ValueError, TypeError, KeyError) as e:
        print(f"Error while reformating model: {e}")
    return reformatted


class TastyTraderAPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TastyTrade Trading App")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(load_stylesheet()) 

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Initialize tabs
        self.market_data_tab = QWidget()
        self.active_orders_tab = QWidget()
        self.positions_tab = QWidget()
        self.place_order_tab = QWidget()
        self.analytics_tab = QWidget()

        # Add tabs to the QTabWidget
        self.tabs.addTab(self.market_data_tab, "Market Data")
        self.tabs.addTab(self.active_orders_tab, "Active Orders")
        self.tabs.addTab(self.positions_tab, "Positions")
        self.tabs.addTab(self.place_order_tab, "Place Order")
        self.tabs.addTab(self.analytics_tab, "Analytics")

        # Set up each tab
        self.setup_market_data_tab()
        self.setup_place_order_tab()
        self.setup_analytics_tab()
        self.populate_table([])
        self.setup_positions_tab([])
        self.setup_active_orders_tab([])

    def setup_place_order_tab(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Event Symbol", "Quantity", "Price", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Add buttons for purchase option and close position
        purchase_button = QPushButton("Purchase Option")
        purchase_button.clicked.connect(self.handle_purchase_strategy)
        purchase_button.clicked.connect(lambda: purchase_button.hide())
        
        layout.addWidget(self.table)
        layout.addWidget(purchase_button)

        self.place_order_tab.setLayout(layout)

    def handle_purchase_strategy(self):
        layout = self.place_order_tab.layout()

        # Add limit order button
        limit_order_button = QPushButton("Limit Order")
        limit_order_button.clicked.connect(lambda: self.handle_purchase_option("Limit Order"))
        layout.addWidget(limit_order_button)

        # Add market order button
        market_order_button = QPushButton("Market Order")
        market_order_button.clicked.connect(lambda: self.handle_purchase_option("Market Order"))
        layout.addWidget(market_order_button)

        # Add smart order button
        smart_order_button = QPushButton("Smart Order")
        smart_order_button.clicked.connect(lambda: self.handle_purchase_option("Smart Order"))
        layout.addWidget(smart_order_button)



    def setup_positions_tab(self, data):
        self.current_positions_table = QTableWidget()
        self.current_positions_table.setColumnCount(7)
        self.current_positions_table.setHorizontalHeaderLabels([
            "Symbol", "Quantity", "Avg Price", "Current Price", "PnL", "PnL %", "Market Value"
        ])
        self.current_positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.current_positions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.current_positions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.current_positions_table.setSelectionMode(QTableWidget.SingleSelection)

        self.current_positions_table.setRowCount(len(data))
        for row_idx, entry in enumerate(data):
            self.current_positions_table.setItem(row_idx, 0, QTableWidgetItem(entry.get("symbol", "N/A")))
            self.current_positions_table.setItem(row_idx, 1, QTableWidgetItem(str(entry.get("quantity", "N/A"))))
            self.current_positions_table.setItem(row_idx, 2, QTableWidgetItem(str(entry.get("avg_price", "N/A"))))
            self.current_positions_table.setItem(row_idx, 3, QTableWidgetItem(str(entry.get("current_price", "N/A"))))
            self.current_positions_table.setItem(row_idx, 4, QTableWidgetItem(str(entry.get("pnl", "N/A"))))
            self.current_positions_table.setItem(row_idx, 5, QTableWidgetItem(str(entry.get("pnl_percent", "N/A"))))
            self.current_positions_table.setItem(row_idx, 6, QTableWidgetItem(str(entry.get("market_value", "N/A"))))

    def setup_active_orders_tab(self, data):
        self.active_orders_table = QTableWidget()
        self.active_orders_table.setRowCount(len(data))
        for row_idx, entry in enumerate(data):
            self.active_orders_table.setItem(row_idx, 0, QTableWidgetItem(str(entry.get("order_id", "N/A"))))
            self.active_orders_table.setItem(row_idx, 1, QTableWidgetItem(entry.get("symbol", "N/A")))
            self.active_orders_table.setItem(row_idx, 2, QTableWidgetItem(entry.get("order_type", "N/A")))
            self.active_orders_table.setItem(row_idx, 3, QTableWidgetItem(str(entry.get("quantity", "N/A"))))
            self.active_orders_table.setItem(row_idx, 4, QTableWidgetItem(str(entry.get("price", "N/A"))))
            self.active_orders_table.setItem(row_idx, 5, QTableWidgetItem(entry.get("status", "N/A")))
            self.active_orders_table.setItem(row_idx, 6, QTableWidgetItem(entry.get("timestamp", "N/A")))
        
    def setup_market_data_tab(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Event Symbol", "Delta", "Gamma", "Theta", "Implied Volatility", "Vega", "Rho",
            "Bid Price", "Ask Price"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        layout.addWidget(self.table)
        self.market_data_tab.setLayout(layout)


    def setup_analytics_tab(self):
        layout = QVBoxLayout()
        self.profit_loss_canvas = ProfitLossCanvas(self)
        layout.addWidget(self.profit_loss_canvas)
        self.analytics_tab.setLayout(layout)
        
    def populate_table(self, table_data):
        self.table.setRowCount(len(table_data))
        for row_idx, entry in enumerate(table_data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(entry.get("event_symbol", "N/A")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(entry.get("delta", "N/A"))))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(entry.get("gamma", "N/A"))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(entry.get("theta", "N/A"))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(entry.get("imp_vol", "N/A"))))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(entry.get("vega", "N/A"))))
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(entry.get("rho", "N/A"))))
            self.table.setItem(row_idx, 7, QTableWidgetItem(str(entry.get("bid_price", "N/A"))))
            self.table.setItem(row_idx, 8, QTableWidgetItem(str(entry.get("ask_price", "N/A"))))

        self.table.viewport().update()



    def handle_purchase_option(self, strategy: str):
        if (strategy == "Limit Order"):
            # Implement limit order logic
            QMessageBox.information(self, "Limit Order", "Limit order functionality is not implemented yet.")
        elif (strategy == "Market Order"):
            # Implement market order logic
            QMessageBox.information(self, "Market Order", "Market order functionality is not implemented yet.")
        elif (strategy == "Smart Order"):
            # Implement smart order logic
            QMessageBox.information(self, "Smart Order", "Smart order functionality is not implemented yet.")
        else:
            QMessageBox.warning(self, "Invalid Strategy", "Please select a valid purchase strategy.")
    

    def handle_close_position(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Close Position", "Please select an option from the table.")
            return

    def handle_display_payoff_diagram(self):
        QMessageBox.information(self, "Payoff Diagram", "Payoff diagram functionality is not implemented yet.")

async def fetch_and_display_data(window: TastyTraderAPI):
    
    symbol = "SPX"
    # use the .env file to get the username and password
    username = os.getenv("TASTY_USERNAME")
    password = os.getenv("TASTY_PASSWORD")
    if not username or not password:
        print("[DEBUG] Username and password not found in environment variables.")
        return
    
    session = Session(username=username, password=password)
    if not session.validate():
        print("[DEBUG] Session validation failed.")
        return
    
    today = await asyncio.to_thread(get_tasty_daily)
    print("[DEBUG] Today's date: {}".format(today))

    chain = await asyncio.to_thread(get_option_chain, session, symbol)
    if not chain or today not in chain:
        print("[DEBUG] No options available for today.")
        return

    subs_list = [option.streamer_symbol for option in chain[today]]
    print(f"[DEBUG] Subscribing to {len(subs_list)} symbols.")
    greeks_data, quotes_data = await fetch_streamer_data(session, subs_list)

    if not greeks_data or not quotes_data:
        print("[DEBUG] No data received from streamer.")
        return

    table_data = prepare_table_data(chain[today], greeks_data, quotes_data)
    display_table_data(window, table_data)


async def fetch_streamer_data(session, subs_list):
    streamer = await DXLinkStreamer(session, reconnect_args=(session,))
    try:
        await streamer.subscribe(Greeks, subs_list)
        greeks_events = await asyncio.gather(*[streamer.get_event(Greeks) for _ in subs_list])
        print(f"[DEBUG] Received {len(greeks_events)} Greeks events.")

        await streamer.subscribe(Quote, subs_list)
        quotes = await asyncio.gather(*[streamer.get_event(Quote) for _ in subs_list])
        print(f"[DEBUG] Received {len(quotes)} Quote events.")
    finally:
        await streamer.unsubscribe(Greeks, subs_list)
        await streamer.unsubscribe(Quote, subs_list)
        await streamer.close()

    greeks_data = [reformat_model(g.__dict__) for g in greeks_events if g]
    quotes_data = [
        {
            "symbol": q.event_symbol,
            "bid_price": q.bid_price if q.bid_price is not None else "N/A",
            "ask_price": q.ask_price if q.ask_price is not None else "N/A",
        }
        for q in quotes if q
    ]
    return greeks_data, quotes_data


def prepare_table_data(options, greeks_data, quotes_data):
    table_data = []
    for option, greeks, quote in zip(options, greeks_data, quotes_data):
        if greeks and quote:
            table_data.append({
                "event_symbol": option.symbol,
                "delta": round(greeks.get("delta", 0), 2) if "delta" in greeks else "N/A",
                "gamma": round(greeks.get("gamma", 0), 2) if "gamma" in greeks else "N/A",
                "theta": round(greeks.get("theta", 0), 2) if "theta" in greeks else "N/A",
                "imp_vol": round(greeks.get("volatility", 0), 2) if "volatility" in greeks else "N/A",
                "vega": round(greeks.get("vega", 0), 2) if "vega" in greeks else "N/A",
                "rho": round(greeks.get("rho", 0), 2) if "rho" in greeks else "N/A",
                "bid_price": quote.get("bid_price", "N/A") if "bid_price" in quote else "N/A",
                "ask_price": quote.get("ask_price", "N/A") if "ask_price" in quote else "N/A",
            })
    print(f"[DEBUG] Prepared table data with {len(table_data)} rows.")
    return table_data



def display_table_data(window, table_data):
    if table_data:
        print("[DEBUG] Populating table with data: {}".format(table_data))
        window.populate_table(table_data)
    else:
        print("[DEBUG] No data available to display.")
        QMessageBox.warning(window, "No Data", "No data available to display.")
  

def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = TastyTraderAPI()
    window.show()

    loop.create_task(fetch_and_display_data(window))
    loop.run_forever()


if __name__ == "__main__":
    main()
  