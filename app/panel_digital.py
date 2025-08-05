import sys
from tkinter import Spinbox
from PyQt5.QtWidgets import QAction, QMainWindow, QApplication, QSpinBox, QToolBar, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QColorDialog, QFontDialog, QMessageBox
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

       #crear barra de herramientas
        self.crear_barra_herramientas()

####FUNCIONES PARA LA PANTALLA TRNSPARENTE 
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

###FUNCIONES DE LAS HERRAMIETNAS
    def crear_barra_herramientas(self):
        barra = QToolBar("herramientas")
        barra.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, barra)

        #boton para colores
        boton_rojo = QAction("rojo", self)
        boton_rojo.triggered.connect(lambda: self.cambiar_color(QColor(255,0,0)))
        barra.addAction(boton_rojo)
        
        boton_azul = QAction("azul", self)
        boton_azul.triggered.connect(lambda: self.cambiar_color(QColor(0,0,255)))
        barra.addAction(boton_azul)

        #selector de grosor
        spinbox_grosor = QSpinBox()
        spinbox_grosor.setRange(1, 20)
        spinbox_grosor.setValue(3)
        spinbox_grosor.valueChanged.connect(self.cambiar_grosor)
        barra.addWidget(spinbox_grosor)

        #boton para borrar
        boton_borrar = QAction("Borrar", self)
        boton_borrar.triggered.connect(self.borrar_todo)
        barra.addAction(boton_borrar)

    def cambiar_color(self, color):
        self.lapiz.setColor(color)

    def cambiar_grosor(self, grosor):
        self.lapiz.setWidth(grosor)

    def borrar_todo(self):
        self.trazo = []
        self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaDibujo()
    ventana.show()
    sys.exit(app.exec_())