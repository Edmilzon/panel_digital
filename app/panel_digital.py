import sys
from PyQt5.QtWidgets import (QAction, QInputDialog, QMainWindow, QApplication, 
                             QSpinBox, QToolBar, QColorDialog, QFontDialog, 
                             QMessageBox, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QPushButton, QFrame, QButtonGroup, QRadioButton, QSpacerItem)
from PyQt5.QtCore import QRect, Qt, QPoint, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QFontMetrics, QBrush, QIcon, QPixmap, QPalette
from PyQt5.QtWidgets import QSizePolicy

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
        self.panel_activo = True  # True = panel activo, False = fondo activo
        self.panel_colapsado = False
        self.panel_expandido = True

        #crear barra de herramientas
        self.crear_interfaz_moderna()
        self.setWindowTitle("Panel Digital - ACTIVO")
        
        # Verificar estado después de mostrar la ventana
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, self.verificar_estado_panel)
        
        # Crear ventana de reactivación
        self.crear_ventana_reactivacion()

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
        
        # Dibujar indicador de estado del panel solo en una esquina pequeña
        if not self.panel_activo:
            # Indicador pequeño en la esquina superior derecha
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.setBrush(QBrush(QColor(255, 0, 0, 150)))
            painter.drawRect(self.width() - 50, 10, 40, 20)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawText(QRect(self.width() - 50, 10, 40, 20), Qt.AlignCenter, "INACTIVO")

    def mousePressEvent(self, event):
        # Si el panel está inactivo, solo permitir activarlo en el indicador pequeño
        if not self.panel_activo:
            # Verificar si el clic está en el indicador pequeño (esquina superior derecha)
            indicador_rect = QRect(self.width() - 50, 10, 40, 20)
            if indicador_rect.contains(event.pos()):
                self.alternar_modo()
                return
            else:
                # NO hacer nada, dejar que los eventos pasen a las aplicaciones del sistema
                event.ignore()
                return

        if event.button() == Qt.LeftButton:
            if self.modo == "lapiz":
                self.dibujando = True
                self.ultimo_punto = event.pos()
            elif self.modo == "punto":
                # Dibujar un punto
                self.trazo.append((event.pos(), event.pos()))
                self.update()
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
        # Si el panel está inactivo, ignorar eventos de mouse
        if not self.panel_activo:
            return
        
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
        # Si el panel está inactivo, ignorar eventos de mouse
        if not self.panel_activo:
            return
            
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
        # Si el panel está inactivo, ignorar eventos de mouse
        if not self.panel_activo:
            return
            
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
        elif event.key() == Qt.Key_Space:
            # Espacio para alternar modo
            self.alternar_modo()
        elif event.key() == Qt.Key_F12:
            # F12 para reactivar cuando esté oculto
            if not self.panel_activo:
                self.alternar_modo()

    def crear_interfaz_moderna(self):
        # Panel con diseño básico pero bonito
        barra = QToolBar("herramientas")
        barra.setMovable(False)
        barra.setOrientation(Qt.Vertical)
        barra.setIconSize(QSize(20, 20))  # Iconos más pequeños
        barra.setFixedWidth(150)  # Forzar ancho fijo más pequeño
        barra.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # Forzar texto al lado del icono
        barra.setFloatable(False)  # Evitar que flote
        barra.setAllowedAreas(Qt.LeftToolBarArea)  # Solo permitir área izquierda
        
        # Forzar que no haya scroll y muestre todos los elementos
        barra.setContextMenuPolicy(Qt.NoContextMenu)  # Deshabilitar menú contextual
        # Cambiar el CSS completo:
        # CSS moderno para el panel
        css_style = """
            QToolBar {
                background-color: #1a2332;
                border: 2px solid #3c5078;
                border-radius: 8px;
                padding: 3px;
                spacing: 1px;
                margin: 3px;
            }
            QToolButton {
                background-color: #283548;
                border: 2px solid #506e9e;
                border-radius: 4px;
                color: white;
                padding: 4px;
                font-size: 9px;
                font-weight: bold;
                min-height: 20px;
                margin: 1px;
                text-align: center;
                width: 140px;
                max-width: 140px;
            }
            QToolButton:hover {
                background-color: #3c4a5c;
                border: 2px solid #6482aa;
            }
            QToolButton:pressed {
                background-color: #4a5a6c;
                border: 2px solid #7a96b6;
            }
            QSpinBox {
                background-color: #283548;
                border: 2px solid #506e9e;
                border-radius: 4px;
                color: white;
                padding: 3px;
                font-size: 9px;
                min-height: 18px;
                width: 140px;
                max-width: 140px;
            }
            QToolBar::separator {
                background-color: #506e9e;
                width: 1px;
                margin: 3px 0px;
            }
            QToolButton:disabled {
                color: #00ccff;
                font-weight: bold;
                font-size: 12px;
                background-color: transparent;
                border: none;
            }
            
            /* Estilo especial para el botón de alternar */
            QToolButton[text*=" Alternar"] {
                background-color: #ff6b35;
                border: 3px solid #e55a2b;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 11px;
                min-height: 25px;
                margin: 3px;
            }
            QToolButton[text*=" Alternar"]:hover {
                background-color: #ff8c5a;
                border: 3px solid #ff6b35;
            }
            QToolButton[text*=" Alternar"]:pressed {
                background-color: #e55a2b;
                border: 3px solid #cc4a1a;
            }
            
            /* Estilo especial para el botón de cerrar */
            QToolButton[text*="❌"] {
                background-color: #dc3545;
                border: 3px solid #c82333;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 11px;
                min-height: 25px;
                margin: 3px;
            }
            QToolButton[text*="❌"]:hover {
                background-color: #e74c3c;
                border: 3px solid #dc3545;
            }
            QToolButton[text*="❌"]:pressed {
                background-color: #c82333;
                border: 3px solid #a71e2a;
            }
        """
        barra.setStyleSheet(css_style)
        self.addToolBar(Qt.LeftToolBarArea, barra)
        
        # BOTÓN DE ALTERNAR (PRIMERO Y DESTACADO)
        boton_alternar = QAction(" Alternar", self)
        boton_alternar.triggered.connect(self.alternar_modo)
        barra.addAction(boton_alternar)
        
        barra.addSeparator()
        
        # SECCIÓN: HERRAMIENTAS DE DIBUJO
        titulo_herramientas = QAction("✏️ HERRAMIENTAS", self)
        titulo_herramientas.setEnabled(False)
        barra.addAction(titulo_herramientas)
        
        boton_lapiz = QAction("✏️ Lápiz", self)
        boton_lapiz.triggered.connect(lambda: self.cambiar_modo("lapiz"))
        barra.addAction(boton_lapiz)
        
        boton_borrador = QAction(" Borrador", self)
        boton_borrador.triggered.connect(lambda: self.cambiar_modo("borrador"))
        barra.addAction(boton_borrador)
        
        barra.addSeparator()
        
        # SECCIÓN: TEXTO
        titulo_texto = QAction("📝 TEXTO", self)
        titulo_texto.setEnabled(False)
        barra.addAction(titulo_texto)
        
        boton_texto = QAction("📝 Texto", self)
        boton_texto.triggered.connect(lambda: self.cambiar_modo("texto"))
        barra.addAction(boton_texto)
        
        barra.addSeparator()
        
        # SECCIÓN: FIGURAS
        titulo_figuras = QAction("⬜ FIGURAS", self)
        titulo_figuras.setEnabled(False)
        barra.addAction(titulo_figuras)
        
        boton_linea = QAction("📏 Línea", self)
        boton_linea.triggered.connect(lambda: self.cambiar_figura("linea"))
        barra.addAction(boton_linea)
        
        boton_cuadrado = QAction("⬜ Cuadrado", self)
        boton_cuadrado.triggered.connect(lambda: self.cambiar_figura("cuadrado"))
        barra.addAction(boton_cuadrado)
        
        boton_circulo = QAction("⭕ Círculo", self)
        boton_circulo.triggered.connect(lambda: self.cambiar_figura("circulo"))
        barra.addAction(boton_circulo)
        
        barra.addSeparator()
        
        # SECCIÓN: CONTROLES
        titulo_controles = QAction(" CONTROLES", self)
        titulo_controles.setEnabled(False)
        barra.addAction(titulo_controles)
        
        boton_mover = QAction("✋ Mover", self)
        boton_mover.triggered.connect(lambda: self.cambiar_modo("mover"))
        barra.addAction(boton_mover)
        
        boton_redimensionar = QAction("⤡ Redimensionar", self)
        boton_redimensionar.triggered.connect(lambda: self.cambiar_modo("redimensionar"))
        barra.addAction(boton_redimensionar)
        
        barra.addSeparator()
        
        # SECCIÓN: COLORES
        titulo_colores = QAction("🎨 COLORES", self)
        titulo_colores.setEnabled(False)
        barra.addAction(titulo_colores)
        
        boton_rojo = QAction("🔴 Rojo", self)
        boton_rojo.triggered.connect(lambda: self.cambiar_color(QColor(255, 0, 0)))
        barra.addAction(boton_rojo)
        
        boton_amarillo = QAction(" Amarillo", self)
        boton_amarillo.triggered.connect(lambda: self.cambiar_color(QColor(255, 255, 0)))
        barra.addAction(boton_amarillo)
        
        boton_azul = QAction("🔵 Azul", self)
        boton_azul.triggered.connect(lambda: self.cambiar_color(QColor(0, 0, 255)))
        barra.addAction(boton_azul)
        
        barra.addSeparator()
        
        # SECCIÓN: EDICIÓN
        titulo_edicion = QAction("⚙️ EDICIÓN", self)
        titulo_edicion.setEnabled(False)
        barra.addAction(titulo_edicion)
        
        spinbox_grosor = QSpinBox()
        spinbox_grosor.setRange(1, 20)
        spinbox_grosor.setValue(3)
        spinbox_grosor.valueChanged.connect(self.cambiar_grosor)
        barra.addWidget(spinbox_grosor)
        
        boton_deshacer = QAction("↶ Deshacer", self)
        boton_deshacer.triggered.connect(self.deshacer)
        barra.addAction(boton_deshacer)
        
        boton_borrar = QAction(" Borrar Todo", self)
        boton_borrar.triggered.connect(self.borrar_todo)
        barra.addAction(boton_borrar)
        
        barra.addSeparator()
        
        # BOTÓN DE CERRAR (AL FINAL)
        boton_cerrar = QAction("❌ Cerrar", self)
        boton_cerrar.triggered.connect(self.cerrar_aplicacion)
        barra.addAction(boton_cerrar)
        
        # Forzar la aplicación de estilos
        barra.setStyle(barra.style())
        barra.update()
        
        # Verificar que los estilos se aplicaron
        print(f"Estilos aplicados: {barra.styleSheet()[:100]}...")
        print(f"Barra visible: {barra.isVisible()}")
        print(f"Barra ancho: {barra.width()}")
        
        # Forzar actualización después de un breve delay
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: barra.update())
        
        # Verificar si los estilos se aplicaron correctamente
        if not barra.styleSheet():
            print("⚠️ Los estilos no se aplicaron, usando estilos básicos...")
            self.aplicar_estilos_basicos(barra)
        
        # Asegurar que la barra sea visible
        barra.setVisible(True)
        barra.show()
        
        # Forzar layout vertical después de agregar todos los elementos
        barra.updateGeometry()
        
        # Verificar que todos los elementos estén visibles
        print(f"Total de acciones en la barra: {len(barra.actions())}")
        print(f"Total de widgets en la barra: {len(barra.findChildren(QSpinBox))}")
        
        # Forzar que todos los elementos sean visibles
        for action in barra.actions():
            if action.isVisible() == False:
                action.setVisible(True)
        
        print("Panel con diseño creado")

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
        if not self.panel_activo:
            return  # No cambiar modo si el panel está inactivo
        self.modo = modo
        if modo == "texto":
            self.setCursor(Qt.IBeamCursor)
        elif modo == "mover":
            self.setCursor(Qt.OpenHandCursor)
        elif modo == "figura":
            self.setCursor(Qt.CrossCursor)
        elif modo == "redimensionar":
            self.setCursor(Qt.SizeAllCursor)
        elif modo == "borrador":
            self.setCursor(Qt.CrossCursor)
        elif modo == "seleccionar":
            self.setCursor(Qt.ArrowCursor)
        elif modo == "punto":
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

    def alternar_modo(self):
        self.panel_activo = not self.panel_activo
        if self.panel_activo:
            # Activar panel - Mostrar completamente
            self.show()
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setCursor(Qt.ArrowCursor)
            self.setWindowTitle("Panel Digital - ACTIVO")
            # Mostrar barra de herramientas
            for barra in self.findChildren(QToolBar):
                barra.setVisible(True)
            # Ocultar ventana de reactivación
            if hasattr(self, 'ventana_reactivacion'):
                self.ventana_reactivacion.hide()
            print("🟢 Panel ACTIVADO - Completamente visible")
        else:
            # Desactivar panel - Ocultar completamente
            self.hide()
            self.setWindowTitle("Panel Digital - OCULTO")
            # Mostrar ventana de reactivación
            if hasattr(self, 'ventana_reactivacion'):
                self.ventana_reactivacion.show()
            print("🔴 Panel OCULTO - Completamente invisible")
        
        # Forzar actualización de la ventana
        self.update()
        self.repaint()

    def crear_icono_color(self, color, texto=""):
        # Crear un icono de color sólido más grande
        pixmap = QPixmap(48, 48)  # Tamaño más grande
        pixmap.fill(color)
        return QIcon(pixmap)

    def crear_icono_texto(self, texto, color_fondo=QColor(255, 255, 255), color_texto=QColor(0, 0, 0)):
        # Crear icono con texto más grande
        pixmap = QPixmap(48, 48)  # Tamaño más grande
        pixmap.fill(color_fondo)
        painter = QPainter(pixmap)
        painter.setPen(QPen(color_texto))
        painter.setFont(QFont("Arial", 16, QFont.Bold))  # Fuente más grande y negrita
        painter.drawText(pixmap.rect(), Qt.AlignCenter, texto)
        painter.end()
        return QIcon(pixmap)

    def crear_icono_mejorado(self, simbolo, color_fondo, color_texto, color_borde=None):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparente
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo redondeado
        painter.setBrush(QBrush(color_fondo))
        if color_borde:
            painter.setPen(QPen(color_borde, 2))
        else:
            painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
        
        # Texto
        painter.setPen(QPen(color_texto))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, simbolo)
        painter.end()
        
        return QIcon(pixmap)

    def deshacer(self):
        if self.trazo:
            self.trazo.pop()
        elif self.textos:
            self.textos.pop()
        elif self.figuras:
            self.figuras.pop()
        self.update()

    def aplicar_estilos_basicos(self, barra):
        """Método alternativo para aplicar estilos básicos si el CSS complejo falla"""
        try:
            # Estilos básicos como respaldo
            css_basico = """
                QToolBar {
                    background-color: #2b3e50;
                    border: 1px solid #34495e;
                }
                QToolButton {
                    background-color: #34495e;
                    border: 1px solid #2c3e50;
                    color: white;
                    padding: 5px;
                    font-weight: bold;
                }
                QSpinBox {
                    background-color: #34495e;
                    color: white;
                    border: 1px solid #2c3e50;
                }
            """
            barra.setStyleSheet(css_basico)
            print("Estilos básicos aplicados como respaldo")
        except Exception as e:
            print(f"Error aplicando estilos básicos: {e}")

    def verificar_estado_panel(self):
        """Verificar el estado del panel después de que se muestre la ventana"""
        try:
            # Buscar la barra de herramientas
            for barra in self.findChildren(QToolBar):
                print(f"✅ Barra encontrada: {barra.objectName()}")
                print(f"   Visible: {barra.isVisible()}")
                print(f"   Ancho: {barra.width()}")
                print(f"   Alto: {barra.height()}")
                print(f"   Estilos: {barra.styleSheet()[:50]}...")
                
                # Forzar actualización si no es visible
                if not barra.isVisible():
                    barra.setVisible(True)
                    barra.show()
                    barra.update()
                    print("   🔄 Barra forzada a visible")
        except Exception as e:
            print(f"❌ Error verificando panel: {e}")

    def crear_ventana_reactivacion(self):
        """Crear una ventana pequeña para reactivar el panel cuando esté oculto"""
        from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
        from PyQt5.QtCore import QTimer
        
        self.ventana_reactivacion = QWidget()
        self.ventana_reactivacion.setWindowTitle("Reactivar Panel")
        self.ventana_reactivacion.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.ventana_reactivacion.setAttribute(Qt.WA_TranslucentBackground)
        self.ventana_reactivacion.setGeometry(10, 10, 100, 30)
        
        # Crear layout
        layout = QVBoxLayout()
        self.ventana_reactivacion.setLayout(layout)
        
        # Crear etiqueta
        etiqueta = QLabel("🔄 Panel")
        etiqueta.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 0, 0, 200);
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        layout.addWidget(etiqueta)
        
        # Conectar clic para reactivar
        etiqueta.mousePressEvent = lambda event: self.reactivar_panel()
        
        # Mostrar la ventana de reactivación
        self.ventana_reactivacion.show()
        
        print("✅ Ventana de reactivación creada")
        
    def reactivar_panel(self):
        """Reactivar el panel cuando está oculto"""
        if not self.panel_activo:
            self.alternar_modo()
            print("🔄 Panel reactivado desde ventana de reactivación")

    def cerrar_aplicacion(self):
        """Cerrar completamente la aplicación"""
        reply = QMessageBox.question(self, 'Confirmar Cierre', 
                                   '¿Estás seguro de que quieres cerrar el Panel Digital?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            print("🔄 Cerrando Panel Digital...")
            # Cerrar ventana de reactivación si existe
            if hasattr(self, 'ventana_reactivacion'):
                self.ventana_reactivacion.close()
            # Cerrar la aplicación
            QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaDibujo()
    ventana.show()
    sys.exit(app.exec_())