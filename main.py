#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from qtstyles import StylePicker
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QFont
from utils.main_ui import MainWindow


for i in StylePicker().available_styles:
    print(i)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(StylePicker('qdark').get_sheet())
    app.setFont(QFont('微软雅黑', 9))
    mainWindow = MainWindow()
    sys.exit(app.exec_())
