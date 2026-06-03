from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
import sys

def button_clicked():
    print("الزرار اتضغط!")
app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("أول GUI!")
window.setGeometry(100, 100, 400, 300)
button = QPushButton("اضغطني!", window)
button.move(150, 130)
button.clicked.connect(button_clicked)
window.show()
sys.exit(app.exec_())