#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, multiprocessing
from PySide2.QtWidgets import QApplication, QSplashScreen
from PySide2.QtGui import QFont, QPixmap
from utils.main_ui import MainWindow


if __name__ == '__main__':
    multiprocessing.freeze_support()
    qss = ''
    try:
        with open('utils/qdark.qss', 'r') as f:
            qss = f.read()
    except:
        print('警告！找不到QSS文件！请从github项目地址下载完整文件。')
    app = QApplication(sys.argv)
    app.setStyleSheet(qss)
    app.setFont(QFont('微软雅黑', 9))
    splash = QSplashScreen(QPixmap(r'utils\splash.jpg'))
    splash.show()
    mainWindow = MainWindow()
    mainWindow.show()
    splash.finish(mainWindow)
    sys.exit(app.exec_())
