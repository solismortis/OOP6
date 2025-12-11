import math
import sys
from functools import partial

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QBrush, QColor, QPainter, QPixmap, QMouseEvent, QPen
from PyQt6.QtWidgets import (QApplication,
                             QColorDialog,
                             QFileDialog,
                             QLabel,
                             QMainWindow,
                             QPushButton,
                             QSizePolicy,
                             QToolBar,
                             QVBoxLayout,
                             QWidget)


class Shape:
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.color = "#FF0000"  # Red
        self.selected = False

    def got_selected(self, x, y):
        if ((x - self.center_x) ** 2 + (y - self.center_y) ** 2) ** 0.5 <= RADIUS:
            self.selected = True
            return True
        return False

    def move(self, dx, dy, widget_width, widget_height):
        self.center_x += dx
        self.center_y += dy


class Group(Shape):
    """Отправляется в контейнер после принятия объектов"""

class Ellipse(Shape):
    def __init__(self, center_x, center_y, r1=None, r2=None):
        super().__init__(center_x, center_y)
        if r1:
            if r2:  # Ellipse
                self.r1 = r1
                self.r2 = r2
            else:  # Circle
                self.r1 = RADIUS
                self.r2 = RADIUS
        else:
            # Default ellipse
            self.r1 = RADIUS + 20
            self.r2 = RADIUS - 20

    def move(self, dx, dy, widget_width=None, widget_height=None):
        new_center_x = self.center_x + dx
        new_center_y = self.center_y + dy
        # Check left and top
        if new_center_x - self.r1 < 0 \
        or new_center_y - self.r2 < 0:
            return
        # Check right and bottom
        if new_center_x + self.r1 > widget_width \
        or new_center_y + self.r2 > widget_height:
            return

        self.center_x += dx
        self.center_y += dy

    def paint(self, painter):
        painter.drawEllipse(QPoint(self.center_x, self.center_y), self.r1, self.r2)

    def resize(self, ds, widget_width=None, widget_height=None):
        # ds too small for ellipse
        if ds > 0:
            ds += 30
        else:
            ds -= 30
        # Check borders
        if ds < 0:
            pass  # No need to check borders
        else:
            new_r1 = self.r1 + ds
            new_r2 = self.r2 + ds
            # Check left and top
            if self.center_x < new_r1 or self.center_y < new_r2:
                return
            # Check right and bottom
            if self.center_x + new_r1 > widget_width \
            or self.center_y + new_r2 > widget_height:
                return
        self.r1 += ds
        self.r2 += ds


class Circle(Ellipse):
    pass

class Point(Shape):
    pass


class ConnectedPointGroup(Shape):
    def __init__(self, center_x, center_y, points: list[Point]):
        super().__init__(center_x, center_y)
        self.points = points

    def move(self, dx, dy, widget_width, widget_height):
        # Check points for borders
        for point in self.points:
            # Left
            if dx < 0 and point.center_x + dx < 0:
                return
            # Right
            elif point.center_x + dx > widget_width:
                return
            # Top
            if dy < 0 and point.center_y + dy < 0:
                return
            # Bottom
            elif point.center_y + dy > widget_height:
                return

        self.center_x += dx
        self.center_y += dy
        for point in self.points:
            point.move(dx, dy, widget_width, widget_height)

    def paint(self, painter):
        point0 = self.points[0]
        for point1 in self.points[1:]:
            painter.drawLine(point0.center_x, point0.center_y, point1.center_x, point1.center_y)
            point0 = point1
        # Connect 0th and last points
        painter.drawLine(self.points[0].center_x,
                         self.points[0].center_y,
                         self.points[-1].center_x,
                         self.points[-1].center_y)

    def resize(self, ds, widget_width, widget_height):
        if ds < 0:
            ds = 1 / abs(ds)
        # Check borders
        for point in self.points:
            # Calculate vector from center to point
            vector_x = point.center_x - self.center_x
            vector_y = point.center_y - self.center_y

            # Scale the vector
            vector_x *= ds
            vector_y *= ds

            # Calculate new position
            new_center_x = int(self.center_x + vector_x)
            new_center_y = int(self.center_y + vector_y)
            if new_center_x < 0 or new_center_y < 0 \
            or new_center_x > widget_width or new_center_y > widget_height:
                return

        for point in self.points:
            # Calculate vector from center to point
            vector_x = point.center_x - self.center_x
            vector_y = point.center_y - self.center_y

            # Scale the vector
            vector_x *= ds
            vector_y *= ds

            # Calculate new position. We have to int() because PyQT doesn't want float for coords
            point.center_x = int(self.center_x + vector_x)
            point.center_y = int(self.center_y + vector_y)


class Section(ConnectedPointGroup):
    # Make sure there are 2 points
    def __init__(self, center_x: int, center_y: int, points: list[Point]=None):
        if points:
            if len(points) != 2:
                raise ValueError('Section can only have 2 points')
            else:
                super().__init__(center_x, center_y, points)
        else:  # Default points
            super().__init__(center_x, center_y,
                             [Point(center_x-50, center_y-50),
                              Point(center_x+50, center_y+50)])


class Rectangle(ConnectedPointGroup):
    # Make sure there are 4 points
    def __init__(self, center_x: int, center_y: int, points: list[Point]=None):
        if points:
            if len(points) != 4:
                raise ValueError('Section can only have 2 points')
            else:
                super().__init__(center_x, center_y, points)
        else:  # Default points
            super().__init__(center_x, center_y,
                             [Point(center_x-100, center_y-50),
                              Point(center_x-100, center_y+50),
                              Point(center_x+100, center_y+50),
                              Point(center_x+100, center_y-50)])



class Square(Rectangle):
    def __init__(self, center_x, center_y, points=None):
        if not points:  # Default points
            super().__init__(center_x, center_y,
                             [Point(center_x-50, center_y-50),
                              Point(center_x-50, center_y+50),
                              Point(center_x+50, center_y+50),
                              Point(center_x+50, center_y-50)])


class PaintWidget(QPushButton):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.setMinimumSize(500, 500)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.mode = 'Ellipse'
        self.ctrl_multiple_select = False

    def paintEvent(self, event):
        painter = QPainter()
        pen = QPen()
        pen.setWidth(5)
        painter.begin(self)

        for shape in shape_container:
            if shape.selected:
                pen.setColor(QColor('#0dff00'))  # Lime
            else:
                pen.setColor(QColor(shape.color))
            painter.setPen(pen)
            shape.paint(painter)
        painter.end()

    def mousePressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        if self.mode == 'Select':
            selected = False
            for shape in shape_container:
                if shape.got_selected(x, y):
                    selected = True
                    if not self.ctrl_multiple_select:
                        for other_shape in shape_container:
                            if other_shape != shape:
                                other_shape.selected = False
                    break
            if selected:
                print("Selected!")
            else:  # Deselect all
                for shape in shape_container:
                    shape.selected = False
        else:  # Create
            # Deselect all
            for shape in shape_container:
                shape.selected = False
            # Add shape
            if self.mode == 'Ellipse':
                shape_container.append(Ellipse(x, y))
                self.parent.parent.set_mode('Select')
            elif self.mode == 'Circle':
                shape_container.append(Circle(x, y, RADIUS))
                self.parent.parent.set_mode('Select')
            elif self.mode == 'Section':
                shape_container.append(Section(x, y))
                self.parent.parent.set_mode('Select')
            elif self.mode == 'Rectangle':
                shape_container.append(Rectangle(x, y))
                self.parent.parent.set_mode('Select')
            elif self.mode == 'Square':
                shape_container.append(Square(x, y))
                self.parent.parent.set_mode('Select')

    def resizeEvent(self, event):
        width = self.size().width()
        height = self.size().height()
        self.parent.resize_label.setText(f"Paint Widget size: {width} {height}")

    def keyPressEvent(self, event):
        # Get the key code of the pressed key
        key = event.key()

        # Convert the key code to a readable string
        key_text = Qt.Key(key).name.replace("Key_", "")

        print(f"Key pressed: {key_text}")

        # Move all selected
        if key == Qt.Key.Key_Up:
            for shape in shape_container:
                if shape.selected:
                    shape.move(0, -MOVE_DIST,
                               self.size().width(),
                               self.size().height())
            self.update()
        elif key == Qt.Key.Key_Down:
            for shape in shape_container:
                if shape.selected:
                    shape.move(0, MOVE_DIST,
                               self.size().width(),
                               self.size().height())
            self.update()
        elif key == Qt.Key.Key_Left:
            for shape in shape_container:
                if shape.selected:
                    shape.move(-MOVE_DIST, 0,
                               self.size().width(),
                               self.size().height())
            self.update()
        elif key == Qt.Key.Key_Right:
            for shape in shape_container:
                if shape.selected:
                    shape.move(MOVE_DIST, 0,
                               self.size().width(),
                               self.size().height())
            self.update()

        # Change size of all selected
        elif key == Qt.Key.Key_Minus:
            for shape in shape_container:
                if shape.selected:
                    shape.resize(-SCALE_INCREMENT,
                                 self.size().width(),
                                 self.size().height())
            self.update()
        elif key == Qt.Key.Key_Equal:
            for shape in shape_container:
                if shape.selected:
                    shape.resize(SCALE_INCREMENT,
                                 self.size().width(),
                                 self.size().height())
            self.update()

        # Delete all selected
        elif key == Qt.Key.Key_Delete:
            shapes_to_delete = []
            for shape in shape_container:
                if shape.selected:
                    shapes_to_delete.append(shape)
            for shape in shapes_to_delete:
                shape_container.remove(shape)
            self.update()
        elif key == Qt.Key.Key_Control:
            self.ctrl_multiple_select = True

    def keyReleaseEvent(self, event):
        # Get the key code of the pressed key
        key = event.key()
        if key == Qt.Key.Key_Control:
            self.ctrl_multiple_select = False


class CentralWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Info label
        self.info_label = QLabel("Hold CTRL to select multiple\n"
                                 "Use ARROWS to move objects\n"
                                 "Use - and = to resize objects\n"
                                 "Press DELETE to delete selected")
        self.main_layout.addWidget(self.info_label)

        # Paint
        self.paint_button = PaintWidget(parent=self)
        self.main_layout.addWidget(self.paint_button)

        # Mode label
        self.mode_label = QLabel(parent=self, text=f'Current mode: {self.paint_button.mode}')
        self.main_layout.addWidget(self.mode_label)

        # Resize event
        self.resize_label = QLabel("Paint Widget size: ")
        self.main_layout.addWidget(self.resize_label)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("OOP lab 6")
        self.central_widget = CentralWidget(parent=self)
        self.setCentralWidget(self.central_widget)
        self.create_menu()
        self.create_creation_toolbar()
        self.create_editing_toolbar()

    def create_menu(self):
        # Don't know what should go here. Save, load and exit?
        menu = self.menuBar().addMenu("&Menu")
        menu.addAction("&Load", self.load)
        menu.addAction("&Save", self.save)
        menu.addAction("&Exit", self.close)

    def create_creation_toolbar(self):
        creationg_toolbar = QToolBar()
        creationg_toolbar.setStyleSheet("background-color: #537278; border: none;")
        creationg_toolbar.addWidget(QLabel('Creation:'))
        creationg_toolbar.addAction("Ellipse", partial(self.set_mode, 'Ellipse'))
        creationg_toolbar.addAction("Circle", partial(self.set_mode, 'Circle'))
        creationg_toolbar.addAction("Section", partial(self.set_mode, 'Section'))
        creationg_toolbar.addAction("Rectangle", partial(self.set_mode, 'Rectangle'))
        creationg_toolbar.addAction("Square", partial(self.set_mode, 'Square'))
        self.addToolBar(creationg_toolbar)

    def set_mode(self, mode):
        self.central_widget.paint_button.mode = mode
        self.central_widget.mode_label.setText(f'Current mode: {mode}')

    def create_editing_toolbar(self):
        editing_toolbar = QToolBar()
        editing_toolbar.setStyleSheet("background-color: #537278; border: none;")
        editing_toolbar.addWidget(QLabel('Editing:'))
        editing_toolbar.addAction('Select', partial(self.set_mode, 'Select'))
        editing_toolbar.addAction('Color', self.change_color)
        self.addToolBar(editing_toolbar)

    def change_color(self):
        color = QColorDialog.getColor()
        for shape in shape_container:
            if shape.selected:
                shape.color = color

    def load(self):
        filename = QFileDialog.getOpenFileName()[0]
        print(filename)
        with open(filename, 'r') as file:
            content = file.read()
            print(content)


    def save(self):
        QFileDialog()

        with open('example.txt', 'w') as file:
            file.write("Hello, world!")


if __name__ == '__main__':
    RADIUS = 70
    MOVE_DIST = 40
    SCALE_INCREMENT = 2
    shape_container = []

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit(app.exec())