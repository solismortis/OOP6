# Attempts to merge OOP4 and 6 with 6 as the base
# TODO: Import everything from lab 4 that u deleted
# TODO: Save color?
"""Qt hates floats in coords"""
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


RADIUS = 70
MOVE_DIST = 40
SCALE_INCREMENT = 2
shape_container = []
CENTER_COLOR = 'white'


class Shape:
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.color = "#FF0000"  # Red
        self.selected = False

    def got_selected(self, x, y):
        pass

    def move_possible(self, dx, dy, widget_width, widget_height):
        # Left
        if dx < 0 and self.center_x + dx < 0:
            return False
        # Right
        elif self.center_x + dx > widget_width:
            return False
        # Top
        if dy < 0 and self.center_y + dy < 0:
            return False
        # Bottom
        elif self.center_y + dy > widget_height:
            return False
        return True

    def move(self, dx, dy):
        self.center_x += dx
        self.center_y += dy

    def draw_center(self, painter):
        painter.drawLine(self.center_x - 10,
                         self.center_y - 10,
                         self.center_x + 10,
                         self.center_y + 10)
        painter.drawLine(self.center_x - 10,
                         self.center_y + 10,
                         self.center_x + 10,
                         self.center_y - 10)

    def paint(self, painter):
        pass

    def save(self, file):
        pass

    def load(self, file):
        pass

    def resize(self, ds, widget_width, widget_height):
        pass

class Group(Shape):
    def __init__(self, center_x=0, center_y=0):
        super().__init__(center_x, center_y)
        self.objs = []

    def got_selected(self, x, y):
        for obj in self.objs:
            # If at least 1 is selected, all are
            if obj.got_selected(x, y):
                self.selected = True
                return True
        return False

    def add(self, obj):
        self.objs.append(obj)
        # Calc new center from other centers
        total_x = 0
        total_y = 0
        for obj in self.objs:
            total_x += obj.center_x
            total_y += obj.center_y
        self.center_x = int(total_x / len(self.objs))
        self.center_y = int(total_y / len(self.objs))

    def move_possible(self, dx, dy, widget_width, widget_height):
        for obj in self.objs:
            if not obj.move_possible(dx, dy, widget_width, widget_height):
                return False
        return True

    def move(self, dx, dy):
        self.center_x += dx
        self.center_y += dy
        for obj in self.objs:
            obj.move(dx, dy)

    def paint(self, painter):
        for obj in self.objs:
            obj.paint(painter)

    def save(self, file):
        file.write(f'G\n'
                   f'{self.center_x}\n'
                   f'{self.center_y}\n'
                   f'{len(self.objs)}\n')  # Number of objs
        for obj in self.objs:
            obj.save(file)

    def load(self, file):
        self.center_x = int(file.readline())
        self.center_y = int(file.readline())
        for _ in range(int(file.readline())):  # Number of objs
            obj = window.factory.create_default_shape(file.readline())
            obj.load(file)
            self.objs.append(obj)


class Ellipse(Shape):
    def __init__(self,
                 center_x=0,
                 center_y=0,
                 r1=RADIUS+20,
                 r2=RADIUS-20):
        super().__init__(center_x, center_y)
        self.r1 = r1
        self.r2 = r2

    def got_selected(self, x, y):
        if ((x-self.center_x)/self.r1)**2 \
            + ((y-self.center_y)/self.r2)**2 <= 1:
            self.selected = True
            return True
        return False

    def move_possible(self, dx, dy, widget_width, widget_height):
        new_center_x = self.center_x + dx
        new_center_y = self.center_y + dy
        # Check left and top
        if new_center_x - self.r1 < 0 \
        or new_center_y - self.r2 < 0:
            return False
        # Check right and bottom
        if new_center_x + self.r1 > widget_width \
        or new_center_y + self.r2 > widget_height:
            return False
        return True

    def move(self, dx, dy):
        self.center_x += dx
        self.center_y += dy

    def paint(self, painter):
        painter.drawEllipse(QPoint(self.center_x, self.center_y), self.r1, self.r2)

    def save(self, file):
        file.write(f'E\n'
                   f'{self.center_x}\n'
                   f'{self.center_y}\n'
                   f'{self.r1}\n'
                   f'{self.r2}\n')

    def load(self, file):
        self.center_x = int(file.readline())
        self.center_y = int(file.readline())
        self.r1 = int(file.readline())
        self.r2 = int(file.readline())

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
    def __init__(self, center_x, center_y, r1=RADIUS):
        super().__init__(center_x, center_y, r1, r1)


class Point(Shape):
    def save(self, file):
        file.write(f'P\n'
                   f'{self.center_x}\n'
                   f'{self.center_y}\n')

    def load(self, file):
        self.center_x = int(file.readline())
        self.center_y = int(file.readline())


class ConnectedPointGroup(Shape):
    def __init__(self,
                 center_x=0,
                 center_y=0,
                 points: list[Point]=None):
        super().__init__(center_x, center_y)
        if not points:
            points = []
        self.points = points

    def move_possible(self, dx, dy, widget_width, widget_height):
        for point in self.points:
            if not point.move_possible(dx, dy, widget_width, widget_height):
                return False
        return True

    def move(self, dx, dy):
        self.center_x += dx
        self.center_y += dy
        for point in self.points:
            point.move(dx, dy)
        return True

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

    def save(self, file):
        file.write(f'CPG\n'
                   f'{self.center_x}\n'
                   f'{self.center_y}\n'
                   f'{len(self.points)}\n')
        for point in self.points:
            point.save(file)

    def load(self, file):
        self.center_x = int(file.readline())
        self.center_y = int(file.readline())
        for _ in range(int(file.readline())):  # Number of points
            file.readline()  # Discard 'P'
            p = Point(int(file.readline()), int(file.readline()))
            self.points.append(p)

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

class Rectangle(ConnectedPointGroup):
    def set_width_and_height(self):
        self.width = self.points[2].center_x - self.points[0].center_x
        self.height = self.points[1].center_y - self.points[0].center_y

    def __init__(self,
                 center_x: int=0,
                 center_y: int=0,
                 points: list[Point]=None):
        # Make sure there are only 4 points
        if points:
            if len(points) != 4:
                raise ValueError('Rectangle can only have 4 points')
            else:
                super().__init__(center_x, center_y, points)
        else:  # Default points
            super().__init__(center_x, center_y,
                             [Point(center_x-100, center_y-50),
                              Point(center_x-100, center_y+50),
                              Point(center_x+100, center_y+50),
                              Point(center_x+100, center_y-50)])
        self.width = None
        self.height = None
        self.set_width_and_height()

    def got_selected(self, x, y):
        if self.center_x - self.width/2 <= x <= self.center_x + self.width/2 \
            and self.center_y - self.height/2 <= y <= self.center_y + self.height/2:
            self.selected = True
            return True
        return False

    def resize(self, ds, widget_width, widget_height):
        super().resize(ds, widget_width, widget_height)
        self.set_width_and_height()


class Square(Rectangle):
    def __init__(self,
                 center_x=0,
                 center_y=0,
                 points=None):
        if not points:  # Default points
            super().__init__(center_x, center_y,
                             [Point(center_x-50, center_y-50),
                              Point(center_x-50, center_y+50),
                              Point(center_x+50, center_y+50),
                              Point(center_x+50, center_y-50)])


class ShapeFactory:
    def __init__(self):
        """По коду возвращает дефолтный объект,
        у которого потом вызывается load()"""
        self.shape_dict = {
            'G\n': Group,
            'E\n': Ellipse,
            'C\n': Circle,
            'P\n': Point,
            'CPG\n': ConnectedPointGroup,
            'R\n': Rectangle,
            'SQ\n': Square
        }

    def create_default_shape(self, code):
        return self.shape_dict[code](0, 0)


class PaintWidget(QPushButton):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.setMinimumSize(500, 500)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.mode = 'Ellipse'
        self.ctrl_multiple_select = False
        self.intersect_select = False

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

        # Draw center
        pen.setWidth(1)
        pen.setColor(QColor(CENTER_COLOR))
        painter.setPen(pen)
        for shape in shape_container:
            shape.draw_center(painter)

        painter.end()

    def mousePressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        if self.mode == 'Select':
            if not self.intersect_select:
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
                else:  # Nothing selected, deselect all
                    for shape in shape_container:
                        shape.selected = False
            else:  # intersect_select
                selected = False
                if not self.ctrl_multiple_select:
                    for shape in shape_container:
                        shape.selected = False
                for shape in shape_container:
                    if shape.got_selected(x, y):
                        selected = True
                if selected:
                    print("Selected!")
                else:  # Nothing selected, deselect all
                    for shape in shape_container:
                        shape.selected = False
        else:  # Modes other than "select"
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
                if shape.selected and shape.move_possible(
                0,
                -MOVE_DIST,
                self.size().width(),
                self.size().height()
                ):
                    shape.move(0, -MOVE_DIST)
            self.update()
        elif key == Qt.Key.Key_Down:
            for shape in shape_container:
                if shape.selected and shape.move_possible(
                0,
                MOVE_DIST,
                self.size().width(),
                self.size().height()
                ):
                    shape.move(0, MOVE_DIST)
            self.update()
        elif key == Qt.Key.Key_Left:
            for shape in shape_container:
                if shape.selected and shape.move_possible(
                -MOVE_DIST,
                0,
                self.size().width(),
                self.size().height()
                ):
                    shape.move(-MOVE_DIST, 0)
            self.update()
        elif key == Qt.Key.Key_Right:
            for shape in shape_container:
                if shape.selected and shape.move_possible(
                MOVE_DIST,
                0,
                self.size().width(),
                self.size().height()
                ):
                    shape.move(MOVE_DIST, 0)
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
        elif key == Qt.Key.Key_Z:
            self.intersect_select = not self.intersect_select
            self.parent.intersect_select_label.setText(f"Intersect select mode: {self.intersect_select}")

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
                                 "Press DELETE to delete selected\n"
                                 "Press Z to change intersect select mode")
        self.main_layout.addWidget(self.info_label)

        # Paint
        self.paint_button = PaintWidget(parent=self)
        self.main_layout.addWidget(self.paint_button)

        # Intersect label
        self.intersect_select_label = QLabel(f"Intersect select mode: {self.paint_button.intersect_select}")
        self.main_layout.addWidget(self.intersect_select_label)

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
        self.factory = ShapeFactory()

    def create_menu(self):
        # Don't know what should go here. Save, load and exit?
        menu = self.menuBar().addMenu("&Menu")
        menu.addAction("&Save", self.save)
        menu.addAction("&Load", self.load)
        menu.addAction("&Exit", self.close)

    def create_creation_toolbar(self):
        creation_toolbar = QToolBar()
        creation_toolbar.setStyleSheet("background-color: #537278; border: none;")
        creation_toolbar.addWidget(QLabel('Creation:'))
        creation_toolbar.addAction("Ellipse", partial(self.set_mode, 'Ellipse'))
        creation_toolbar.addAction("Circle", partial(self.set_mode, 'Circle'))
        creation_toolbar.addAction("Rectangle", partial(self.set_mode, 'Rectangle'))
        creation_toolbar.addAction("Square", partial(self.set_mode, 'Square'))
        self.addToolBar(creation_toolbar)

    def set_mode(self, mode):
        self.central_widget.paint_button.mode = mode
        self.central_widget.mode_label.setText(f'Current mode: {mode}')

    def create_editing_toolbar(self):
        editing_toolbar = QToolBar()
        editing_toolbar.setStyleSheet("background-color: #537278; border: none;")
        editing_toolbar.addWidget(QLabel('Editing:'))
        editing_toolbar.addAction('Select', partial(self.set_mode, 'Select'))
        editing_toolbar.addAction('Color', self.change_color)
        editing_toolbar.addAction('Group', self.group)
        editing_toolbar.addAction('Ungroup', self.ungroup)
        self.addToolBar(editing_toolbar)

    def change_color(self):
        color = QColorDialog.getColor()
        for shape in shape_container:
            if shape.selected:
                shape.color = color

    def group(self):
        group = Group()
        shapes_to_remove_from_container = []
        for shape in shape_container:
            if shape.selected:
                group.add(shape)
                shapes_to_remove_from_container.append(shape)
        for shape in shapes_to_remove_from_container:
            shape_container.remove(shape)
        shape_container.append(group)
        self.update()
        print('Group created')

    def ungroup(self):
        shapes_to_remove_from_container = []
        for shape in shape_container:
            if shape.selected and type(shape) is Group:
                for obj in shape.objs:
                    shape_container.append(obj)
                shapes_to_remove_from_container.append(shape)
        for shape in shapes_to_remove_from_container:
            shape_container.remove(shape)
        self.update()
        print('Ungroup')

    def save(self):
        filename = QFileDialog.getSaveFileName()[0]
        with open(filename, 'w') as file:
            # Save container size
            file.write(f'{len(shape_container)}\n')
            # Save all shapes
            for shape in shape_container:
                shape.save(file)

    def load(self):
        # Clear the global container
        global shape_container
        shape_container = []

        filename = QFileDialog.getOpenFileName()[0]
        with open(filename, 'r') as file:
            container_size = int(file.readline())
            print(container_size)
            for _ in range(container_size):
                obj = self.factory.create_default_shape(file.readline())
                obj.load(file)
                shape_container.append(obj)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit(app.exec())