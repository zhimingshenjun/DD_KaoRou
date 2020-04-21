#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess
from PySide2.QtWidgets import QWidget, QMainWindow, QGridLayout, QFileDialog, QToolBar,\
        QAction, QDialog, QStyle, QSlider, QLabel, QPushButton, QStackedWidget, QHBoxLayout,\
        QLineEdit, QTableWidget, QAbstractItemView, QTableWidgetItem, QGraphicsTextItem, QMenu,\
        QGraphicsScene, QGraphicsView, QGraphicsDropShadowEffect, QComboBox, QMessageBox,\
    QProgressBar, QColorDialog, QCheckBox
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtMultimediaWidgets import QGraphicsVideoItem
from PySide2.QtGui import QIcon, QKeySequence, QFont, QBrush, QColor
from PySide2.QtCore import Qt, QTimer, QEvent, QPoint, Signal, QSizeF, QUrl
from utils.youtube_downloader import YoutubeDnld
from utils.subtitle import exportSubtitle
from utils.videoDecoder import VideoDecoder


def calSubTime(t):
    '''
    receive str
    return int
    h:m:s.ms -> ms in total
    '''
    h = int(t[:2])
    m = int(t[3:5])
    s = int(t[6:8])
    t = t.replace(',', '.')
    ms = int(t.split('.')[-1])
    return h * 3600000 + m * 60000 + s * 1000 + ms


def calSubTime2(t):
    '''
    receive str
    return int
    m:s.ms -> ms in total
    '''
    t.replace(',', '.')
    m, s = t.split(':')
    if '.' in s:
        s, ms = s.split('.')
    else:
        ms = 0
    return int(m) * 60000 + int(s) * 1000 + int(ms)


def cnt2Time(cnt, interval):
    '''
    receive int
    return str
    count of interval times -> h:m:s,ms
    '''
    h, m = divmod(cnt, 3600000 // interval)
    m, s = divmod(m, 60000 // interval)
    s, ms = divmod(s, 1000 // interval)
    h = ('0%s' % h)[-2:]
    m = ('0%s' % m)[-2:]
    s = ('0%s' % s)[-2:]
    return '%s:%s:%s,%s00' % (h, m, s, ms)


def cnt2Time2(cnt, interval):
    '''
    receive int
    return str
    count of interval times -> m:s.ms
    '''
    m, s = divmod(cnt, 60000 // interval)
    s, ms = divmod(s, 1000 // interval)
    ms = ms * (interval // 100)
    s = ('0%s' % s)[-2:]
    return '%3s:%2s.%s' % (m, s, ms)


def ms2Time(ms):
    '''
    receive int
    return str
    ms -> h:m:s,ms
    '''
    h, m = divmod(ms, 3600000)
    m, s = divmod(m, 60000)
    s, ms = divmod(s, 1000)
    h = ('0%s' % h)[-2:]
    m = ('0%s' % m)[-2:]
    s = ('0%s' % s)[-2:]
    ms = ('%s00' % ms)[:3]
    return '%s:%s:%s,%s' % (h, m, s, ms)


class Slider(QSlider):
    pointClicked = Signal(QPoint)

    def mousePressEvent(self, event):
        self.pointClicked.emit(event.pos())

    def mouseMoveEvent(self, event):
        self.pointClicked.emit(event.pos())


class LineEdit(QLineEdit):
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()


class InitProcess(QDialog):
    def __init__(self):
        super().__init__()
        self.resize(250, 30)
        self.setWindowTitle('正在重建字幕轨道...')


class Label(QLabel):
    clicked = Signal()

    def mouseReleaseEvent(self, QMouseEvent):
        self.clicked.emit()


class PreviewSubtitle(QDialog):
    fontColor = '#ffffff'
    fontSize = 90
    bold = True
    italic = False
    shadowOffset = 4

    def __init__(self):
        super().__init__()
        self.resize(400, 200)
        self.setWindowTitle('设置预览字幕')
        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel('字体大小'), 0, 0, 1, 1)
        self.fontSizeBox = QComboBox()
        self.fontSizeBox.addItems([str(x * 10 + 30) for x in range(15)])
        self.fontSizeBox.setCurrentIndex(6)
        self.fontSizeBox.currentIndexChanged.connect(self.getFontSize)
        layout.addWidget(self.fontSizeBox, 0, 1, 1, 1)
        layout.addWidget(QLabel(''), 0, 2, 1, 1)
        layout.addWidget(QLabel('字体颜色'), 0, 3, 1, 1)
        self.fontColorSelect = Label()
        self.fontColorSelect.setAlignment(Qt.AlignCenter)
        self.fontColorSelect.setText(self.fontColor)
        self.fontColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.fontColor, self.colorReverse(self.fontColor)))
        self.fontColorSelect.clicked.connect(self.getFontColor)
        layout.addWidget(self.fontColorSelect, 0, 4, 1, 1)
        self.boldCheckBox = QCheckBox('粗体')
        self.boldCheckBox.setChecked(True)
        self.boldCheckBox.stateChanged.connect(self.boldChange)
        layout.addWidget(self.boldCheckBox, 1, 0, 1, 1)
        self.italicCheckBox = QCheckBox('斜体')
        self.italicCheckBox.stateChanged.connect(self.italicChange)
        layout.addWidget(self.italicCheckBox, 1, 1, 1, 1)
        layout.addWidget(QLabel('阴影距离'), 1, 3, 1, 1)
        self.shadowBox = QComboBox()
        self.shadowBox.addItems([str(x) for x in range(5)])
        self.shadowBox.setCurrentIndex(4)
        self.shadowBox.currentIndexChanged.connect(self.getShadow)
        layout.addWidget(self.shadowBox, 1, 4, 1, 1)

    def getFontSize(self, index):
        self.fontSize = [x * 10 + 30 for x in range(15)][index]

    def getFontColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.fontColor = color.name()
            self.fontColorSelect.setText(self.fontColor)
            self.fontColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.fontColor, self.colorReverse(self.fontColor)))

    def colorReverse(self, color):
        r = 255 - int(color[1:3], 16)
        g = 255 - int(color[3:5], 16)
        b = 255 - int(color[5:7], 16)
        return '#%s%s%s' % (hex(r)[2:], hex(g)[2:], hex(b)[2:])

    def boldChange(self):
        self.bold = self.boldCheckBox.isChecked()

    def italicChange(self):
        self.italic = self.italicCheckBox.isChecked()

    def getShadow(self, index):
        self.shadowOffset = index


class MainWindow(QMainWindow):  # Main window
    def __init__(self):
        super().__init__()
        self.setWindowTitle = 'DD烤肉机'
        self.resize(1870, 820)
        self.mainWidget = QWidget()
        self.mainLayout = QGridLayout()  # Grid layout
        self.mainLayout.setSpacing(10)
        self.mainWidget.setLayout(self.mainLayout)
        self.duration = 60000

        self.initProcess = InitProcess()
        self.previewSubtitle = PreviewSubtitle()
        self.dnldWindow = YoutubeDnld()
        self.exportWindow = exportSubtitle()
        self.videoDecoder = VideoDecoder()
        self.exportWindow.exportArgs.connect(self.exportSubtitle)
        self.stack = QStackedWidget()
        self.stack.setFixedWidth(1300)
        self.mainLayout.addWidget(self.stack, 0, 0, 10, 8)
        buttonWidget = QWidget()
        buttonLayout = QHBoxLayout()
        buttonWidget.setLayout(buttonLayout)
        self.playButton = QPushButton('从本地打开')
        self.playButton.clicked.connect(self.open)
        self.playButton.setFixedWidth(400)
        self.playButton.setFixedHeight(75)
        self.dnldButton = QPushButton('Youtube下载器')
        self.dnldButton.clicked.connect(self.popDnld)
        self.dnldButton.setFixedWidth(400)
        self.dnldButton.setFixedHeight(75)
        buttonLayout.addWidget(self.playButton)
        buttonLayout.addWidget(self.dnldButton)
        self.stack.addWidget(buttonWidget)

        self.videoPath = ''
        self.videoWidth = 1920
        self.videoHeight = 1080
        self.globalInterval = 200
        self.setPlayer()
        self.setSubtitle()
        self.setToolBar()
        self.setCentralWidget(self.mainWidget)
        self.playStatus = False
        self.volumeStatus = True
        self.volumeValue = 100
        self.subSelectedTxt = ''
        self.subReplayTime = 1
        self.clipBoard = []
        self.grabKeyboard()
        self.show()

    def setPlayer(self):
        self.playerWidget = QGraphicsVideoItem()
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.resize(1280, 730)
        self.scene.addItem(self.playerWidget)
        self.stack.addWidget(self.view)
        self.player = QMediaPlayer(self, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.playerWidget)
        self.view.installEventFilter(self)
        self.view.show()
        self.srtTextItemDict = {0: QGraphicsTextItem(), 1: QGraphicsTextItem(), 2: QGraphicsTextItem(), 3: QGraphicsTextItem(), 4: QGraphicsTextItem()}
        for _, srtTextItem in self.srtTextItemDict.items():
            self.scene.addItem(srtTextItem)

    def setSubtitle(self):
        self.subtitleDict = {x: {-1: [100, '']} for x in range(5)}
        self.subTimer = QTimer()
        self.subTimer.setInterval(100)
        self.subtitle = QTableWidget()
        self.subtitle.setAutoScroll(False)
        self.subtitle.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mainLayout.addWidget(self.subtitle, 0, 8, 10, 12)
        self.subtitle.setColumnCount(5)
        self.subtitle.selectRow(0)
        self.subtitle.setHorizontalHeaderLabels(['%s' % (i + 1) for i in range(5)])
        self.subtitle.setVerticalHeaderLabels([cnt2Time2(i, self.globalInterval) for i in range(self.subtitle.rowCount())])
        for index in range(5):
            self.subtitle.setColumnWidth(index, 130)
        self.subtitle.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.subtitle.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.subtitle.horizontalHeader().sectionClicked.connect(self.addSubtitle)
        self.subtitle.doubleClicked.connect(self.releaseKeyboard)
        self.subtitle.cellChanged.connect(self.subEdit)
        self.subtitle.verticalHeader().sectionClicked.connect(self.subHeaderClick)
        self.subtitle.verticalHeader().setFixedWidth(70)
        self.subtitle.setContextMenuPolicy(Qt.CustomContextMenu)
        self.subtitle.customContextMenuRequested.connect(self.popTableMenu)
        self.initSubtitle()

    def initSubtitle(self):
        self.initProcess.show()
        self.subtitle.cellChanged.disconnect(self.subEdit)
        for x in range(self.subtitle.columnCount()):
            for y in range(self.subtitle.rowCount()):
                self.subtitle.setSpan(y, x, 1, 1)
        self.subtitle.setRowCount(self.duration // self.globalInterval + 1)
        for x in range(self.subtitle.columnCount()):
            for y in range(self.subtitle.rowCount()):
                self.subtitle.setItem(y, x, QTableWidgetItem(''))
                self.subtitle.item(y, x).setBackground(QBrush(QColor('#232629')))
        self.subtitle.setVerticalHeaderLabels([cnt2Time2(i, self.globalInterval) for i in range(self.subtitle.rowCount())])
        self.subtitle.cellChanged.connect(self.subEdit)
        self.initProcess.hide()

    def addSubtitle(self, index):
        subtitlePath = QFileDialog.getOpenFileName(self, "请选择字幕", None, "字幕文件 (*.srt *.vtt)")[0]
        if subtitlePath:
            self.initProcess.show()
            self.subtitle.cellChanged.disconnect(self.subEdit)
            self.subtitle.setHorizontalHeaderItem(index, QTableWidgetItem(str(index + 1)))
            subData = {}
            with open(subtitlePath, 'r', encoding='utf-8') as f:
                f = f.readlines()
            subText = ''
            YoutubeAutoSub = False
            for l in f:
                if '<c>' in l:
                    YoutubeAutoSub = True
                    break
            for cnt, l in enumerate(f):
                if '<c>' in l:
                    lineData = l.split('c>')
                    if len(lineData) > 3:
                        subText, start, _ = lineData[0].split('<')
                        start = calSubTime(start[:-1]) // self.globalInterval * self.globalInterval
                        if start not in self.subtitleDict[index]:
                            end = calSubTime(lineData[-3][1:-2]) // self.globalInterval * self.globalInterval
                            for i in range(len(lineData) // 2):
                                subText += lineData[i * 2 + 1][:-2]
                            subData[start] = [end - start, subText]
                    else:
                        subText, start, _ = lineData[0].split('<')
                        start = calSubTime(start[:-1]) // self.globalInterval * self.globalInterval
                        if start not in self.subtitleDict[index]:
                            subText += lineData[1][:-2]
                            subData[start] = [self.globalInterval, subText]
                elif '-->' in l and f[cnt + 2].strip() and '<c>' not in f[cnt + 2]:
                    subText = f[cnt + 2][:-1]
                    start = calSubTime(l[:12]) // self.globalInterval * self.globalInterval
                    if start not in self.subtitleDict[index]:
                        end = calSubTime(l[17:29]) // self.globalInterval * self.globalInterval
                        subData[start] = [end - start, subText]
                if '-->' in l and f[cnt + 1].strip() and not YoutubeAutoSub:
                    start = calSubTime(l[:12]) // self.globalInterval * self.globalInterval
                    if start not in self.subtitleDict[index]:
                        end = calSubTime(l[17:29]) // self.globalInterval * self.globalInterval
                        delta = end - start
                        if delta > 10:
                            subData[start] = [delta, f[cnt + 1][:-1]]
            self.subtitleDict[index].update(subData)
            maxRow = 0
            for _, v in self.subtitleDict.items():
                startMax = max(v.keys())
                rowCount = (startMax + v[startMax][0]) // self.globalInterval
                if rowCount > maxRow:
                    maxRow = rowCount
            if maxRow < self.duration // self.globalInterval + 1:
                maxRow = self.duration // self.globalInterval
            else:
                self.duration = maxRow * self.globalInterval
            self.subtitle.setRowCount(maxRow)
            self.subtitle.setVerticalHeaderLabels([cnt2Time2(i, self.globalInterval) for i in range(self.subtitle.rowCount())])
            for start, rowData in subData.items():
                startRow = start // self.globalInterval
                endRow = startRow + rowData[0] // self.globalInterval
                for row in range(startRow, endRow):
                    self.subtitle.setItem(row, index, QTableWidgetItem(rowData[1]))
                    self.subtitle.item(row, index).setBackground(QBrush(QColor('#35545d')))
                self.subtitle.setSpan(startRow, index, endRow - startRow, 1)
            self.refreshComboBox()
            self.subtitle.cellChanged.connect(self.subEdit)
            self.initProcess.hide()

    def subTimeOut(self):
        fontColor = self.previewSubtitle.fontColor
        fontSize = (self.previewSubtitle.fontSize + 5) / 2.5
        fontBold = self.previewSubtitle.bold
        fontItalic = self.previewSubtitle.italic
        fontShadowOffset = self.previewSubtitle.shadowOffset
        for _, srtTextItem in self.srtTextItemDict.items():
            srtTextItem.setDefaultTextColor(fontColor)
            font = QFont()
            font.setFamily("微软雅黑")
            font.setPointSize(fontSize)
            font.setBold(fontBold)
            font.setItalic(fontItalic)
            srtTextItem.setFont(font)
            srtTextShadow = QGraphicsDropShadowEffect()
            srtTextShadow.setOffset(fontShadowOffset)
            srtTextItem.setGraphicsEffect(srtTextShadow)
        try:
            selected = self.subtitle.selectionModel().selection().indexes()
            for x, i in enumerate(selected):
                if self.subtitle.item(i.row(), x):
                    txt = self.subtitle.item(i.row(), x).text()
                    if txt:
                        self.srtTextItemDict[x].setPlainText('#%s：' % (x + 1) + txt)
                        txtSize = self.srtTextItemDict[x].boundingRect().size()
                        posY = self.playerWidget.size().height() - txtSize.height() * (x + 1)
                        posX = (self.playerWidget.size().width() - txtSize.width()) / 2
                        self.srtTextItemDict[x].setPos(posX, posY)
                    else:
                        self.srtTextItemDict[x].setPlainText('')
                else:
                    self.srtTextItemDict[x].setPlainText('')
        except:
            pass

    def subHeaderClick(self, index):
        if self.player.duration():
            position = index * self.globalInterval
            self.player.setPosition(position)
            self.videoSlider.setValue(position * 1000 // self.player.duration())
            self.setTimeLabel()

    def subEdit(self, row, index):
        repeat = self.subtitle.rowSpan(row, index)
        self.setSubtitleDict(row, index, repeat, self.subtitle.item(row, index).text())
        self.subtitle.cellChanged.disconnect(self.subEdit)
        for cnt in range(repeat):
            if self.subtitle.item(row + cnt, index).text():
                self.subtitle.item(row, index).setBackground(QBrush(QColor('#35545d')))
            else:
                self.subtitle.item(row, index).setBackground(QBrush(QColor('#232629')))
        self.subtitle.cellChanged.connect(self.subEdit)

    def setSubtitleDict(self, row, index, num, text):
        self.subtitleDict[index][row * self.globalInterval] = [num * self.globalInterval, text]

    def popTableMenu(self, pos):
        self.subtitle.cellChanged.disconnect(self.subEdit)
        pos = QPoint(pos.x() + 55, pos.y() + 30)
        menu = QMenu()
        copy = menu.addAction('复制')
        paste = menu.addAction('粘贴')
        setSpan = menu.addAction('合并')
        clrSpan = menu.addAction('拆分')
        addSub = menu.addAction('导入字幕')
        cutSub = menu.addAction('裁剪字幕')
        action = menu.exec_(self.subtitle.mapToGlobal(pos))
        selected = self.subtitle.selectionModel().selection().indexes()
        yList = [selected[0].row(), selected[-1].row()]
        xSet = set()
        for i in range(len(selected)):
            xSet.add(selected[i].column())
        if action == copy:
            for x in xSet:
                self.clipBoard = []
                for y in range(yList[0], yList[1] + 1):
                    if self.subtitle.item(y, x):
                        self.clipBoard.append(self.subtitle.item(y, x).text())
                    else:
                        self.clipBoard.append('')
                break
        elif action == paste:
            self.subtitle.cellChanged.connect(self.subEdit)
            for x in xSet:
                for cnt, text in enumerate(self.clipBoard):
                    self.subtitle.setItem(yList[0] + cnt, x, QTableWidgetItem(text))
                    self.subtitleDict[x][(yList[0] + cnt) * self.globalInterval] = [self.globalInterval, text]
            self.subtitle.cellChanged.disconnect(self.subEdit)
        elif action == setSpan:
            for x in xSet:
                if not self.subtitle.item(yList[0], x):
                    firstItem = ''
                else:
                    firstItem = self.subtitle.item(yList[0], x).text()
                for y in range(yList[0], yList[1] + 1):
                    self.subtitle.setSpan(y, x, 1, 1)
                    self.subtitle.setItem(y, x, QTableWidgetItem(firstItem))
                    self.subtitle.item(y, x).setBackground(QBrush(QColor('#35545d')))
                    if y * self.globalInterval in self.subtitleDict[x]:
                        del self.subtitleDict[x][y * self.globalInterval]
            for x in xSet:
                self.subtitle.setSpan(yList[0], x, yList[1] - yList[0] + 1, 1)
            self.setSubtitleDict(yList[0], x, yList[1] - yList[0] + 1, firstItem)
        elif action == clrSpan:
            for x in xSet:
                if not self.subtitle.item(yList[0], x):
                    firstItem = ''
                else:
                    firstItem = self.subtitle.item(yList[0], x).text()
                for cnt, y in enumerate(range(yList[0], yList[1] + 1)):
                    self.subtitle.setSpan(y, x, 1, 1)
                    if not cnt:
                        self.subtitle.setItem(yList[0], x, QTableWidgetItem(firstItem))
                        if firstItem:
                            self.subtitle.item(y, x).setBackground(QBrush(QColor('#35545d')))
                        else:
                            self.subtitle.item(y, x).setBackground(QBrush(QColor('#232629')))
                    else:
                        self.subtitle.setItem(y, x, QTableWidgetItem(''))
                        self.subtitle.item(y, x).setBackground(QBrush(QColor('#232629')))
                    self.setSubtitleDict(yList[0], x, yList[1] - yList[0] + 1, firstItem)
                break
        elif action == addSub:
            self.subtitle.cellChanged.connect(self.subEdit)
            for x in xSet:
                self.addSubtitle(x)
            self.subtitle.cellChanged.disconnect(self.subEdit)
        elif action == cutSub:
            for x in xSet:
                start = yList[0] * self.globalInterval
                end = yList[1] * self.globalInterval
                self.exportSubWindow(start, end, x + 1)
        self.subtitle.cellChanged.connect(self.subEdit)

    def setToolBar(self):
        '''
        menu bar, file menu, play menu, tool bar.
        '''
        toolBar = QToolBar()
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.addToolBar(toolBar)
        fileMenu = self.menuBar().addMenu('&文件')
        openAction = QAction(QIcon.fromTheme('document-open'), '&打开...', self, shortcut=QKeySequence.Open, triggered=self.open)
        fileMenu.addAction(openAction)
        downloadAction = QAction(QIcon.fromTheme('document-open'), '&Youtube下载器', self, triggered=self.popDnld)
        fileMenu.addAction(downloadAction)
        exitAction = QAction(QIcon.fromTheme('application-exit'), '&退出', self, shortcut='Ctrl+Q', triggered=self.close)
        fileMenu.addAction(exitAction)

        playMenu = self.menuBar().addMenu('&功能')
        self.playIcon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.pauseIcon = self.style().standardIcon(QStyle.SP_MediaPause)
        self.playAction = toolBar.addAction(self.playIcon, '播放')
        self.playAction.triggered.connect(self.mediaPlay)
        self.volumeIcon = self.style().standardIcon(QStyle.SP_MediaVolume)
        self.volumeMuteIcon = self.style().standardIcon(QStyle.SP_MediaVolumeMuted)
        self.volumeAction = toolBar.addAction(self.volumeIcon, '静音')
        self.volumeAction.triggered.connect(self.volumeMute)
        previewAction = QAction(QIcon.fromTheme('document-open'), '&设置预览字幕', self, triggered=self.popPreview)
        playMenu.addAction(previewAction)

        decodeMenu = self.menuBar().addMenu('&输出')
        decodeAction = QAction(QIcon.fromTheme('document-open'), '&输出字幕及视频', self, triggered=self.decode)
        decodeMenu.addAction(decodeAction)

        self.volSlider = Slider()
        self.volSlider.setOrientation(Qt.Horizontal)
        self.volSlider.setMinimum(0)
        self.volSlider.setMaximum(100)
        self.volSlider.setFixedWidth(120)
        self.volSlider.setValue(self.player.volume())
        self.volSlider.setToolTip(str(self.volSlider.value()))
        self.volSlider.pointClicked.connect(self.setVolume)
        toolBar.addWidget(self.volSlider)

        self.videoPositionEdit = LineEdit('00:00')
        self.videoPositionEdit.setAlignment(Qt.AlignRight)
        self.videoPositionEdit.setFixedWidth(75)
        self.videoPositionEdit.setFont(QFont('Timers', 14))
        self.videoPositionEdit.clicked.connect(self.mediaPauseOnly)
        self.videoPositionEdit.editingFinished.connect(self.mediaPlayOnly)
        self.videoPositionLabel = QLabel(' / 00:00  ')
        self.videoPositionLabel.setFont(QFont('Timers', 14))
        toolBar.addWidget(QLabel('    '))
        toolBar.addWidget(self.videoPositionEdit)
        toolBar.addWidget(self.videoPositionLabel)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.videoSlider = Slider()
        self.videoSlider.setEnabled(False)
        self.videoSlider.setOrientation(Qt.Horizontal)
        self.videoSlider.setMinimum(0)
        self.videoSlider.setMaximum(1000)
        self.videoSlider.setFixedWidth(1000)
        self.videoSlider.sliderMoved.connect(self.timeStop)
        self.videoSlider.sliderReleased.connect(self.timeStart)
        self.videoSlider.pointClicked.connect(self.videoSliderClick)
        toolBar.addWidget(self.videoSlider)

        toolBar.addWidget(QLabel('   '))
        self.globalIntervalComBox = QComboBox()
        self.globalIntervalComBox.addItems(['间隔 100ms', '间隔 200ms', '间隔 500ms', '间隔 1s'])
        self.globalIntervalComBox.setCurrentIndex(1)
        self.globalIntervalComBox.currentIndexChanged.connect(self.setGlobalInterval)
        toolBar.addWidget(self.globalIntervalComBox)
        toolBar.addWidget(QLabel('  '))
        self.subEditComBox = QComboBox()
        self.refreshComboBox()
        toolBar.addWidget(self.subEditComBox)
        toolBar.addWidget(QLabel('  '))
        moveForward = QPushButton('- 1')
        moveForward.setFixedWidth(50)
        toolBar.addWidget(moveForward)
        toolBar.addWidget(QLabel('  '))
        moveAfterward = QPushButton('+ 1')
        moveAfterward.setFixedWidth(50)
        toolBar.addWidget(moveAfterward)
        toolBar.addWidget(QLabel('  '))
        clearSub = QPushButton('清空')
        clearSub.setFixedWidth(50)
        toolBar.addWidget(clearSub)
        toolBar.addWidget(QLabel('  '))
        outputSub = QPushButton('裁剪')
        outputSub.setFixedWidth(50)
        toolBar.addWidget(outputSub)
        moveForward.clicked.connect(self.moveForward)
        moveAfterward.clicked.connect(self.moveAfterward)
        clearSub.clicked.connect(self.clearSub)
        outputSub.clicked.connect(self.exportSubWindow)

    def setGlobalInterval(self, index):
        if not self.playStatus:
            self.mediaPlay()
        self.globalInterval = {0: 100, 1: 200, 2: 500, 3: 1000}[index]
        self.initSubtitle()
        self.initProcess.show()
        self.subtitle.cellChanged.disconnect(self.subEdit)
        for index, subData in self.subtitleDict.items():
            for start, rowData in subData.items():
                startRow = start // self.globalInterval
                deltaRow = rowData[0] // self.globalInterval
                if deltaRow:
                    endRow = startRow + deltaRow
                    for row in range(startRow, endRow):
                        self.subtitle.setItem(row, index, QTableWidgetItem(rowData[1]))
                        if row >= 0:
                            self.subtitle.item(row, index).setBackground(QBrush(QColor('#35545d')))
                    self.subtitle.setSpan(startRow, index, endRow - startRow, 1)
        self.subtitle.cellChanged.connect(self.subEdit)
        self.initProcess.hide()

    def moveForward(self):
        self.initProcess.show()
        self.subtitle.cellChanged.disconnect(self.subEdit)
        index = self.subEditComBox.currentIndex()
        for y in range(self.subtitle.rowCount()):
            self.subtitle.setSpan(y, index, 1, 1)
            self.subtitle.setItem(y, index, QTableWidgetItem(''))
            self.subtitle.item(y, index).setBackground(QBrush(QColor('#232629')))
        tmpDict = self.subtitleDict[index]
        self.subtitleDict[index] = {}
        for start, rowData in tmpDict.items():
            self.subtitleDict[index][start - self.globalInterval] = rowData
        for start, rowData in self.subtitleDict[index].items():
            startRow = start // self.globalInterval
            endRow = startRow + rowData[0] // self.globalInterval
            for row in range(startRow, endRow):
                self.subtitle.setItem(row, index, QTableWidgetItem(rowData[1]))
                self.subtitle.item(row, index).setBackground(QBrush(QColor('#35545d')))
            self.subtitle.setSpan(startRow, index, endRow - startRow, 1)
        self.subtitle.cellChanged.connect(self.subEdit)
        self.initProcess.hide()

    def moveAfterward(self):
        self.initProcess.show()
        self.subtitle.cellChanged.disconnect(self.subEdit)
        index = self.subEditComBox.currentIndex()
        for y in range(self.subtitle.rowCount()):
            self.subtitle.setSpan(y, index, 1, 1)
            self.subtitle.setItem(y, index, QTableWidgetItem(''))
            self.subtitle.item(y, index).setBackground(QBrush(QColor('#232629')))
        tmpDict = self.subtitleDict[index]
        self.subtitleDict[index] = {}
        for start, rowData in tmpDict.items():
            self.subtitleDict[index][start + self.globalInterval] = rowData
        for start, rowData in self.subtitleDict[index].items():
            startRow = start // self.globalInterval
            endRow = startRow + rowData[0] // self.globalInterval
            for row in range(startRow, endRow):
                self.subtitle.setItem(row, index, QTableWidgetItem(rowData[1]))
                self.subtitle.item(row, index).setBackground(QBrush(QColor('#35545d')))
            self.subtitle.setSpan(startRow, index, endRow - startRow, 1)
        self.subtitle.cellChanged.connect(self.subEdit)
        self.initProcess.hide()

    def clearSub(self):
        index = self.subEditComBox.currentIndex()
        reply = QMessageBox.information(self, '清空字幕', '清空第 %s 列字幕条？' % (index + 1), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.initProcess.show()
            self.subtitle.cellChanged.disconnect(self.subEdit)
            self.subtitleDict[index] = {0: [self.globalInterval, '']}
            for i in range(self.subtitle.rowCount()):
                self.subtitle.setSpan(i, index, 1, 1)
                self.subtitle.setItem(i, index, QTableWidgetItem(''))
                self.subtitle.item(i, index).setBackground(QBrush(QColor('#232629')))
                self.subtitle.setHorizontalHeaderItem(index, QTableWidgetItem('%s' % (index + 1)))
            self.subtitle.cellChanged.connect(self.subEdit)
            self.initProcess.hide()

    def exportSubWindow(self, start=0, end=0, index=None):
        self.releaseKeyboard()
        self.exportWindow.hide()
        self.exportWindow.show()
        start = '00:00.0' if not start else self.splitTime(start)
        end = self.splitTime(self.duration) if not end else self.splitTime(end)
        if not index:
            index = self.subEditComBox.currentIndex() + 1
        self.exportWindow.setDefault(start, end, index)

    def exportSubtitle(self, exportArgs):
        start = calSubTime2(exportArgs[0])
        end = calSubTime2(exportArgs[1])
        subStart = calSubTime2(exportArgs[2])
        index = exportArgs[3] - 1
        subData = self.subtitleDict[index]
        rowList = sorted(subData.keys())
        exportRange = []
        for t in rowList:
            if t >= start and t <= end:
                exportRange.append(t)
        subNumber = 1
        with open(exportArgs[-1], 'w', encoding='utf-8') as exportFile:
            for t in exportRange:
                text = subData[t][1]
                if text:
                    start = ms2Time(t + subStart)
                    end = ms2Time(t + subStart + subData[t][0])
                    exportFile.write('%s\n%s --> %s\n%s\n\n' % (subNumber, start, end, text))
                    subNumber += 1
        QMessageBox.information(self, '导出字幕', '导出完成', QMessageBox.Yes)
        self.exportWindow.hide()

    def refreshComboBox(self):
        self.subEditComBox.clear()
        for i in range(self.subtitle.columnCount()):
            self.subEditComBox.addItem('字幕 ' + str(i + 1))

    def open(self):
        self.videoPath = QFileDialog.getOpenFileName(self, "请选择视频文件", None, "视频文件 (*.mp4 *.mkv);;所有文件(*.*)")[0]
        if self.videoPath:
            cmd = ['ffmpeg.exe', '-i', self.videoPath]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            for l in p.stdout.readlines():
                l = l.decode('utf8')
                if 'Duration' in l:
                    self.duration = calSubTime(l.split(' ')[3][:-1])
                if 'Stream' in l and 'DAR' in l:
                    self.videoWidth, self.videoHeight = map(int, l.split(' [')[0].split(' ')[-1].split('x'))
                    break
            self.initProcess.show()
            self.subtitle.cellChanged.disconnect(self.subEdit)
            self.subtitle.setRowCount(self.duration // self.globalInterval + 1)
            self.subtitle.setVerticalHeaderLabels([cnt2Time2(i, self.globalInterval) for i in range(self.subtitle.rowCount())])
            self.subtitle.cellChanged.connect(self.subEdit)
            self.initProcess.hide()
            url = QUrl.fromLocalFile(self.videoPath)
            self.stack.setCurrentIndex(1)
            self.playerWidget.setSize(QSizeF(1280, 720))
            self.player.setMedia(url)
            self.playStatus = True
            self.videoSlider.setEnabled(True)
            self.mediaPlay()
            self.timer.start()
            self.timer.timeout.connect(self.timeOut)
            self.subTimer.start()
            self.subTimer.timeout.connect(self.subTimeOut)

    def popDnld(self):
        self.releaseKeyboard()
        self.dnldWindow.hide()
        self.dnldWindow.show()

    def popPreview(self):
        self.releaseKeyboard()
        self.previewSubtitle.hide()
        self.previewSubtitle.show()

    def decode(self):
        self.releaseKeyboard()
        self.videoDecoder.setVideoArgs(self.videoPath, self.videoWidth, self.videoHeight, self.subtitleDict)
        self.videoDecoder.hide()
        self.videoDecoder.show()

    def mediaPlay(self):
        if self.playStatus:
            self.player.play()
            self.grabKeyboard()
            self.timeStart()
            self.playStatus = False
            self.playAction.setIcon(self.pauseIcon)
            self.playAction.setText('暂停')
        else:
            self.player.pause()
            self.timeStop()
            self.playStatus = True
            self.playAction.setIcon(self.playIcon)
            self.playAction.setText('播放')

    def mediaPlayOnly(self):
        self.grabKeyboard()
        try:
            timeText = self.videoPositionEdit.text().split(':')
            m, s = timeText[:2]
            if not m:
                m = '00'
            if not s:
                s = '00'
            if len(m) > 3:
                m = m[:3]
            if len(s) > 2:
                s = s[:2]
            if m.isdigit():
                m = int(m)
            if s.isdigit():
                s = int(s)
            if s > 60:
                s = 60
            total_m = self.player.duration() // 60000
            if m > total_m:
                m = total_m
            self.player.setPosition(m * 60000 + s * 1000)
            self.videoSlider.setValue(self.player.position() * 1000 / self.player.duration())
        except:
            pass
        self.videoPositionEdit.setReadOnly(True)
        self.timeStart()

    def mediaPauseOnly(self):
        self.releaseKeyboard()
        self.videoPositionEdit.setReadOnly(False)
        self.player.pause()
        self.timeStop()
        self.playStatus = True
        self.playAction.setIcon(self.playIcon)
        self.playAction.setText('播放')

    def splitTime(self, playTime):
        playTime = playTime // 1000
        m = str(playTime // 60)
        s = playTime % 60
        s = ('0%s' % s)[-2:]
        if len(m) > 2:
            t = '%3s:%2s' % (m, s)
        else:
            t = '%2s:%2s' % (m, s)
        return t

    def timeOut(self):
        row = self.player.position() // self.globalInterval
        self.subtitle.selectRow(row)
        self.subtitle.verticalScrollBar().setValue(row - 10)
        if self.dnldWindow.isHidden() or self.exportWindow.isHidden() or self.videoDecoder.isHidden():
            self.grabKeyboard()
        try:
            self.videoSlider.setValue(self.player.position() * 1000 / self.player.duration())
            self.setTimeLabel()
        except:
            pass

    def timeStop(self):
        self.timer.stop()

    def timeStart(self):
        self.timer.start()

    def videoSliderClick(self, p):
        self.videoSlider.setValue(p.x())
        self.player.setPosition(p.x() * self.player.duration() // 1000)
        self.setTimeLabel()

    def setVolume(self, p):
        self.volumeValue = p.x()
        if self.volumeValue > 100:
            self.volumeValue = 100
        if self.volumeValue < 0:
            self.volumeValue = 0
        self.volSlider.setValue(self.volumeValue)
        self.player.setVolume(self.volumeValue)
        self.volSlider.setToolTip(str(self.volSlider.value()))
        if self.volumeValue:
            self.volumeStatus = True
            self.volumeAction.setIcon(self.volumeIcon)
        else:
            self.volumeStatus = False
            self.volumeAction.setIcon(self.volumeMuteIcon)

    def volumeMute(self):
        if self.volumeStatus:
            self.volumeStatus = False
            self.old_volumeValue = self.player.volume()
            self.player.setVolume(0)
            self.volSlider.setValue(0)
            self.volumeAction.setIcon(self.volumeMuteIcon)
        else:
            self.volumeStatus = True
            self.player.setVolume(self.old_volumeValue)
            self.volSlider.setValue(self.old_volumeValue)
            self.volumeAction.setIcon(self.volumeIcon)

    def setTimeLabel(self):
        now = self.player.position()
        total = self.player.duration()
        now = self.splitTime(now)
        total = self.splitTime(total)
        self.videoPositionEdit.setText(now)
        self.videoPositionLabel.setText(' / %s  ' % total)

    def eventFilter(self, obj, event):
        if obj == self.view:
            if event.type() == QEvent.MouseButtonPress:
                self.mediaPlay()
        return QMainWindow.eventFilter(self, obj, event)

    def keyPressEvent(self, QKeyEvent):
        key = QKeyEvent.key()
        if key == Qt.Key_Left:
            if self.videoSlider.isEnabled():
                self.player.setPosition(self.player.position() - 5000)
                self.videoSlider.setValue(self.player.position() * 1000 / self.player.duration())
                self.setTimeLabel()
        elif key == Qt.Key_Right:
            if self.videoSlider.isEnabled():
                self.player.setPosition(self.player.position() + 5000)
                self.videoSlider.setValue(self.player.position() * 1000 / self.player.duration())
                self.setTimeLabel()
        elif key == Qt.Key_Up:
            self.volumeValue += 10
            if self.volumeValue > 100:
                self.volumeValue = 100
            self.volSlider.setValue(self.volumeValue)
            self.player.setVolume(self.volumeValue)
        elif key == Qt.Key_Down:
            self.volumeValue -= 10
            if self.volumeValue < 0:
                self.volumeValue = 0
            self.volSlider.setValue(self.volumeValue)
            self.player.setVolume(self.volumeValue)
        elif key == Qt.Key_Space:
            self.mediaPlay()
