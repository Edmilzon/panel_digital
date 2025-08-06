import sys
from PyQt5.QtWidgets import (QAction, QInputDialog, QMainWindow, QApplication, 
                             QSpinBox, QToolBar, QColorDialog, QFontDialog, 
                             QMessageBox, QVBoxLayout, QHBoxLayout, QWidget)
from PyQt5.QtCore import QRect, Qt, QPoint
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QFontMetrics, QBrush

class VentanaDibujo(QMainWindow):
    def __init__(self):
        super().__init__()
        #ventana transparente
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, QApplication.desktop().screenGeometry().width(),
                        QApplication.desktop().screenGeometry().height())

        #variables para dibujar
        self.dibujando = False
        self.ultimo_punto = QPoint()
        self.trazo = []
        self.lapiz = QPen(QColor(255, 0, 0), 3, Qt.SolidLine)  # lapiz rojo de 3px

        #variables para texto
        self.textos = []
        self.texto_actual = ""
        self.pos_texto = QPoint(100, 100)
        self.editando_texto = False
        self.texto_seleccionado = -1
        self.arrastrando_texto = False
        self.fuente = QFont("Arial", 12)

        #figuras geometricas
        self.figura_actual = "linea"
        self.punto_inicio = QPoint()
        self.dibujando_figura = False
        self.figuras = []  # Lista para almacenar todas las figuras
        self.figura_seleccionada = -1
        self.arrastrando_figura = False
        self.redimensionando = False
        self.punto_inicio_redimension = QPoint()
        self.borrando = False
        
        #modos
        self.modo = "lapiz"

        #crear barra de herramientas
        self.crear_barra_herramientas()

    def paintEvent(self, event):
        painter = QPainter(self)

        #dibujar trazos
        painter.setPen(self.lapiz)
        for punto_inicial, punto_final in self.trazo:
            painter.drawLine(punto_inicial, punto_final)
                
        # Dibujar textos
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
                
        # Dibujar figuras guardadas
        for figura in self.figuras:
            tipo, inicio, fin, color, grosor = figura
            pen = QPen(color, grosor)
            painter.setPen(pen)
            self.dibujar_figura(painter, tipo, inicio, fin)

        # Dibujar preview de figura en curso
        if self.dibujando_figura:
            painter.setPen(self.lapiz)
            self.dibujar_figura_preview(painter, self.punto_inicio, self.mouse_pos)
    
        # Dibujar indicador de borrador si está activo
        if self.modo == "borrador":
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.setBrush(QBrush(QColor(255, 0, 0, 50)))  # Rojo semi-transparente
            painter.drawEllipse(self.mouse_pos, 15, 15)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.modo == "lapiz":
                self.dibujando = True
                self.ultimo_punto = event.pos()
            elif self.modo == "texto":
                self.agregar_texto(event.pos())
            elif self.modo == "mover":
                # Verificar si se hace clic en una figura existente
                figura_idx = self.seleccionar_figura(event.pos())
                if figura_idx != -1:
                    self.figura_seleccionada = figura_idx
                    self.arrastrando_figura = True
                    self.ultimo_punto = event.pos()
            elif self.modo == "figura":
                self.dibujando_figura = True
                self.punto_inicio = event.pos()
            elif self.modo == "redimensionar":
                figura_idx = self.seleccionar_figura(event.pos())
                if figura_idx != -1:
                    self.figura_seleccionada = figura_idx
                    self.redimensionando = True
                    self.punto_inicio_redimension = event.pos()
            elif self.modo == "borrador":
                self.borrar_en_posicion(event.pos())
    
    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        if self.dibujando:
            self.trazo.append((self.ultimo_punto, event.pos()))  # guarda el trazo
            self.ultimo_punto = event.pos()
            self.update()  # redibujar ventana
        elif self.arrastrando_texto and self.texto_seleccionado != -1:
            try:
                pos, texto, color, fuente = self.textos[self.texto_seleccionado]
                self.textos[self.texto_seleccionado] = (event.pos(), texto, color, fuente)
            except ValueError:
                pos, texto, color = self.textos[self.texto_seleccionado]
                self.textos[self.texto_seleccionado] = (event.pos(), texto, color)
            self.update()
        elif self.dibujando_figura:
            self.update()  # Para mostrar preview de la figura
        elif self.arrastrando_figura and self.figura_seleccionada != -1:
            # Calcular el desplazamiento
            desplazamiento = event.pos() - self.ultimo_punto
            self.mover_figura(self.figura_seleccionada, desplazamiento)
            self.ultimo_punto = event.pos()
            self.update()
        elif self.redimensionando and self.figura_seleccionada != -1:
            self.redimensionar_figura(self.figura_seleccionada, event.pos())
        elif self.modo == "borrador" and event.buttons() & Qt.LeftButton:
            self.borrar_en_posicion(event.pos())
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dibujando = False
            self.arrastrando_texto = False
            if self.editando_texto and self.texto_actual:
                self.guardar_texto()
            if self.dibujando_figura:
                self.agregar_figura(event.pos())
                self.dibujando_figura = False
            if self.arrastrando_figura:
                self.arrastrando_figura = False
                self.figura_seleccionada = -1
            if self.redimensionando:
                self.redimensionando = False
                self.figura_seleccionada = -1
    
    def mouseDoubleClickEvent(self, event):
        if self.modo == "mover":
            for i, item in enumerate(self.textos):
                try:
                    pos, texto, color, fuente = item
                    fm = QFontMetrics(fuente)
                except ValueError:
                    pos, texto, color = item
                    fm = QFontMetrics(self.fuente)
                
                rect = QRect(pos.x(), pos.y() - fm.height(), 
                            fm.width(texto), fm.height())
                if rect.contains(event.pos()):
                    self.editar_texto(i)
                    break
    
    def keyPressEvent(self, event):
        if self.editando_texto:
            if event.key() == Qt.Key_Return:
                self.guardar_texto()
            elif event.key() == Qt.Key_Escape:
                self.editando_texto = False
                self.texto_actual = ""
                self.update()
            elif event.key() == Qt.Key_Backspace:
                self.texto_actual = self.texto_actual[:-1]
            else:
                self.texto_actual += event.text()
            self.update()

    def crear_barra_herramientas(self):
        barra = QToolBar("herramientas")
        barra.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, barra)

        #boton para lapiz
        boton_lapiz = QAction("Lápiz", self)
        boton_lapiz.triggered.connect(lambda: self.cambiar_modo("lapiz"))
        barra.addAction(boton_lapiz)

        #selector de grosor
        spinbox_grosor = QSpinBox()
        spinbox_grosor.setRange(1, 20)
        spinbox_grosor.setValue(3)
        spinbox_grosor.valueChanged.connect(self.cambiar_grosor)
        barra.addWidget(spinbox_grosor)

        #boton para texto
        boton_texto = QAction("Texto", self)
        boton_texto.triggered.connect(lambda: self.cambiar_modo("texto"))
        barra.addAction(boton_texto)

        boton_mover = QAction("Mover", self)
        boton_mover.triggered.connect(lambda: self.cambiar_modo("mover"))
        barra.addAction(boton_mover)

        #boton para colores
        boton_rojo = QAction("Rojo", self)
        boton_rojo.triggered.connect(lambda: self.cambiar_color(QColor(255, 0, 0)))
        barra.addAction(boton_rojo)
        
        boton_azul = QAction("Azul", self)
        boton_azul.triggered.connect(lambda: self.cambiar_color(QColor(0, 0, 255)))
        barra.addAction(boton_azul)

        boton_verde = QAction("Verde", self)
        boton_verde.triggered.connect(lambda: self.cambiar_color(QColor(0, 255, 0)))
        barra.addAction(boton_verde)

        boton_negro = QAction("Negro", self)
        boton_negro.triggered.connect(lambda: self.cambiar_color(QColor(0, 0, 0)))
        barra.addAction(boton_negro)

        #selector de color personalizado
        boton_color = QAction("Color", self)
        boton_color.triggered.connect(self.seleccionar_color)
        barra.addAction(boton_color)

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

        #botones para figuras geometricas
        boton_linea = QAction("Línea", self)
        boton_linea.triggered.connect(lambda: self.cambiar_figura("linea"))
        barra.addAction(boton_linea)

        boton_cuadrado = QAction("Cuadrado", self)
        boton_cuadrado.triggered.connect(lambda: self.cambiar_figura("cuadrado"))
        barra.addAction(boton_cuadrado)

        boton_circulo = QAction("Círculo", self)
        boton_circulo.triggered.connect(lambda: self.cambiar_figura("circulo"))
        barra.addAction(boton_circulo)

        boton_redimensionar = QAction("Redimensionar", self)
        boton_redimensionar.triggered.connect(lambda: self.cambiar_modo("redimensionar"))
        barra.addAction(boton_redimensionar)

        #boton para salir
        boton_salir = QAction("Salir", self)
        boton_salir.triggered.connect(self.close)
        barra.addAction(boton_salir)

        boton_borrador = QAction("Borrador", self)
        boton_borrador.triggered.connect(lambda: self.cambiar_modo("borrador"))
        barra.addAction(boton_borrador)

        barra.setMovable(True)

    def cambiar_grosor(self, grosor):
        self.lapiz.setWidth(grosor)

    def cambiar_color(self, color):
        self.lapiz.setColor(color)

    def seleccionar_color(self):
        color = QColorDialog.getColor(self.lapiz.color(), self)
        if color.isValid():
            self.lapiz.setColor(color)

    def borrar_todo(self):
        reply = QMessageBox.question(self, 'Confirmar', 
                                   '¿Estás seguro de que quieres borrar todo?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.trazo = []
            self.textos = []
            self.figuras = []
            self.update()
    
    def cambiar_modo(self, modo):
        self.modo = modo
        if modo == "texto":
            self.setCursor(Qt.IBeamCursor)
        elif modo == "mover":
            self.setCursor(Qt.OpenHandCursor)
            # Cambiar cursor a mano abierta para indicar que se pueden mover figuras
        elif modo == "figura":
            self.setCursor(Qt.CrossCursor)
        elif modo == "redimensionar":
            self.setCursor(Qt.SizeAllCursor)
        elif modo == "borrador":
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    
    def agregar_texto(self, posicion):
        texto, ok = QInputDialog.getText(self, "Añadir Texto", "Escribe texto:")
        if ok and texto:
            self.textos.append((posicion, texto, self.lapiz.color(), QFont(self.fuente)))
            self.update()

    def guardar_texto(self):
        if self.texto_actual:
            self.textos.append((
                self.pos_texto, 
                self.texto_actual, 
                self.lapiz.color(), 
                QFont(self.fuente)
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
            try:
                pos, texto, color, fuente = self.textos[indice]
                self.textos.pop(indice)
                self.editando_texto = True
                self.texto_actual = texto
                self.pos_texto = pos
                self.fuente = QFont(fuente)
            except ValueError:
                pos, texto, color = self.textos[indice]
                self.textos.pop(indice)
                self.editando_texto = True
                self.texto_actual = texto
                self.pos_texto = pos
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

    def cambiar_figura(self, figura):
        self.figura_actual = figura
        self.modo = "figura"
        self.setCursor(Qt.CrossCursor)

    def agregar_figura(self, punto_final):
        self.figuras.append((
            self.figura_actual,
            self.punto_inicio,
            punto_final,
            self.lapiz.color(),
            self.lapiz.width()
        ))
        self.update()

    def dibujar_figura_preview(self, painter, inicio, fin):
        if self.figura_actual == "linea":
            painter.drawLine(inicio, fin)
        elif self.figura_actual == "cuadrado":
            rect = QRect(inicio, fin)
            painter.drawRect(rect)
        elif self.figura_actual == "circulo":
            rect = QRect(inicio, fin)
            painter.drawEllipse(rect)

    def dibujar_figura(self, painter, tipo, inicio, fin):
        if tipo == "linea":
            painter.drawLine(inicio, fin)
        elif tipo == "cuadrado":
            rect = QRect(inicio, fin)
            painter.drawRect(rect)
        elif tipo == "circulo":
            rect = QRect(inicio, fin)
            painter.drawEllipse(rect)

    def seleccionar_figura(self, pos):
        for i, figura in enumerate(self.figuras):
            tipo, inicio, fin, color, grosor = figura
            if self.figura_contiene_punto(tipo, inicio, fin, pos):
                return i
        return -1

    def figura_contiene_punto(self, tipo, inicio, fin, punto):
        if tipo == "linea":
            # Verificar si el punto está cerca de la línea
            distancia = self.distancia_punto_linea(inicio, fin, punto)
            return distancia < 10
        elif tipo == "cuadrado":
            rect = QRect(inicio, fin)
            return rect.contains(punto)
        elif tipo == "circulo":
            rect = QRect(inicio, fin)
            return rect.contains(punto)
        return False

    def distancia_punto_linea(self, inicio, fin, punto):
        # Cálculo de distancia de punto a línea
        x1, y1 = inicio.x(), inicio.y()
        x2, y2 = fin.x(), fin.y()
        x0, y0 = punto.x(), punto.y()
        
        if x2 == x1 and y2 == y1:
            return ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5
        
        t = ((x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1)) / ((x2 - x1) ** 2 + (y2 - y1) ** 2)
        t = max(0, min(1, t))
        
        x_proj = x1 + t * (x2 - x1)
        y_proj = y1 + t * (y2 - y1)
        
        return ((x0 - x_proj) ** 2 + (y0 - y_proj) ** 2) ** 0.5

    def mover_figura(self, indice, desplazamiento):
        if 0 <= indice < len(self.figuras):
            tipo, inicio, fin, color, grosor = self.figuras[indice]
            nuevo_inicio = inicio + desplazamiento
            nuevo_fin = fin + desplazamiento
            self.figuras[indice] = (tipo, nuevo_inicio, nuevo_fin, color, grosor)
            self.update()

    def redimensionar_figura(self, indice, nuevo_fin):
        if 0 <= indice < len(self.figuras):
            tipo, inicio, fin, color, grosor = self.figuras[indice]
            self.figuras[indice] = (tipo, inicio, nuevo_fin, color, grosor)
            self.update()

    def dibujar_handles_redimension(self, painter, figura):
        tipo, inicio, fin, color, grosor = figura
        # Dibujar pequeños cuadrados en las esquinas para redimensionar
        handle_size = 6
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        painter.setBrush(QColor(255, 255, 255))
        
        if tipo == "cuadrado" or tipo == "circulo":
            rect = QRect(inicio, fin)
            # Esquinas del rectángulo
            painter.drawRect(QRect(rect.topLeft().x() - handle_size//2, 
                                  rect.topLeft().y() - handle_size//2, 
                                  handle_size, handle_size))
            painter.drawRect(QRect(rect.bottomRight().x() - handle_size//2, 
                                  rect.bottomRight().y() - handle_size//2, 
                                  handle_size, handle_size))
        elif tipo == "linea":
            # Puntos finales de la línea
            painter.drawRect(QRect(inicio.x() - handle_size//2, 
                                  inicio.y() - handle_size//2, 
                                  handle_size, handle_size))
            painter.drawRect(QRect(fin.x() - handle_size//2, 
                                  fin.y() - handle_size//2, 
                                  handle_size, handle_size))

    def borrar_en_posicion(self, pos):
        # Borrar trazos
        trazos_a_borrar = []
        for i, (inicio, fin) in enumerate(self.trazo):
            if self.punto_cerca_de_linea(inicio, fin, pos, 10):
                trazos_a_borrar.append(i)
        
        # Borrar en orden inverso para no afectar los índices
        for i in reversed(trazos_a_borrar):
            del self.trazo[i]
        
        # Borrar textos
        textos_a_borrar = []
        for i, item in enumerate(self.textos):
            try:
                texto_pos, texto, color, fuente = item
            except ValueError:
                texto_pos, texto, color = item
            
            fm = QFontMetrics(fuente if 'fuente' in locals() else self.fuente)
            rect = QRect(texto_pos.x(), 
                        texto_pos.y() - fm.height(), 
                        fm.width(texto), 
                        fm.height())
            if rect.contains(pos):
                textos_a_borrar.append(i)
        
        # Borrar en orden inverso
        for i in reversed(textos_a_borrar):
            del self.textos[i]
        
        # Borrar figuras
        figuras_a_borrar = []
        for i, figura in enumerate(self.figuras):
            tipo, inicio, fin, color, grosor = figura
            if self.figura_contiene_punto(tipo, inicio, fin, pos):
                figuras_a_borrar.append(i)
        
        # Borrar en orden inverso
        for i in reversed(figuras_a_borrar):
            del self.figuras[i]
        
        self.update()

    def punto_cerca_de_linea(self, inicio, fin, punto, distancia_maxima):
        return self.distancia_punto_linea(inicio, fin, punto) < distancia_maxima

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaDibujo()
    ventana.show()
    sys.exit(app.exec_())