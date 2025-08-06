from pydoc import text
import sys
from tkinter import Spinbox
from PyQt5.QtWidgets import QAction, QInputDialog, QMainWindow, QApplication, QSpinBox, QToolBar, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QColorDialog, QFontDialog, QMessageBox
from PyQt5.QtCore import QRect, Qt, QPoint
from PyQt5.QtGui import QFont, QPainter, QPen, QColor

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

        #variables para texto
        self.textos = []
        self.texto_actual = ""
        self.pos_texto = QPoint(100, 100)
        self.editando_texto = False
        self.texto_seleccionado = -1
        self.arrastrando_texto = False
        self.fuente = QFont("Arial", 12)
        
        #modos
        self.modo = "lapiz"

       #crear barra de herramientas
        self.crear_barra_herramientas()

####FUNCIONES PARA LA PANTALLA TRNSPARENTE 
    def paintEvent(self, event):
        painter = QPainter(self)

        #dibujar trazos
        painter.setPen(self.lapiz)
        for punto_inicial, punto_final in self.trazo:
            painter.drawLine(punto_inicial, punto_final)
                
        # Dibujar textos (compatible con versiones antiguas y nuevas)
        for item in self.textos:
            try:
                # Intenta desempaquetar 4 valores
                pos, texto, color, fuente = item
                painter.setFont(fuente)
            except ValueError:
                # Si falla, usa 3 valores (posición, texto, color) con fuente por defecto
                pos, texto, color = item
                painter.setFont(self.fuente)
            
            painter.setPen(QPen(color))
            painter.drawText(pos, texto)
                
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.modo == "lapiz":
                self.dibujando = True
                self.ultimo_punto = event.pos()
            elif self.modo == "texto":
                self.agregar_texto(event.pos())
            elif self.modo == "mover":
                self.seleccionar_texto(event.pos())
    
    def mouseMoveEvent(self, event):
        if self.dibujando:
            self.trazo.append((self.ultimo_punto, event.pos())) # guarda el; trazo
            self.ultimo_punto = event.pos()
            self.update() #redibujar ventana
        elif self.arrastrando_texto and self.texto_seleccionado != -1:
            pos, texto, color, fuente = self.textos[self.texto_seleccionado]
            self.textos[self.texto_seleccionado] = (event.pos(), texto, color, fuente)
            self.update()
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dibujando = False
            self.arrastrando_texto = False
            if self.editando_texto and self.texto_actual:
                self.guardar_texto()
    
    def mouseDoubleClickEvent(self,event):
        if self.modo == "mover":
            for i, (pos, texto, color, fuente) in enumerate(self.textos):
                rect = QRect(pos.x(), pos.y() - fuente.pointSize(), 
                            self.fontMetrics().width(texto),
                            fuente.pointSize() + 5)
                if rect.contains(event.pos()):
                    self.editando_texto(i)
                    break
    def keyPressEvent(self, event):
        if self.editando_texto:
            if event.key() == Qt.Key_Return:
                self.guardar_texto()
            elif event.key() == Qt.Key_Backspace:
                self.texto_actual = self.texto_actual[:-1]
            else:
                self.texto_actual += event.text()
            self.update()

###BARRA DE HERRAMIENTAS
    def crear_barra_herramientas(self):
        barra = QToolBar("herramientas")
        barra.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, barra)

        #boton para lapiz
        boton_lapiz = QAction("lapiz", self)
        boton_lapiz.triggered.connect(lambda: self.cambiar_modo("lapiz"))
        barra.addAction(boton_lapiz)

        #selector de grosor
        spinbox_grosor = QSpinBox()
        spinbox_grosor.setRange(1, 20)
        spinbox_grosor.setValue(3)
        spinbox_grosor.valueChanged.connect(self.cambiar_grosor)
        barra.addWidget(spinbox_grosor)

        #boton para texto
        boton_texto = QAction("texto", self)
        boton_texto.triggered.connect(lambda: self.cambiar_modo("texto"))
        barra.addAction(boton_texto)

        boton_mover = QAction("mover", self)
        boton_mover.triggered.connect(lambda: self.cambiar_modo("mover"))
        barra.addAction(boton_mover)

        #boton para colores
        boton_rojo = QAction("rojo", self)
        boton_rojo.triggered.connect(lambda: self.cambiar_color(QColor(255,0,0)))
        barra.addAction(boton_rojo)
        
        boton_azul = QAction("azul", self)
        boton_azul.triggered.connect(lambda: self.cambiar_color(QColor(0,0,255)))
        barra.addAction(boton_azul)

        #tamanio de fuente
        spinbox_tamanio = QSpinBox()
        spinbox_tamanio.setRange(8, 72)
        spinbox_tamanio.setValue(12)
        spinbox_tamanio.valueChanged.connect(self.cambiar_tamanio_fuente)
        barra.addWidget(spinbox_tamanio)

        # boton para fuente 
        boton_fuente = QAction("Fuente", self)
        boton_fuente.triggered.connect(self.seleccionar_fuente)
        barra.addAction(boton_fuente)

        #boton para borrar
        boton_borrar = QAction("Borrar", self)
        boton_borrar.triggered.connect(self.borrar_todo)
        barra.addAction(boton_borrar)


        barra.setMovable(True)
###FUNCIONES DE LAS HERRAMIETNAS

    ##funciones para el lapiz
    def cambiar_grosor(self, grosor):
        self.lapiz.setWidth(grosor)


    #para los dos
    def cambiar_color(self, color):
        self.lapiz.setColor(color)

    def borrar_todo(self):
        self.trazo = []
        self.textos = []
        self.update()
    
    def cambiar_modo(self, modo):
        self.modo = modo
        if modo == "texto":
            self.setCursor(Qt.IBeamCursor)
        elif modo == "mover":
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    
    #funciones para el texto
    def agregar_texto(self, posicion):
        texto, ok = QInputDialog.getText(self, "Añadir Texto", "Escribe texto:")
        if ok and texto:
            self.textos.append((posicion, texto, self.lapiz.color()))
            self.update()

    def iniciar_texto(self, pos):
        self.editando_texto = True
        self.texto_actual = ""
        self.pos_texto = pos
        self.update()
    
    def guardar_texto(self):
        if self.texto_actual:
            self.textos.append((
                self.pos_texto, 
                self.texto_actual, 
                self.lapiz.color(), 
                QFont(self.fuente)  # Guarda una COPIA de la fuente actual
            ))
        self.editando_texto = False
        self.texto_actual = ""
        self.update()
    
    def seleccionar_texto(self, pos):
        for i, item in enumerate(self.textos):
            try:
                texto_pos, texto, color, fuente = item
                current_font = fuente
            except ValueError:
                texto_pos, texto, color = item
                current_font = self.fuente
            
            fm = QFontMetrics(current_font)
            rect = QRect(texto_pos.x(), 
                        texto_pos.y() - fm.height(), 
                        fm.width(texto), 
                        fm.height())
            
            if rect.contains(pos):
                self.texto_seleccionado = i
                self.arrastrando_texto = True
                self.update()
                return
        
        self.texto_seleccionado = -1
        self.update()

    def editar_texto(self, indice):
        if 0 <= indice < len(self.textos):
            pos, texto, color, fuente = self.textos[indice]
            self.textos.pop(indice)
            self.editando_texto = True
            self.texto_actual = texto
            self.pos_texto = pos
            self.fuente = QFont(fuente)
            self.setFocus()
            self.update()
    
    def cambiar_tamanio_fuente(self, tamanio):
        self.fuente.setPointSize(tamanio)
        self.update()

    def seleccionar_fuente(self):
        fuente, ok = QFontDialog.getFont(self.fuente, self)
        if ok:
            self.fuente = fuente
            self.update()
    
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaDibujo()
    ventana.show()
    sys.exit(app.exec_())