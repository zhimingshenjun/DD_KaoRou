#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QGridLayout, QFileDialog, QDialog, QLabel, QPushButton, QLineEdit
from PySide2.QtGui import QFont
from PySide2.QtCore import Qt, Signal


class exportSubtitle(QDialog):
    exportArgs = Signal(list)

    def __init__(self):
        super().__init__()
        self.subNum = 1
        self.setWindowTitle('字幕裁剪: 第%s列字幕' % self.subNum)
        self.resize(800, 200)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.startLabel = QLabel('视频起始时间：')
        self.layout.addWidget(self.startLabel, 0, 0, 1, 2)
        self.startEdit = QLineEdit('00:00.0')
        self.layout.addWidget(self.startEdit, 0, 2, 1, 2)
        self.startEdit.setAlignment(Qt.AlignRight)
        self.startEdit.setFixedWidth(100)
        self.startEdit.setFont(QFont('Timers', 14))
        self.startEdit.textChanged.connect(self.setSubtStart)

        self.endLabel = QLabel('视频结束时间：')
        self.layout.addWidget(self.endLabel, 0, 4, 1, 2)
        self.endEdit = QLineEdit('00:00.0')
        self.layout.addWidget(self.endEdit, 0, 6, 1, 2)
        self.endEdit.setAlignment(Qt.AlignRight)
        self.endEdit.setFixedWidth(100)
        self.endEdit.setFont(QFont('Timers', 14))

        self.subStartLabel = QLabel('字幕起始时间：')
        self.layout.addWidget(self.subStartLabel, 0, 8, 1, 2)
        self.subStartEdit = QLineEdit('00:00.0')
        self.layout.addWidget(self.subStartEdit, 0, 10, 1, 2)
        self.subStartEdit.setAlignment(Qt.AlignRight)
        self.subStartEdit.setFixedWidth(100)
        self.subStartEdit.setFont(QFont('Timers', 14))

        self.outputButton = QPushButton('保存路径')
        self.layout.addWidget(self.outputButton, 1, 0, 1, 1)
        self.outputButton.clicked.connect(self.outputChoose)
        self.outputPath = QLineEdit()
        self.layout.addWidget(self.outputPath, 1, 1, 1, 8)

        self.startButton = QPushButton('开始导出')
        self.layout.addWidget(self.startButton, 1, 9, 1, 3)
        self.startButton.clicked.connect(self.export)

    def setSubtStart(self, t):
        self.subStartEdit.setText(t)

    def setDefault(self, startTime, endTime, subNum):
        self.endEdit.setText(endTime)
        self.subNum = subNum
        self.setWindowTitle('字幕导出: 第%s列字幕' % self.subNum)

    def outputChoose(self):
        start = self.startEdit.text().replace('：', ':').replace(':', '.')
        end = self.endEdit.text().replace('：', ':').replace(':', '.')
        subtitlePath = QFileDialog.getSaveFileName(self, "选择输出字幕文件夹", './未命名_第%s列字幕_%s-%s.srt' % (self.subNum, start, end), "字幕文件 (*.srt)")[0]
        if subtitlePath:
            self.outputPath.setText(subtitlePath)

    def export(self):
        start = self.startEdit.text().replace('：', ':')
        end = self.endEdit.text().replace('：', ':')
        subStart = self.subStartEdit.text().replace('：', ':')
        self.exportArgs.emit([start, end, subStart, self.outputPath.text()])
