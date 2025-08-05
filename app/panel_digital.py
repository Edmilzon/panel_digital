import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QColorDialog, QFontDialog, QMessageBox
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor

class VentanaDibujo(QMainWindow):
    def __init__(self):
        super().__init__()
        #ventana transparente
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0,0, QApplication.desktop().screenGeometry().width(),
                        QApplication.desktop().screenGeometry().height())

        #variables para dibujar
        self.dibujando = False
        self.ultimo_punto = QPoint()
        self.trazo =[]
        self.lapiz = QPen(QColor(255,0,0),3, Qt.SolidLine)# lapiz rojo de 3px

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.lapiz)
        for punto_inicial, punto_final in self.trazo:
            painter.drawLine(punto_inicial, punto_final)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dibujando = True
            self.ultimo_punto = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.dibujando:
            self.trazo.append((self.ultimo_punto, event.pos())) # guarda el; trazo
            self.ultimo_punto = event.pos()
            self.update() #redibujar ventana
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dibujando = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaDibujo()
    ventana.show()
    sys.exit(app.exec_())