#!/usr/bin/env python

###
# Author: Stefan Holstein
# inspired by: https://github.com/Werkov/PyQt4/blob/master/examples/widgets/analogclock.py
# Thanks to https://stackoverflow.com/
#
# Sorry for mixing english & german notes
#
# ToDo: Fix Bug: Rundungsfehler Max Value / Grid
# ToDo: mehrere Zeiger ermöglichen. z.b. über ein ZeigerArray mit allen valiablen
#       Signal erzeugung (self.valueChange.emit()) pruefen wie es dann möglich ist.
#       Evtl MausTracking(Teil)-deaktivieren
#       Farben separat handeln
# todo: aktuell ist nur eine Zeigerrichtung klein nach gross im Uhrzeigersinn moeglich
# -> erweiterung Anzeige von gross nach klein um Uhrzeigersin
# todo: auf timer event verzichten um effizienz zu steigern
#       self.update() an allen stellen einfügen, an denen es notwendig ist.
#       It is possible to En-/disable timerevents. Use: self.use_timer_event = True/False
# todo: Bug Fix: Offset Berechnung bezogen auf den Winkel ist falsch
# Todo: print() in logging() ausgabe aendern
###

import os
import sys
import math
import time
try:
    from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication

    from PyQt5.QtGui import QPolygon, QPolygonF, QColor, QPen, QFont, QPainter, QFontMetrics, QConicalGradient, QRadialGradient

    from PyQt5.QtCore import Qt ,QTime, QTimer, QPoint, QPointF, QRect, QSize, QObject, pyqtSignal

except:
    print("Error while importing PyQt5")
    exit()

################################################################################################
# AnalogGaugeWidget CLASS
################################################################################################
class AnalogGaugeWidget(QWidget):
    """Fetches rows from a Bigtable.
    Args: 
        none
    
    """
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super(AnalogGaugeWidget, self).__init__(parent)

        ################################################################################################
        # DEFAULT TIMER VALUE
        ################################################################################################
        self.use_timer_event = False

        ################################################################################################
        # DEFAULT NEEDLE COLOR
        ################################################################################################
        self.setNeedleColor(0, 255, 255, 255)

        ################################################################################################
        # DEFAULT NEEDLE WHEN RELEASED
        ################################################################################################
        self.NeedleColorReleased = self.NeedleColor

        ################################################################################################
        # DEFAULT NEEDLE COLOR ON DRAG
        ################################################################################################
        # self.NeedleColorDrag = QColor(255, 0, 00, 255)
        self.setNeedleColorOnDrag(0, 0, 255, 255)

        ################################################################################################
        # DEFAULT SCALE TEXT COLOR
        ################################################################################################
        self.setScaleValueColor(0, 255, 255, 255)

        ################################################################################################
        # DEFAULT VALUE COLOR
        ################################################################################################
        self.setDisplayValueColor(0, 255, 255, 255)

        ################################################################################################
        # DEFAULT CENTER POINTER COLOR
        ################################################################################################
        # self.CenterPointColor = QColor(50, 50, 50, 255)
        self.set_CenterPointColor(0, 255, 255, 255)

        ################################################################################################
        # DEFAULT NEEDLE COUNT
        ################################################################################################
        self.value_needle_count = 1

        self.value_needle = QObject
        self.change_value_needle_style([QPolygon([
            QPoint(4, 4),
            QPoint(-4, 4),
            QPoint(-3, -120),
            QPoint(0, -126),
            QPoint(3, -120)
        ])])

        ################################################################################################
        # DEFAULT MINIMUM AND MAXIMUM VALUE
        ################################################################################################
        self.minValue = 0
        self.maxValue = 40
        ################################################################################################
        # DEFAULT START VALUE
        ################################################################################################
        self.value = self.minValue

        ################################################################################################
        # DEFAULT OFFSET
        ################################################################################################
        self.value_offset = 0

        self.valueNeedleSnapzone = 0.05
        self.last_value = 0

        # self.value2 = 0
        # self.value2Color = QColor(0, 0, 0, 255)

        ################################################################################################
        # DEFAULT RADIUS
        ################################################################################################
        self.gauge_color_outer_radius_factor = 1
        self.gauge_color_inner_radius_factor = 0.9

        self.center_horizontal_value = 0
        self.center_vertical_value = 0

        # self.debug1 = None
        # self.debug2 = None

        ################################################################################################
        # DEFAULT SCALE VALUE
        ################################################################################################
        self.scale_angle_start_value = 135
        self.scale_angle_size = 270

        self.angle_offset = 0

        # self.scalaCount = 10
        self.setScalaCount(10)
        self.scala_subdiv_count = 5

        self.pen = QPen(QColor(0, 0, 0))
        self.font = QFont('Decorative', 20, QFont.Bold)

        ################################################################################################
        # DEFAULT POLYGON COLOR
        ################################################################################################
        self.scale_polygon_colors = []
        self.set_scale_polygon_colors([[.00, Qt.red],
                                     [.1, Qt.yellow],
                                     [.15, Qt.green],
                                     [1, Qt.transparent]])

        ################################################################################################
        # DEFAULT SCALE TEXT STATUS
        ################################################################################################
        self.setEnableScaleText(True)
        self.scale_fontname = "Decorative"
        self.initial_scale_fontsize = 15
        self.scale_fontsize = self.initial_scale_fontsize

        ################################################################################################
        # DEFAULT VALUE TEXT STATUS
        ################################################################################################
        self.enable_value_text = True
        self.value_fontname = "Decorative"
        self.initial_value_fontsize = 40
        self.value_fontsize = self.initial_value_fontsize
        self.text_radius_factor = 0.5

        ################################################################################################
        # ENABLE BAR GRAPH BY DEFAULT
        ################################################################################################
        self.setEnableBarGraph(True)
        ################################################################################################
        # FILL POLYGON COLOR BY DEFAULT
        ################################################################################################
        self.setEnableScalePolygon(True)
        ################################################################################################
        # ENABLE CENTER POINTER BY DEFAULT
        ################################################################################################
        self.enable_CenterPoint = True
        ################################################################################################
        # ENABLE FINE SCALE BY DEFAULT
        ################################################################################################
        self.enable_fine_scaled_marker = True
        ################################################################################################
        # ENABLE BIG SCALE BY DEFAULT
        ################################################################################################
        self.enable_big_scaled_marker = True

        ################################################################################################
        # NEEDLE SCALE FACTOR/LENGTH
        ################################################################################################
        self.needle_scale_factor = 0.8
        ################################################################################################
        # ENABLE NEEDLE POLYGON BY DEFAULT
        ################################################################################################
        self.enable_Needle_Polygon = True

        ################################################################################################
        # ENABLE NEEDLE MOUSE TRACKING BY DEFAULT
        ################################################################################################
        self.setMouseTracking(False)

        ################################################################################################
        # SET GAUGE UNITS
        ################################################################################################
        self.units = "Km/h"

        # QTimer sorgt für neu Darstellung alle X ms
        # evtl performance hier verbessern mit self.update() und self.use_timer_event = False
        # todo: self.update als default ohne ueberpruefung, ob self.use_timer_event gesetzt ist oder nicht
        # Timer startet alle 10ms das event paintEvent
        if self.use_timer_event:
            timer = QTimer(self)
            timer.timeout.connect(self.update)
            timer.start(10)
        else:
            self.update()

        self.setGaugeTheme(10)

        # self.setGaugeTheme(0)


        # self.connect(self, SIGNAL("resize()"), self.rescaleMethod)

        # self.resize(300 , 300)
        ################################################################################################
        # RESIZE GAUGE
        ################################################################################################
        self.rescale_method()
    ################################################################################################
    # GAUGE THEMES
    ################################################################################################
    def setGaugeTheme(self, Theme = 1):
        if Theme == 0 or Theme == None:
            self.set_scale_polygon_colors([[.00, Qt.red],
                                    [.1, Qt.yellow],
                                    [.15, Qt.green],
                                    [1, Qt.transparent]])

            self.needle_center_bg = [
                                    [0, QColor(35, 40, 3, 255)], 
                                    [0.16, QColor(30, 36, 45, 255)], 
                                    [0.225, QColor(36, 42, 54, 255)], 
                                    [0.423963, QColor(19, 23, 29, 255)], 
                                    [0.580645, QColor(45, 53, 68, 255)], 
                                    [0.792627, QColor(59, 70, 88, 255)], 
                                    [0.935, QColor(30, 35, 45, 255)], 
                                    [1, QColor(35, 40, 3, 255)]
                                    ]

            self.outer_circle_bg =  [
                                    [0.0645161, QColor(30, 35, 45, 255)], 
                                    [0.37788, QColor(57, 67, 86, 255)], 
                                    [1, QColor(30, 36, 45, 255)]
                                    ]

        if Theme == 1:
            self.set_scale_polygon_colors([[.75, Qt.red],
                                     [.5, Qt.yellow],
                                     [.25, Qt.green]])

            self.needle_center_bg = [
                                    [0, QColor(35, 40, 3, 255)], 
                                    [0.16, QColor(30, 36, 45, 255)], 
                                    [0.225, QColor(36, 42, 54, 255)], 
                                    [0.423963, QColor(19, 23, 29, 255)], 
                                    [0.580645, QColor(45, 53, 68, 255)], 
                                    [0.792627, QColor(59, 70, 88, 255)], 
                                    [0.935, QColor(30, 35, 45, 255)], 
                                    [1, QColor(35, 40, 3, 255)]
                                    ]

            self.outer_circle_bg =  [
                                    [0.0645161, QColor(30, 35, 45, 255)], 
                                    [0.37788, QColor(57, 67, 86, 255)], 
                                    [1, QColor(30, 36, 45, 255)]
                                    ]

        if Theme == 2:
            self.set_scale_polygon_colors([[.25, Qt.red],
                                     [.5, Qt.yellow],
                                     [.75, Qt.green]])

            self.needle_center_bg = [
                                    [0, QColor(35, 40, 3, 255)], 
                                    [0.16, QColor(30, 36, 45, 255)], 
                                    [0.225, QColor(36, 42, 54, 255)], 
                                    [0.423963, QColor(19, 23, 29, 255)], 
                                    [0.580645, QColor(45, 53, 68, 255)], 
                                    [0.792627, QColor(59, 70, 88, 255)], 
                                    [0.935, QColor(30, 35, 45, 255)], 
                                    [1, QColor(35, 40, 3, 255)]
                                    ]

            self.outer_circle_bg =  [
                                    [0.0645161, QColor(30, 35, 45, 255)], 
                                    [0.37788, QColor(57, 67, 86, 255)], 
                                    [1, QColor(30, 36, 45, 255)]
                                    ]

        elif Theme == 3:
            self.set_scale_polygon_colors([[.00, Qt.white]])

            self.needle_center_bg = [
                                    [0, Qt.white], 
                                    ]

            self.outer_circle_bg =  [
                                    [0, Qt.white], 
                                    ]

        elif Theme == 4:
            self.set_scale_polygon_colors([[1, Qt.black]])

            self.needle_center_bg = [
                                    [0, Qt.black], 
                                    ]

            self.outer_circle_bg =  [
                                    [0, Qt.black], 
                                    ]

        elif Theme == 5:
            self.set_scale_polygon_colors([[1, QColor("#029CDE")]])  

            self.needle_center_bg = [
                                    [0, QColor("#029CDE")], 
                                    ]

            self.outer_circle_bg =  [
                                    [0, QColor("#029CDE")], 
                                    ]

        elif Theme == 6:
            self.set_scale_polygon_colors([[.75, QColor("#01ADEF")],
                                     [.5, QColor("#0086BF")],
                                     [.25, QColor("#005275")]])

            self.needle_center_bg = [
                                    [0, QColor(0, 46, 61, 255)], 
                                    [0.322581, QColor(1, 173, 239, 255)], 
                                    [0.571429, QColor(0, 73, 99, 255)],
                                    [1, QColor(0, 46, 61, 255)]
                                    ]

            self.outer_circle_bg =  [
                                    [0.0645161, QColor(0, 85, 116, 255)], 
                                    [0.37788, QColor(1, 173, 239, 255)], 
                                    [1, QColor(0, 69, 94, 255)]
                                    ]

        elif Theme == 7:
            self.set_scale_polygon_colors([[.25, QColor("#01ADEF")],
                                     [.5, QColor("#0086BF")],
                                     [.75, QColor("#005275")]])

            self.needle_center_bg = [
                                    [0, QColor(0, 46, 61, 255)], 
                                    [0.322581, QColor(1, 173, 239, 255)], 
                                    [0.571429, QColor(0, 73, 99, 255)],
                                    [1, QColor(0, 46, 61, 255)]
                                    ]

            self.outer_circle_bg =  [
                                    [0.0645161, QColor(0, 85, 116, 255)], 
                                    [0.37788, QColor(1, 173, 239, 255)], 
                                    [1, QColor(0, 69, 94, 255)]
                                    ]

        elif Theme == 8:
            self.set_scale_polygon_colors([[.25, QColor("#00ffff")],
                                     [.5, QColor("#017070")],
                                     [.75, QColor("#002929")]])

            self.needle_center_bg = [
                                    [0, QColor("#013b3b")], 
                                    [0.322581, QColor("#00ffff")], 
                                    [0.571429, QColor("#018a8a")],
                                    [1, QColor("#013b3b")]
                                    ]

            self.outer_circle_bg =  [
                                    [0.0645161, QColor("#013b3b")], 
                                    [0.37788, QColor("#0")], 
                                    [1, QColor("#0")]
                                    ]

        elif Theme == 9:
            self.set_scale_polygon_colors([[.25, QColor("#ff007f")],
                                     [.5, QColor("#aa0055")],
                                     [.75, QColor("#830042")]])

            self.needle_center_bg = [
                                    [0, QColor("#830042")], 
                                    [0.322581, QColor("#ff007f")], 
                                    [0.571429, QColor("#aa0055")],
                                    [1, QColor("#830042")]
                                    ]

            self.outer_circle_bg =  [
                                    [0.0645161, QColor("#830042")], 
                                    [0.37788, QColor("#ff007f")], 
                                    [1, QColor("#ff007f")]
                                    ]

        elif Theme == 10:
            self.set_scale_polygon_colors([[.25, QColor("#ffe75d")],
                                     [.5, QColor("#896c1a")],
                                     [.75, QColor("#232803")]])

            self.needle_center_bg = [
                                    [0, QColor("#232803")], 
                                    [0.322581, QColor("#ffe75d")], 
                                    [0.571429, QColor("#896c1a")],
                                    [1, QColor("#232803")]
                                    ]

            self.outer_circle_bg =  [
                                    [0.0645161, QColor("#fc031c")], 
                                    [0.37788, QColor("#fc031c")], 
                                    [1, QColor("#fc031c")]
                                    ]




    ################################################################################################
    # RESCALE
    ################################################################################################
    def rescale_method(self):
        # print("slotMethod")
        ################################################################################################
        # SET WIDTH AND HEIGHT
        ################################################################################################
        if self.width() <= self.height():
            self.widget_diameter = self.width()
        else:
            self.widget_diameter = self.height()

        ################################################################################################
        # SET NEEDLE SIZE
        ################################################################################################
        self.change_value_needle_style([QPolygon([
            QPoint(4, 30),
            QPoint(-4, 30),
            QPoint(-2, - self.widget_diameter / 2 * self.needle_scale_factor),
            QPoint(0, - self.widget_diameter / 2 * self.needle_scale_factor - 6),
            QPoint(2, - self.widget_diameter / 2 * self.needle_scale_factor)
        ])])


        ################################################################################################
        # SET FONT SIZE
        ################################################################################################
        self.scale_fontsize = self.initial_scale_fontsize * self.widget_diameter / 400
        self.value_fontsize = self.initial_value_fontsize * self.widget_diameter / 400


    def change_value_needle_style(self, design):
        # prepared for multiple needle instrument
        self.value_needle = []
        for i in design:
            self.value_needle.append(i)
        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # UPDATE VALUE
    ################################################################################################
    def updateValue(self, value, mouse_controlled = False):
        if not mouse_controlled:
            self.value = value
        #
        # if mouse_controlled:
        #     self.valueChanged.emit(int(value))

        if value <= self.minValue:
            self.value = self.minValue
        elif value >= self.maxValue:
            self.value = self.maxValue
        else:
            self.value = value
        # self.paintEvent("")
        self.valueChanged.emit(int(value))
        # print(self.value)

        # ohne timer: aktiviere self.update()
        if not self.use_timer_event:
            self.update()
        

    def updateAngleOffset(self, offset):
        self.angle_offset = offset
        if not self.use_timer_event:
            self.update()

    def center_horizontal(self, value):
        self.center_horizontal_value = value
        # print("horizontal: " + str(self.center_horizontal_value))

    def center_vertical(self, value):
        self.center_vertical_value = value
        # print("vertical: " + str(self.center_vertical_value))

    ################################################################################################
    # SET NEEDLE COLOR
    ################################################################################################
    def setNeedleColor(self, R=50, G=50, B=50, Transparency=255):
        # Red: R = 0 - 255
        # Green: G = 0 - 255
        # Blue: B = 0 - 255
        # Transparency = 0 - 255
        self.NeedleColor = QColor(R, G, B, Transparency)
        self.NeedleColorReleased = self.NeedleColor

        if not self.use_timer_event:
            self.update()
    ################################################################################################
    # SET NEEDLE COLOR ON DRAG
    ################################################################################################
    def setNeedleColorOnDrag(self, R=50, G=50, B=50, Transparency=255):
        # Red: R = 0 - 255
        # Green: G = 0 - 255
        # Blue: B = 0 - 255
        # Transparency = 0 - 255
        self.NeedleColorDrag = QColor(R, G, B, Transparency)

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET SCALE VALUE COLOR
    ################################################################################################
    def setScaleValueColor(self, R=50, G=50, B=50, Transparency=255):
        # Red: R = 0 - 255
        # Green: G = 0 - 255
        # Blue: B = 0 - 255
        # Transparency = 0 - 255
        self.ScaleValueColor = QColor(R, G, B, Transparency)

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET DISPLAY VALUE COLOR
    ################################################################################################
    def setDisplayValueColor(self, R=50, G=50, B=50, Transparency=255):
        # Red: R = 0 - 255
        # Green: G = 0 - 255
        # Blue: B = 0 - 255
        # Transparency = 0 - 255
        self.DisplayValueColor = QColor(R, G, B, Transparency)

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET CENTER POINTER COLOR
    ################################################################################################
    def set_CenterPointColor(self, R=50, G=50, B=50, Transparency=255):
        self.CenterPointColor = QColor(R, G, B, Transparency)

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SHOW HIDE NEEDLE POLYGON
    ################################################################################################
    def setEnableNeedlePolygon(self, enable = True):
        self.enable_Needle_Polygon = enable

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SHOW HIDE SCALE TEXT
    ################################################################################################
    def setEnableScaleText(self, enable = True):
        self.enable_scale_text = enable

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SHOW HIDE BAR GRAPH
    ################################################################################################
    def setEnableBarGraph(self, enable = True):
        self.enableBarGraph = enable

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SHOW HIDE VALUE TEXT
    ################################################################################################
    def setEnableValueText(self, enable = True):
        self.enable_value_text = enable

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SHOW HIDE CENTER POINTER
    ################################################################################################
    def setEnableCenterPoint(self, enable = True):
        self.enable_CenterPoint = enable

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SHOW HIDE FILLED POLYGON
    ################################################################################################
    def setEnableScalePolygon(self, enable = True):
        self.enable_filled_Polygon = enable

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SHOW HIDE BIG SCALE
    ################################################################################################
    def setEnableBigScaleGrid(self, enable = True):
        self.enable_big_scaled_marker = enable

        if not self.use_timer_event:
            self.update()


    ################################################################################################
    # SHOW HIDE FINE SCALE
    ################################################################################################
    def setEnableFineScaleGrid(self, enable = True):
        self.enable_fine_scaled_marker = enable

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SHOW HIDE SCALA MAIN CONT
    ################################################################################################
    def setScalaCount(self, count):
        if count < 1:
            count = 1
        self.scalaCount = count

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET MINIMUM VALUE
    ################################################################################################
    def setMinValue(self, min):
        if self.value < min:
            self.value = min
        if min >= self.maxValue:
            self.minValue = self.maxValue - 1
        else:
            self.minValue = min

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET MAXIMUM VALUE
    ################################################################################################
    def setMaxValue(self, max):
        if self.value > max:
            self.value = max
        if max <= self.minValue:
            self.maxValue = self.minValue + 1
        else:
            self.maxValue = max

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET SCALE ANGLE
    ################################################################################################
    def setScaleStartAngle(self, value):
        # Value range in DEG: 0 - 360
        self.scale_angle_start_value = value
        # print("startFill: " + str(self.scale_angle_start_value))

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET SCALE SIZE
    ################################################################################################
    def setTotalScaleAngleSize(self, value):
        self.scale_angle_size = value
        # print("stopFill: " + str(self.scale_angle_size))

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET GAUGE COLOR OUTER RADIUS
    ################################################################################################
    def setGaugeColorOuterRadiusFactor(self, value):
        self.gauge_color_outer_radius_factor = float(value) / 1000
        # print(self.gauge_color_outer_radius_factor)

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET GAUGE COLOR INNER RADIUS
    ################################################################################################
    def setGaugeColorInnerRadiusFactor(self, value):
        self.gauge_color_inner_radius_factor = float(value) / 1000
        # print(self.gauge_color_inner_radius_factor)

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # SET SCALE POLYGON COLOR
    ################################################################################################
    def set_scale_polygon_colors(self, color_array):
        # print(type(color_array))
        if 'list' in str(type(color_array)):
            self.scale_polygon_colors = color_array
        elif color_array == None:
            self.scale_polygon_colors = [[.0, Qt.transparent]]
        else:
            self.scale_polygon_colors = [[.0, Qt.transparent]]

        if not self.use_timer_event:
            self.update()

    ################################################################################################
    # GET MAXIMUM VALUE
    ################################################################################################
    def get_value_max(self):
        return self.maxValue

    ###############################################################################################
    # SCALE PAINTER
    ###############################################################################################

    ################################################################################################
    # CREATE PIE
    ################################################################################################
    def create_polygon_pie(self, outer_radius, inner_raduis, start, lenght, bar_graph = True):
        polygon_pie = QPolygonF()
        # start = self.scale_angle_start_value
        # start = 0
        # lenght = self.scale_angle_size
        # lenght = 180
        # inner_raduis = self.width()/4
        # print(start)
        n = 360     # angle steps size for full circle
        # changing n value will causes drawing issues
        w = 360 / n   # angle per step
        # create outer circle line from "start"-angle to "start + lenght"-angle
        x = 0
        y = 0

        # todo enable/disable bar graf here
        if not self.enableBarGraph and bar_graph:
            # float_value = ((lenght / (self.maxValue - self.minValue)) * (self.value - self.minValue))
            lenght = int(round((lenght / (self.maxValue - self.minValue)) * (self.value - self.minValue)))
            # print("f: %s, l: %s" %(float_value, lenght))
            pass

        # mymax = 0

        for i in range(lenght+1):                                              # add the points of polygon
            t = w * i + start - self.angle_offset
            x = outer_radius * math.cos(math.radians(t))
            y = outer_radius * math.sin(math.radians(t))
            polygon_pie.append(QPointF(x, y))
        # create inner circle line from "start + lenght"-angle to "start"-angle
        for i in range(lenght+1):                                              # add the points of polygon
            # print("2 " + str(i))
            t = w * (lenght - i) + start - self.angle_offset
            x = inner_raduis * math.cos(math.radians(t))
            y = inner_raduis * math.sin(math.radians(t))
            polygon_pie.append(QPointF(x, y))

        # close outer line
        polygon_pie.append(QPointF(x, y))
        return polygon_pie

    def draw_filled_polygon(self, outline_pen_with=0):
        if not self.scale_polygon_colors == None:
            painter_filled_polygon = QPainter(self)
            painter_filled_polygon.setRenderHint(QPainter.Antialiasing)
            # Koordinatenursprung in die Mitte der Flaeche legen
            painter_filled_polygon.translate(self.width() / 2, self.height() / 2)

            painter_filled_polygon.setPen(Qt.NoPen)

            self.pen.setWidth(outline_pen_with)
            if outline_pen_with > 0:
                painter_filled_polygon.setPen(self.pen)

            colored_scale_polygon = self.create_polygon_pie(
                ((self.widget_diameter / 2) - (self.pen.width() / 2)) * self.gauge_color_outer_radius_factor,
                (((self.widget_diameter / 2) - (self.pen.width() / 2)) * self.gauge_color_inner_radius_factor),
                self.scale_angle_start_value, self.scale_angle_size)

            gauge_rect = QRect(QPoint(0, 0), QSize(self.widget_diameter / 2 - 1, self.widget_diameter - 1))
            grad = QConicalGradient(QPointF(0, 0), - self.scale_angle_size - self.scale_angle_start_value +
                                    self.angle_offset - 1)

            # todo definition scale color as array here
            for eachcolor in self.scale_polygon_colors:
                grad.setColorAt(eachcolor[0], eachcolor[1])
            # grad.setColorAt(.00, Qt.red)
            # grad.setColorAt(.1, Qt.yellow)
            # grad.setColorAt(.15, Qt.green)
            # grad.setColorAt(1, Qt.transparent)
            painter_filled_polygon.setBrush(grad)
            # self.brush = QBrush(QColor(255, 0, 255, 255))
            # painter_filled_polygon.setBrush(self.brush)
            painter_filled_polygon.drawPolygon(colored_scale_polygon)
            # return painter_filled_polygon

    ###############################################################################################
    # BIG SCALE MARKERS
    ###############################################################################################
    def draw_big_scaled_markter(self):
        my_painter = QPainter(self)
        my_painter.setRenderHint(QPainter.Antialiasing)
        # Koordinatenursprung in die Mitte der Flaeche legen
        my_painter.translate(self.width() / 2, self.height() / 2)

        # my_painter.setPen(Qt.NoPen)
        self.pen = QPen(QColor(0, 0, 0, 255))
        self.pen.setWidth(2)
        # # if outline_pen_with > 0:
        my_painter.setPen(self.pen)

        my_painter.rotate(self.scale_angle_start_value - self.angle_offset)
        steps_size = (float(self.scale_angle_size) / float(self.scalaCount))
        scale_line_outer_start = self.widget_diameter/2
        scale_line_lenght = (self.widget_diameter / 2) - (self.widget_diameter / 20)
        # print(stepszize)
        for i in range(self.scalaCount+1):
            my_painter.drawLine(scale_line_lenght, 0, scale_line_outer_start, 0)
            my_painter.rotate(steps_size)

    def create_scale_marker_values_text(self):
        painter = QPainter(self)
        # painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.Antialiasing)

        # Koordinatenursprung in die Mitte der Flaeche legen
        painter.translate(self.width() / 2, self.height() / 2)
        # painter.save()
        font = QFont(self.scale_fontname, self.scale_fontsize, QFont.Bold)
        fm = QFontMetrics(font)

        pen_shadow = QPen()

        pen_shadow.setBrush(self.ScaleValueColor)
        painter.setPen(pen_shadow)

        text_radius_factor = 0.8
        text_radius = self.widget_diameter/2 * text_radius_factor

        scale_per_div = int((self.maxValue - self.minValue) / self.scalaCount)

        angle_distance = (float(self.scale_angle_size) / float(self.scalaCount))
        for i in range(self.scalaCount + 1):
            # text = str(int((self.maxValue - self.minValue) / self.scalaCount * i))
            text = str(int(self.minValue + scale_per_div * i))
            w = fm.width(text) + 1
            h = fm.height()
            painter.setFont(QFont(self.scale_fontname, self.scale_fontsize, QFont.Bold))
            angle = angle_distance * i + float(self.scale_angle_start_value - self.angle_offset)
            x = text_radius * math.cos(math.radians(angle))
            y = text_radius * math.sin(math.radians(angle))
            # print(w, h, x, y, text)

            text = [x - int(w/2), y - int(h/2), int(w), int(h), Qt.AlignCenter, text]
            painter.drawText(text[0], text[1], text[2], text[3], text[4], text[5])
        # painter.restore()

    ################################################################################################
    # FINE SCALE MARKERS
    ################################################################################################
    def create_fine_scaled_marker(self):
        #  Description_dict = 0
        my_painter = QPainter(self)

        my_painter.setRenderHint(QPainter.Antialiasing)
        # Koordinatenursprung in die Mitte der Flaeche legen
        my_painter.translate(self.width() / 2, self.height() / 2)

        my_painter.setPen(Qt.black)
        my_painter.rotate(self.scale_angle_start_value - self.angle_offset)
        steps_size = (float(self.scale_angle_size) / float(self.scalaCount * self.scala_subdiv_count))
        scale_line_outer_start = self.widget_diameter/2
        scale_line_lenght = (self.widget_diameter / 2) - (self.widget_diameter / 40)
        for i in range((self.scalaCount * self.scala_subdiv_count)+1):
            my_painter.drawLine(scale_line_lenght, 0, scale_line_outer_start, 0)
            my_painter.rotate(steps_size)

    ################################################################################################
    # VALUE TEXT
    ################################################################################################
    def create_values_text(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        # painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        # painter.save()
        # xShadow = 3.0
        # yShadow = 3.0
        font = QFont(self.value_fontname, self.value_fontsize, QFont.Bold)
        fm = QFontMetrics(font)

        pen_shadow = QPen()

        pen_shadow.setBrush(self.DisplayValueColor)
        painter.setPen(pen_shadow)

        text_radius = self.widget_diameter / 2 * self.text_radius_factor

        # angle_distance = (float(self.scale_angle_size) / float(self.scalaCount))
        # for i in range(self.scalaCount + 1):
        text = str(int(self.value))
        w = fm.width(text) + 1
        h = fm.height()
        painter.setFont(QFont(self.value_fontname, self.value_fontsize, QFont.Bold))

        # Mitte zwischen Skalenstart und Skalenende:
        # Skalenende = Skalenanfang - 360 + Skalenlaenge
        # Skalenmitte = (Skalenende - Skalenanfang) / 2 + Skalenanfang
        angle_end = float(self.scale_angle_start_value + self.scale_angle_size - 360)
        angle = (angle_end - self.scale_angle_start_value) / 2 + self.scale_angle_start_value

        x = text_radius * math.cos(math.radians(angle))
        y = text_radius * math.sin(math.radians(angle))
        # print(w, h, x, y, text)
        text = [x - int(w/2), y - int(h/2), int(w), int(h), Qt.AlignCenter, text]
        painter.drawText(text[0], text[1], text[2], text[3], text[4], text[5])


    ################################################################################################
    # UNITS TEXT
    ################################################################################################
    def create_units_text(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        # painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        font = QFont(self.value_fontname, int(self.value_fontsize / 2.5), QFont.Bold)
        fm = QFontMetrics(font)

        pen_shadow = QPen()

        pen_shadow.setBrush(self.DisplayValueColor)
        painter.setPen(pen_shadow)

        text_radius = self.widget_diameter / 2 * self.text_radius_factor

        text = str(self.units)
        w = fm.width(text) + 1
        h = fm.height()
        painter.setFont(QFont(self.value_fontname, int(self.value_fontsize / 2.5), QFont.Bold))

      
        angle_end = float(self.scale_angle_start_value + self.scale_angle_size + 180)
        angle = (angle_end - self.scale_angle_start_value) / 2 + self.scale_angle_start_value

        x = text_radius * math.cos(math.radians(angle))
        y = text_radius * math.sin(math.radians(angle))
        # print(w, h, x, y, text)
        text = [x - int(w/2), y - int(h/2), int(w), int(h), Qt.AlignCenter, text]
        painter.drawText(text[0], text[1], text[2], text[3], text[4], text[5])


    ################################################################################################
    # CENTER POINTER
    ################################################################################################
    def draw_big_needle_center_point(self, diameter=30):
        painter = QPainter(self)
        # painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.Antialiasing)

        # Koordinatenursprung in die Mitte der Flaeche legen
        painter.translate(self.width() / 2, self.height() / 2)
        painter.setPen(Qt.NoPen)
        # painter.setPen(Qt.NoPen)

        # painter.setBrush(self.CenterPointColor)
        # diameter = diameter # self.widget_diameter/6
        # painter.drawEllipse(int(-diameter / 2), int(-diameter / 2), int(diameter), int(diameter))


        # create_polygon_pie(self, outer_radius, inner_raduis, start, lenght)
        colored_scale_polygon = self.create_polygon_pie(
                ((self.widget_diameter / 8) - (self.pen.width() / 2)),
                0,
                self.scale_angle_start_value, 360, False)

        # 150.0 0.0 131 360

        grad = QConicalGradient(QPointF(0, 0), 0)

        # todo definition scale color as array here
        for eachcolor in self.needle_center_bg:
            grad.setColorAt(eachcolor[0], eachcolor[1])
        # grad.setColorAt(.00, Qt.red)
        # grad.setColorAt(.1, Qt.yellow)
        # grad.setColorAt(.15, Qt.green)
        # grad.setColorAt(1, Qt.transparent)
        painter.setBrush(grad)
        # self.brush = QBrush(QColor(255, 0, 255, 255))
        # painter_filled_polygon.setBrush(self.brush)

        painter.drawPolygon(colored_scale_polygon)
        # return painter_filled_polygon

    ################################################################################################
    # CREATE OUTER COVER
    ################################################################################################
    def draw_outer_circle(self, diameter=30):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.setPen(Qt.NoPen)
        colored_scale_polygon = self.create_polygon_pie(
                ((self.widget_diameter / 2) - (self.pen.width())),
                (self.widget_diameter / 6),
                self.scale_angle_start_value / 10, 360, False)

        radialGradient = QRadialGradient(QPointF(0, 0), self.width())

        for eachcolor in self.outer_circle_bg:
            radialGradient.setColorAt(eachcolor[0], eachcolor[1])


        painter.setBrush(radialGradient)

        painter.drawPolygon(colored_scale_polygon)


    ################################################################################################
    # NEEDLE POINTER
    ################################################################################################
    def draw_needle(self):
        painter = QPainter(self)
        # painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.Antialiasing)
        # Koordinatenursprung in die Mitte der Flaeche legen
        painter.translate(self.width() / 2, self.height() / 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.NeedleColor)
        painter.rotate(((self.value - self.value_offset - self.minValue) * self.scale_angle_size /
                        (self.maxValue - self.minValue)) + 90 + self.scale_angle_start_value)

        painter.drawConvexPolygon(self.value_needle[0])

    ###############################################################################################
    # EVENTS
    ###############################################################################################

    ################################################################################################
    # ON WINDOW RESIZE
    ################################################################################################
    def resizeEvent(self, event):
        # self.resized.emit()
        # return super(self.parent, self).resizeEvent(event)
        # print("resized")
        # print(self.width())
        self.rescale_method()
        # self.emit(QtCore.SIGNAL("resize()"))
        # print("resizeEvent")

    ################################################################################################
    # ON PAINT EVENT
    ################################################################################################
    def paintEvent(self, event):
        # Main Drawing Event:
        # Will be executed on every change
        # vgl http://doc.qt.io/qt-4.8/qt-demos-affine-xform-cpp.html
        # print("event", event)

        self.draw_outer_circle()
        # colored pie area
        if self.enable_filled_Polygon:
            self.draw_filled_polygon()

        # draw scale marker lines
        if self.enable_fine_scaled_marker:
            self.create_fine_scaled_marker()
        if self.enable_big_scaled_marker:
            self.draw_big_scaled_markter()

        # draw scale marker value text
        if self.enable_scale_text:
            self.create_scale_marker_values_text()

        # Display Value
        if self.enable_value_text:
            self.create_values_text()
            self.create_units_text()

        # draw needle 1
        if self.enable_Needle_Polygon:
            self.draw_needle()

        # Draw Center Point
        if self.enable_CenterPoint:
            self.draw_big_needle_center_point(diameter=(self.widget_diameter / 6))


    ###############################################################################################
    # MOUSE EVENTS
    ###############################################################################################

    def setMouseTracking(self, flag):
        def recursive_set(parent):
            for child in parent.findChildren(QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)

        QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def mouseReleaseEvent(self, QMouseEvent):
        self.NeedleColor = self.NeedleColorReleased

        if not self.use_timer_event:
            self.update()
        pass

    ########################################################################
    ## MOUSE LEAVE EVENT
    ########################################################################
    # def leaveEvent(self, event):
    #     self.NeedleColor = self.NeedleColorReleased
    #     self.update() 

    # def mouseMoveEvent(self, event):
    #     x, y = event.x() - (self.width() / 2), event.y() - (self.height() / 2)
    #     # print(event.x(), event.y(), self.width(), self.height())
    #     if not x == 0: 
    #         angle = math.atan2(y, x) / math.pi * 180
    #         # winkellaenge der anzeige immer positiv 0 - 360deg
    #         # min wert + umskalierter wert
    #         value = (float(math.fmod(angle - self.scale_angle_start_value + 720, 360)) / \
    #                  (float(self.scale_angle_size) / float(self.maxValue - self.minValue))) + self.minValue
    #         temp = value
    #         fmod = float(math.fmod(angle - self.scale_angle_start_value + 720, 360))
    #         state = 0
    #         if (self.value - (self.maxValue - self.minValue) * self.valueNeedleSnapzone) <= \
    #                 value <= \
    #                 (self.value + (self.maxValue - self.minValue) * self.valueNeedleSnapzone):
    #             self.NeedleColor = self.NeedleColorDrag
    #             # todo: evtl ueberpruefen
    #             #
    #             state = 9
    #             # if value >= self.maxValue and self.last_value < (self.maxValue - self.minValue) / 2:
    #             if value >= self.maxValue and self.last_value < (self.maxValue - self.minValue) / 2:
    #                 state = 1
    #                 value = self.maxValue
    #                 self.last_value = self.minValue
    #                 self.valueChanged.emit(int(value))

    #             elif value >= self.maxValue >= self.last_value:
    #                 state = 2
    #                 value = self.maxValue
    #                 self.last_value = self.maxValue
    #                 self.valueChanged.emit(int(value))


    #             else:
    #                 state = 3
    #                 self.last_value = value
    #                 self.valueChanged.emit(int(value))

    #             self.updateValue(value)            



                # todo: mouse event debug output

                # self.updateValue(value, mouse_controlled=True)

                # self.valueChanged.emit(int(value))
                # print(str(int(value)))
            # self.valueChanged.emit()

            # todo: convert print to logging debug
            # print('mouseMoveEvent: x=%d, y=%d, a=%s, v=%s, fmod=%s, temp=%s, state=%s' % (
                # x, y, angle, value, fmod, temp, state))



################################################################################################
# END ==>
################################################################################################
