#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pyqtgraph as pg
pg.setConfigOption('background', '#232629')
from PySide2.QtWidgets import QWidget, QMainWindow, QGridLayout, QFileDialog, QToolBar,\
        QAction, QDialog, QStyle, QSlider, QLabel, QPushButton, QStackedWidget, QHBoxLayout,\
        QLineEdit, QTableWidget, QAbstractItemView, QTableWidgetItem, QGraphicsTextItem, QMenu,\
        QGraphicsScene, QGraphicsView, QGraphicsDropShadowEffect, QComboBox, QMessageBox, QColorDialog
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtMultimediaWidgets import QGraphicsVideoItem
from PySide2.QtGui import QIcon, QKeySequence, QFont, QColor
from PySide2.QtCore import Qt, QTimer, QEvent, QPoint, Signal, QSizeF, QUrl


def ms2Time(ms):
    '''
    receive int
    return str
    ms -> m:s.ms
    '''
    m, s = divmod(ms, 60000)
    s, ms = divmod(s, 1000)
    return ('%s:%02d.%03d' % (m, s, ms))[:-1]


class graph(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        self.graph = pg.PlotWidget()
        self.graph.disableAutoRange()
        layout.addWidget(self.graph)

    def plot(self, x, y, color='#CCCCCC'):
        try:
            self.graph.plot(x, y, pen=pg.mkPen(color=color), clear=True)
            self.graph.setXRange(x[0], x[-1])
            min_y = min(y)
            max_y = max(y)
            if min_y > -1000 or max_y < 1000:
                self.graph.setYRange(-1000, 1000, padding=0.1)  # 上下边距
            else:
                self.graph.setYRange(min_y, max_y, padding=0.1)
            interval = len(x) // 10
            x = [x[0] + i * interval for i in range(11)]  # 设置x label为时间戳
            ticks = [ms2Time(int(ms)) for ms in x]
            modifiedTick = [[(x[i], ticks[i]) for i in range(11)]]
            ax = self.graph.getAxis('bottom')
            ax.setTicks(modifiedTick)
        except:
            pass
