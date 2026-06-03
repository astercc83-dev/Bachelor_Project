import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
import pyqtgraph as pg
from PyQt5.QtCore import QTimer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_window.ui", self)

        # إعداد الـ Graph
        self.graph = pg.PlotWidget()
        self.graphWidget.setLayout(__import__('PyQt5.QtWidgets', fromlist=['QVBoxLayout']).QVBoxLayout())
        self.graphWidget.layout().addWidget(self.graph)
        self.graph.setTitle("Real-Time Signal")
        self.graph.setLabel('left', 'Voltage (V)')
        self.graph.setLabel('bottom', 'Time (ms)')
        self.graph.setYRange(-10, 10)

        # البيانات
        self.x_data = list(range(100))
        self.y_data = [0.0] * 100
        self.curve = self.graph.plot(self.x_data, self.y_data, pen='g')

        # Timer for updating the Graph
        self.timer = QTimer()
        """ 
        when the timer starts(timer.timeout), run the function
        update_graph.
        """
        self.timer.timeout.connect(self.update_graph)

        """
        pushButton is a object name in Qt Designer, i can change it
        there if needed, the two lines below means, when the pushButton
        is clicked it should be conneted to the function start_clicked, 
        that we made , we can here in this function do what ever we want 
        when this Button clicked. and the same with pushButton_2 
        """
        self.pushButton.clicked.connect(self.start_clicked)
        self.pushButton_2.clicked.connect(self.stop_clicked)
    
    def update_graph(self):
        ## new_value = task.read()  # قرا من الـ PXI ##
        # بيولّد data جديدة كل مرة (هنا هنحط data من الـ PXI بعدين)
        # new_value will represent a random Voltage value here.
        new_value = np.random.uniform(-5, 5) # generates random num bet. -5 , 5.
        self.y_data.insert(0, new_value)  # ضيف في الشمال
        self.y_data.pop()   # امسح من اليمين
        #self.y_data.append(new_value)
        #self.y_data = self.y_data[-100:]
        self.curve.setData(self.x_data, self.y_data)
    
    def start_clicked(self):
        #print("Start!")
        """ 
        Using the function update_graph in the timer to update
        the Graph each 50 ms (20 times per second)
        """
        self.timer.start(50)  # حدّث كل 50ms

    
    def stop_clicked(self):
        #print("Stop!")
        self.timer.stop()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())