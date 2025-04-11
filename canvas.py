from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ProfitLossCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

    def plot_profit_loss(self, strikes, profits):
        self.ax.clear()
        self.ax.plot(strikes, profits, label='P/L')
        self.ax.set_title('Profit/Loss Chart')
        self.ax.set_xlabel('Underlying Price')
        self.ax.set_ylabel('Profit/Loss')
        self.ax.legend()
        self.draw()
        self.ax.grid(True)
    
    