from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

# Barra que hereda de QWidget
class _Bar(QtWidgets.QWidget):
    #clickedValue es una señal que emite un número entero
    clickedValue = QtCore.Signal(int)
    # El constructor debe recibir los "steps"
    def __init__(self, steps):
        super().__init__()
        # La política MininumExpanding permite usar todo el espacio disponible a partir del tamaño mínimo establecido en sizeHint()
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding,
        )
        # La función isinstance recibe como argumentos un objeto y una clase y devuelve True si el objeto es una instancia de dicha clase o de una subclase de ella.
        
        # Si steps es una lista de colores
        if isinstance(steps, list):
            # El número de steps es la longitud de la lista
            self.n_steps = len(steps)
            # self.steps es la lista de colores
            self.steps = steps

        # Si steps es un entero
        elif isinstance(steps, int):
            # El número de steps es ese entero
            self.n_steps = steps
            # self.steps es una lista de colores rojos del tamaño de steps
            self.steps = ["red"] * steps
        # Si no es una lista o un entero, lanzamos un error
        else:
            # raise fuerza una excepción
            raise TypeError("steps must be a list or int")

        # Porcentaje de altura de las barras dentro del rectángulo individual de cada una
        self._bar_solid_percent = 0.8
        # El color de fondo de la Bar es negro
        self._background_color = QtGui.QColor("black")
        # Los píxeles de padding alrededor del borde son 4
        self._padding = 4

    # Ante un evento de dibujo
    def paintEvent(self, e):
        # Creamos el objeto painter
        painter = QtGui.QPainter(self)

        # Creamos la brocha
        brush = QtGui.QBrush()
        # Establecemos el color de la brocha (el color de fondo, negro)
        brush.setColor(self._background_color)
        # Establecemos el estilo de patrón de relleno: sólido
        brush.setStyle(Qt.SolidPattern)
        # Dibujamos un rectángulo (fondo de la Bar)
        rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
        # Rellenamos el rectángulo
        painter.fillRect(rect, brush)

        # Obtenemos estado actual del padre (PowerBar)
        parent = self.parent()
        # Obtenemos el mínimo, el máximo y el valor del padre
        # Al no existir esas propiedades en Bar, las obtiene del QDial (método (__getattr__)), que las hereda de QAbstractSlider
        vmin, vmax = parent.minimum(), parent.maximum()
        value = parent.value()

        # Definimos la altura y la anchura del canvas en el que vamos a dibujar las barras
        d_height = painter.device().height() - (self._padding * 2)
        d_width = painter.device().width() - (self._padding * 2)

        # Dibujamos las barras

        # Para la altura del rectángulo para cada barra, dividimos la altura del canvas entre el número de barras
        step_size = d_height / self.n_steps
        # Para determinar la altura del relleno de la barra, multiplicamos la altura del rectángulo para cada una por el porcentaje previamente definido
        bar_height = step_size * self._bar_solid_percent

        # Calculamos el número de barras a dibujar en función del valor actual
        pc = (value - vmin) / (vmax - vmin)
        n_steps_to_draw = int(pc * self.n_steps)

        # Por cada barra a dibujar
        for n in range(n_steps_to_draw):
            # Establecemos el color según la posición de la lista self.steps
            brush.setColor(QtGui.QColor(self.steps[n]))
            # Calculamos su posición en el canvas
            ypos = (1 + n) * step_size
            # Dibujamos el rectángulo de la barra
            rect = QtCore.QRect(
                self._padding,
                self._padding + d_height - int(ypos),
                d_width,
                int(bar_height),
            )
            # Y lo rellenamos
            painter.fillRect(rect, brush)

        painter.end()
    
    # El método sizeHint siempre devuelve el tamaño recomendado del widget (por defecto)
    def sizeHint(self):
        return QtCore.QSize(40, 120)

    # Cada vez que se cambia el valor del QDial, se llama a este método que ejecuta un update()
    # https://doc.qt.io/qt-5/qwidget.html#update
    # update() programa un paintEvent, que provocará el redibujado de la Bar
    def _trigger_refresh(self):
        self.update()

    # Cálculo del valor de la barra en función de donde se haga clic
    def _calculate_clicked_value(self, e):
        parent = self.parent()
        vmin, vmax = parent.minimum(), parent.maximum()
        d_height = self.size().height() + (self._padding * 2)
        step_size = d_height / self.n_steps
        click_y = e.y() - self._padding - step_size / 2

        pc = (d_height - click_y) / d_height
        value = int(vmin + pc * (vmax - vmin))
        # Emitimos una señal con el vambio de valor. Esta es una señal propia de este componente
        self.clickedValue.emit(value)

    # Un evento de movimiento de arrastre del ratón provoca el cálculo del clic
    def mouseMoveEvent(self, e):
        self._calculate_clicked_value(e)

    # Un evento de presionado en el ratón provoca el cálculo del clic
    def mousePressEvent(self, e):
        self._calculate_clicked_value(e)

# Custom widget que combina una Bar y un QDial
class PowerBar(QtWidgets.QWidget):

    def __init__(self, steps=5, parent=None):
        super().__init__(parent)

        # Creamos un Layout vertical con un objeto Bar y un objeto QDial
        layout = QtWidgets.QVBoxLayout()
        self._bar = _Bar(steps)
        layout.addWidget(self._bar)
        self._dial = QtWidgets.QDial()
        # Establecemos algunas propiedades del QDial
        self._dial.setNotchesVisible(True)
        self._dial.setWrapping(False)
        # Conectamos la señal del cambio de valor en el QDial con _trigger_refresh de la Bar para actualizarla
        self._dial.valueChanged.connect(self._bar._trigger_refresh)

        # De la misma forma, conectamos la señal del cambio de valor en la barra con el setValue del QDial para actualizarlo
        self._bar.clickedValue.connect(self._dial.setValue)

        layout.addWidget(self._dial)
        self.setLayout(layout)
    # Este método se ejecuta cuando se intenta obtener alguna propiedad de PowerBar
    def __getattr__(self, name):
        # Si se trata de una propiedad de PowerBar, la devuelve
        if name in self.__dict__:
            return self[name]
        # Si no, intenta obtener la propiedad del objeto QDial
        try:
            return getattr(self._dial, name)
        except AttributeError:
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(
                    self.__class__.__name__, name
                )
            )
    # Método que establece un color para toda la PowerBar
    def setColor(self, color):
        self._bar.steps = [color] * self._bar.n_steps
        self._bar.update()
    # Método que establece los colores de cada barra
    def setColors(self, colors):
        self._bar.n_steps = len(colors)
        self._bar.steps = colors
        self._bar.update()
    # Método que establece un padding diferente para las barras
    def setBarPadding(self, i):
        self._bar._padding = int(i)
        self._bar.update()
    # Método que cambia el porcentaje del relleno de la barra
    def setBarSolidPercent(self, f):
        self._bar._bar_solid_percent = float(f)
        self._bar.update()
    # Método que cambia el color de fondo de la barra
    def setBackgroundColor(self, color):
        self._bar._background_color = QtGui.QColor(color)
        self._bar.update()
