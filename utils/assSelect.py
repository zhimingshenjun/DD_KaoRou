#!/usr/bin/python3
# -*- coding: utf-8 -*-

import codecs
from PySide2.QtWidgets import QWidget, QMainWindow, QGridLayout, QFileDialog, QToolBar,\
        QAction, QDialog, QStyle, QSlider, QLabel, QPushButton, QStackedWidget, QHBoxLayout,\
        QLineEdit, QTableWidget, QAbstractItemView, QTableWidgetItem, QGraphicsTextItem, QMenu,\
        QGraphicsScene, QGraphicsView, QGraphicsDropShadowEffect, QComboBox, QMessageBox, QColorDialog
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtMultimediaWidgets import QGraphicsVideoItem
from PySide2.QtGui import QIcon, QKeySequence, QFont, QBrush, QColor
from PySide2.QtCore import Qt, QTimer, QEvent, QPoint, Signal, QSizeF, QUrl


# def calSubTime(t):
#     '''
#     receive str
#     return int
#     h:m:s.ms -> ms in total
#     '''
#     h = int(t[:2])
#     m = int(t[3:5])
#     s = int(t[6:8])
#     t = t.replace(',', '.')
#     ms = int(('%s00' % t.split('.')[-1])[:3])
#     return h * 3600000 + m * 60000 + s * 1000 + ms

def calSubTime(t):
    '''
    receive str
    return int
    h:m:s.ms -> ms in total
    '''
    t = t.replace(',', '.').replace('：', ':')
    h, m, s = t.split(':')
    if '.' in s:
        s, ms = s.split('.')
        ms = ('%s00' % ms)[:3]
    else:
        ms = 0
    h, m, s, ms = map(int, [h, m, s, ms])
    return h * 3600000 + m * 60000 + s * 1000 + ms


class assSelect(QDialog):
    assSummary = Signal(list)

    def __init__(self):
        super().__init__()
        self.subDict = {'': {'Fontname': '', 'Fontsize': '', 'PrimaryColour': '', 'SecondaryColour': '',
                             'OutlineColour': '', 'BackColour': '', 'Bold': '', 'Italic': '', 'Underline': '', 'StrikeOut': '',
                             'ScaleX': '', 'ScaleY': '', 'Spacing': '', 'Angle': '', 'BorderStyle': '', 'Outline': '',
                             'Shadow': '', 'Alignment': '', 'MarginL': '', 'MarginR': '', 'MarginV': '', 'Encoding': '',
                             'Tableview': [], 'Events': []}}
        self.resize(550, 800)
        self.setWindowTitle('选择要导入的ass字幕轨道')
        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel('检测到字幕样式:'), 0, 0, 1, 1)
        layout.addWidget(QLabel(''), 0, 1, 1, 1)
        self.subCombox = QComboBox()
        self.subCombox.currentTextChanged.connect(self.selectChange)
        layout.addWidget(self.subCombox, 0, 2, 1, 1)
        self.subTable = QTableWidget()
        self.subTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.subTable, 1, 0, 6, 3)
        self.confirm = QPushButton('导入')
        self.confirm.clicked.connect(self.sendSub)
        layout.addWidget(self.confirm, 7, 0, 1, 1)
        self.cancel = QPushButton('取消')
        self.cancel.clicked.connect(self.hide)
        layout.addWidget(self.cancel, 7, 2, 1, 1)

    def setDefault(self, subtitlePath='', index=0):
        if subtitlePath:
            self.assCheck(subtitlePath)
            self.index = index

    def selectChange(self, styleName):
        self.subTable.clear()
        self.subTable.setRowCount(len(self.subDict[styleName]) + len(self.subDict[styleName]['Tableview']) - 2)
        self.subTable.setColumnCount(3)
        self.subTable.setColumnWidth(2, 270)
        y = 0
        for k, v in self.subDict[styleName].items():
            if k not in ['Tableview', 'Events']:
                self.subTable.setItem(y, 0, QTableWidgetItem(k))
                self.subTable.setItem(y, 1, QTableWidgetItem(v))
                y += 1
            elif k == 'Tableview':
                for line in v:
                    self.subTable.setItem(y, 0, QTableWidgetItem(line[0]))
                    self.subTable.setItem(y, 1, QTableWidgetItem(line[1]))
                    self.subTable.setItem(y, 2, QTableWidgetItem(line[2]))
                    y += 1

    def sendSub(self):
        self.assSummary.emit([self.index, self.subDict[self.subCombox.currentText()]])
        self.hide()

    def assCheck(self, subtitlePath):
        self.subDict = {'': {'Fontname': '', 'Fontsize': '', 'PrimaryColour': '', 'SecondaryColour': '',
                             'OutlineColour': '', 'BackColour': '', 'Bold': '', 'Italic': '', 'Underline': '', 'StrikeOut': '',
                             'ScaleX': '', 'ScaleY': '', 'Spacing': '', 'Angle': '', 'BorderStyle': '', 'Outline': '',
                             'Shadow': '', 'Alignment': '', 'MarginL': '', 'MarginR': '', 'MarginV': '', 'Encoding': '',
                             'Tableview': [], 'Events': []}}
        ass = codecs.open(subtitlePath, 'r', 'utf_8_sig')
        f = ass.readlines()
        ass.close()
        V4Token = False
        styleFormat = []
        styles = []
        eventToken = False
        eventFormat = []
        events = []
        for line in f:
            if '[V4+ Styles]' in line:
                V4Token = True
            elif V4Token and 'Format:' in line:
                styleFormat = line.strip().replace(' ', '').split(':')[1].split(',')
            elif V4Token and 'Style:' in line and styleFormat:
                styles.append(line.strip().replace(' ', '').split(':')[1].split(','))
            elif '[Events]' in line:
                eventToken = True
                V4Token = False
            elif eventToken and 'Format:' in line:
                eventFormat = line.strip().replace(' ', '').split(':')[1].split(',')
            elif eventToken and 'Comment:' in line and eventFormat:
                events.append(line.strip().replace(' ', '').split('Comment:')[1].split(','))
            elif eventToken and 'Dialogue:' in line and eventFormat:
                events.append(line.strip().replace(' ', '').split('Dialogue:')[1].split(','))

        for cnt, _format in enumerate(eventFormat):
            if _format == 'Start':
                Start = cnt
            elif _format == 'End':
                End = cnt
            elif _format == 'Style':
                Style = cnt
            elif _format == 'Text':
                Text = cnt

        for style in styles:
            styleName = style[0]
            self.subDict[styleName] = {'Fontname': '', 'Fontsize': '', 'PrimaryColour': '', 'SecondaryColour': '',
                                      'OutlineColour': '', 'BackColour': '', 'Bold': '', 'Italic': '', 'Underline': '', 'StrikeOut': '',
                                      'ScaleX': '', 'ScaleY': '', 'Spacing': '', 'Angle': '', 'BorderStyle': '', 'Outline': '',
                                      'Shadow': '', 'Alignment': '', 'MarginL': '', 'MarginR': '', 'MarginV': '', 'Encoding': '',
                                      'Tableview': [], 'Events': {}}
            for cnt, _format in enumerate(styleFormat):
                if _format in self.subDict[styleName]:
                    self.subDict[styleName][_format] = style[cnt]
            for line in events:
                if styleName == line[Style]:
                    start = calSubTime(line[Start])
                    delta = calSubTime(line[End]) - start
                    self.subDict[styleName]['Tableview'].append([line[Start], line[End], line[Text]])
                    self.subDict[styleName]['Events'][start] = [delta, line[Text]]

        self.subCombox.clear()
        combox = []
        for style in self.subDict.keys():
            if style:
                combox.append(style)
        self.subCombox.addItems(combox)
