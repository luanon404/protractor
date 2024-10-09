import sys
import math
import random
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QGuiApplication, QCursor, QBrush
from PyQt6.QtWidgets import QApplication, QWidget, QLabel

def centerPoint(w: QWidget):
    return QPointF(w.x() + w.width() / 2, w.y() + w.height() / 2)

def drawShortenedLine(qPainter, p1, p2, shorten1 = 0.0, shorten2 = 0.0):
    diff = p2 - p1
    length = math.sqrt(QPointF.dotProduct(diff, diff))
    if length == 0 or shorten1 + shorten2 >= length:
        return
    p2 = p1 + diff * (1 - max(0, min(1, (shorten2 / length))))
    p1 = p1 + diff * max(0, min(1, (shorten1 / length)))
    qPainter.drawLine(p1, p2)

QPainter.drawShortenedLine = drawShortenedLine

class Handle(QWidget):
    moved = pyqtSignal(QPointF, name='moved')

    def __init__(self, parent, movable=True):
        super().__init__(parent)
        self.setGeometry(300, 300, 31, 31)
        self.setCursor(Qt.CursorShape.SizeAllCursor if movable else Qt.CursorShape.ArrowCursor)
        self.setStyleSheet("background-color: transparent;")
        self.movable = movable

    def r(self): return self.width() / 4

    def paintEvent(self, event):
        dark = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.SolidLine)
        light = QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.SolidLine)
        radius = self.width()/4
        qp = QPainter(self)
        r = self.r() + 1
        center = QPointF(self.width()/2, self.height()/2)
        for pen in [light, dark]:
            qp.setPen(pen)
            qp.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            qp.drawShortenedLine(center, QPointF(0, 0), r)
            qp.drawShortenedLine(center, QPointF(0, self.height()), r)
            qp.drawShortenedLine(center, QPointF(self.width(), self.height()), r)
            qp.drawShortenedLine(center, QPointF(self.width(), 0), r)
            qp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            qp.drawEllipse(QPointF(self.width()/2, self.height()/2), radius, radius)
        
        # Vẽ chấm đỏ ở trung tâm
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QBrush(Qt.GlobalColor.red))
        qp.drawEllipse(center, 3, 3)  # Tăng kích thước lên 3 pixel

    def mousePressEvent(self, event):
        if self.movable:
            self.offset = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        if self.movable:
            new_pos = self.mapToParent(event.position().toPoint()) - self.offset
            self.move(new_pos)
            self.moved.emit(QPointF(new_pos))

class Protractor(QWidget):
    angleInvert = False
    MAX_STICK_LENGTH = 300  # Maximum length of the sticks
    MIN_STICK_LENGTH = 50   # Minimum length of the sticks
    PARALLEL_STICK_DISTANCE = 10  # Distance between parallel sticks

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.handleC = Handle(self, movable=False)  # Center handle is not movable
        self.handle1 = Handle(self)
        self.handle2 = Handle(self, movable=False)  # handle2 is not movable
        
        center_x, center_y = 200, 200
        radius = min(150, self.MAX_STICK_LENGTH)
        self.handleC.move(center_x - self.handleC.width()//2, center_y - self.handleC.height()//2)
        self.handle1.move(center_x + radius - self.handle1.width()//2, center_y - self.handle1.height()//2)  # 0 degrees (horizontal)
        self.handle2.move(center_x - self.handle2.width()//2, center_y - radius - self.handle2.height()//2)  # 90 degrees (vertical)
        
        self.handle1.moved.connect(self.updateDisplay)
        
        self.label = QLabel(self)
        self.label.setStyleSheet("""
            font-size: 20px; 
            color: black; 
            background-color: rgba(255, 255, 255, 180);
            border: 1px solid black;
            border-radius: 5px;
            padding: 2px 5px;
        """)
        
        self.stick1_color = self.random_color()
        self.stick2_color = self.random_color()
        self.stick_left_color = self.random_color()
        self.stick_right_color = self.random_color()
        
        self.updateDisplay()
        
        self.moving = False
        self.offset = QPoint()
        
        # Enable mouse tracking to detect mouse movement
        self.setMouseTracking(True)

    def random_color(self):
        return QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def mouseDoubleClickEvent(self, event):
        self.angleInvert = not self.angleInvert
        self.stick1_color = self.random_color()
        self.stick2_color = self.random_color()
        self.stick_left_color = self.random_color()
        self.stick_right_color = self.random_color()
        self.updateDisplay()

    def updateDisplay(self):
        self.limitStickLength()
        self.placeLabel()
        
        v1 = centerPoint(self.handle1) - centerPoint(self.handleC)
        v2 = centerPoint(self.handle2) - centerPoint(self.handleC)
        
        angle_rad = math.atan2(-v2.y(), v2.x()) - math.atan2(-v1.y(), v1.x())
        
        angleDeg = math.degrees(angle_rad)
        if angleDeg < 0:
            angleDeg += 360
        
        if self.angleInvert:
            angleDeg = 360 - angleDeg
        
        self.label.setText(f"{angleDeg:.2f}°")
        self.label.adjustSize()
        self.update()

    def limitStickLength(self):
        center = centerPoint(self.handleC)
        for handle in [self.handle1, self.handle2]:
            vector = centerPoint(handle) - center
            length = math.sqrt(vector.x()**2 + vector.y()**2)
            if length > self.MAX_STICK_LENGTH:
                vector *= (self.MAX_STICK_LENGTH / length)
            elif length < self.MIN_STICK_LENGTH:
                vector *= (self.MIN_STICK_LENGTH / length)
            new_pos = center + vector
            handle.move(int(new_pos.x() - handle.width()//2), int(new_pos.y() - handle.height()//2))

    def placeLabel(self):
        labelPos = centerPoint(self.handleC).toPoint() + QPoint(self.handleC.width() + 10, -self.label.height()//2)
        self.label.move(labelPos)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        centerC = centerPoint(self.handleC)
        center1 = centerPoint(self.handle1)
        center2 = centerPoint(self.handle2)

        # Draw stick 1 (middle) with random color
        qp.setPen(QPen(self.stick1_color, 3, Qt.PenStyle.SolidLine))
        drawShortenedLine(qp, centerC, center1, self.handleC.r() + 1, self.handle1.r() + 1)
        
        # Draw stick 2 with different random color
        qp.setPen(QPen(self.stick2_color, 3, Qt.PenStyle.SolidLine))
        drawShortenedLine(qp, centerC, center2, self.handleC.r() + 1, self.handle2.r() + 1)

        # Calculate vector perpendicular to stick 1
        v1 = center1 - centerC
        perpendicular = QPointF(-v1.y(), v1.x())
        perpendicular_normalized = perpendicular / math.sqrt(perpendicular.x()**2 + perpendicular.y()**2)
        offset = perpendicular_normalized * self.PARALLEL_STICK_DISTANCE

        # Draw parallel stick on the left
        qp.setPen(QPen(self.stick_left_color, 2, Qt.PenStyle.SolidLine))
        drawShortenedLine(qp, centerC - offset, center1 - offset, self.handleC.r() + 1, self.handle1.r() + 1)

        # Draw parallel stick on the right
        qp.setPen(QPen(self.stick_right_color, 2, Qt.PenStyle.SolidLine))
        drawShortenedLine(qp, centerC + offset, center1 + offset, self.handleC.r() + 1, self.handle1.r() + 1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.is_on_stick(event.position()):
            self.moving = True
            self.offset = event.position().toPoint()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.moving:
            new_pos = self.mapToParent(event.position().toPoint() - self.offset)
            self.move(new_pos)
        else:
            if self.is_on_stick(event.position()):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.moving = False
        if self.is_on_stick(event.position()):
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def is_on_stick(self, pos):
        centerC = centerPoint(self.handleC)
        center1 = centerPoint(self.handle1)
        center2 = centerPoint(self.handle2)

        # Check if pos is on one of the sticks
        for start, end in [(centerC, center1), (centerC, center2)]:
            if self.point_on_line(pos, start, end):
                return True

        # Check parallel sticks
        v1 = center1 - centerC
        perpendicular = QPointF(-v1.y(), v1.x())
        perpendicular_normalized = perpendicular / math.sqrt(perpendicular.x()**2 + perpendicular.y()**2)
        offset = perpendicular_normalized * self.PARALLEL_STICK_DISTANCE

        if self.point_on_line(pos, centerC - offset, center1 - offset) or \
           self.point_on_line(pos, centerC + offset, center1 + offset):
            return True

        return False

    def point_on_line(self, point, line_start, line_end, tolerance=5):
        # Check if a point is on a line (with some tolerance)
        d1 = point - line_start
        d2 = line_end - line_start
        
        if d2.x() == 0 and d2.y() == 0:
            return False
        
        t = (d1.x() * d2.x() + d1.y() * d2.y()) / (d2.x()**2 + d2.y()**2)
        
        if 0 <= t <= 1:
            projection = line_start + t * d2
            distance = math.sqrt((point.x() - projection.x())**2 + (point.y() - projection.y())**2)
            return distance <= tolerance
        
        return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Protractor()
    widget.show()
    
    screen = QGuiApplication.primaryScreen().geometry()
    widget.setGeometry(screen)
    
    sys.exit(app.exec())