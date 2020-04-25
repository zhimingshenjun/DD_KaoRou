#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QFont
from utils.main_ui import MainWindow


if __name__ == '__main__':
    qss = ''
    try:
        with open('utils/qdark.qss', 'r') as f:
            qss = f.read()
    except:
        print('警告！找不到QSS文件！请从github项目地址下载完整文件。')
    app = QApplication(sys.argv)
    app.setStyleSheet(qss)
    app.setFont(QFont('微软雅黑', 9))
    mainWindow = MainWindow()
    sys.exit(app.exec_())
