#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess, copy
from PySide2.QtWidgets import QWidget, QMainWindow, QGridLayout, QFileDialog, QToolBar,\
        QAction, QDialog, QStyle, QSlider, QLabel, QPushButton, QStackedWidget, QHBoxLayout,\
        QLineEdit, QTableWidget, QAbstractItemView, QTableWidgetItem, QGraphicsTextItem, QMenu,\
        QGraphicsScene, QGraphicsView, QGraphicsDropShadowEffect, QComboBox, QMessageBox, QColorDialog
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtMultimediaWidgets import QGraphicsVideoItem
from PySide2.QtGui import QIcon, QKeySequence, QFont, QColor
from PySide2.QtCore import Qt, QTimer, QEvent, QPoint, Signal, QSizeF, QUrl
from utils.youtube_downloader import YoutubeDnld
from utils.subtitle import exportSubtitle
from utils.videoDecoder import VideoDecoder
from utils.separate_audio import sepMainAudio, Separate
from utils.assSelect import assSelect
from utils.graph import graph


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


def calSubTime2(t):
    '''
    receive str
    return int
    m:s.ms -> ms in total
    '''
    t.replace(',', '.').replace('：', ':')
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
    count of interval times -> m:s.ms
    '''
    m, s = divmod(cnt * interval, 60000)
    s, ms = divmod(s, 1000)
    return ('%s:%02d.%03d' % (m, s, ms))[:-1]


def ms2Time(ms):
    '''
    receive int
    return str
    ms -> m:s.ms
    '''
    m, s = divmod(ms, 60000)
    s, ms = divmod(s, 1000)
    return ('%s:%02d.%03d' % (m, s, ms))[:-1]


def ms2SRTTime(ms):
    '''
    receive int
    return str
    ms -> h:m:s,ms
    '''
    h, m = divmod(ms, 3600000)
    m, s = divmod(m, 60000)
    s, ms = divmod(s, 1000)
    return '%s:%02d:%02d,%03d' % (h, m, s, ms)


def splitTime(position):
    '''
    ms -> m:s
    '''
    position = position // 1000
    m, s = divmod(position, 60)
    return '%02d:%02d' % (m, s)


class Slider(QSlider):
    pointClicked = Signal(QPoint)

    def mousePressEvent(self, event):
        self.pointClicked.emit(event.pos())

    def mouseMoveEvent(self, event):
        self.pointClicked.emit(event.pos())

    def wheelEvent(self, event):  # 把进度条的滚轮事件去了 用啥子滚轮
        pass


class LineEdit(QLineEdit):
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()


class Label(QLabel):
    clicked = Signal()

    def mouseReleaseEvent(self, QMouseEvent):
        self.clicked.emit()


class GraphicsVideoItem(QGraphicsVideoItem):
    wheel = Signal(int)

    def wheelEvent(self, QEvent):
        self.wheel.emit(QEvent.delta())


class PreviewSubtitle(QDialog):  # 设置字幕预览效果的窗口
    fontColor = '#ffffff'
    fontSize = 60
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
        self.fontSizeBox.setCurrentIndex(3)
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
        self.boldCheckBox = QPushButton('粗体')
        self.boldCheckBox.setStyleSheet('background-color:#3daee9')
        self.boldCheckBox.clicked.connect(self.boldChange)
        layout.addWidget(self.boldCheckBox, 1, 0, 1, 1)
        self.italicCheckBox = QPushButton('斜体')
        self.italicCheckBox.clicked.connect(self.italicChange)
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
        self.bold = not self.bold
        if self.bold:
            self.boldCheckBox.setStyleSheet('background-color:#3daee9')
        else:
            self.boldCheckBox.setStyleSheet('background-color:#31363b')

    def italicChange(self):
        self.italic = not self.italic
        if self.italic:
            self.italicCheckBox.setStyleSheet('background-color:#3daee9')
        else:
            self.italicCheckBox.setStyleSheet('background-color:#31363b')

    def getShadow(self, index):
        self.shadowOffset = index


class MainWindow(QMainWindow):  # Main window
    def __init__(self):
        super().__init__()
        self.subtitle = QTableWidget()  # 重载表格滚轮事件 需提前到渲染UI界面之前才不会报错
        self.subtitle.verticalScrollBar().installEventFilter(self)
        self.oldScrollBarValue = 0

        self.setWindowTitle = 'DD烤肉机'
        self.mainWidget = QWidget()
        self.mainLayout = QGridLayout()  # Grid layout
        self.mainLayout.setSpacing(10)
        self.mainWidget.setLayout(self.mainLayout)
        self.duration = 60000
        self.position = 0
        self.playRange = [0, self.duration]
        self.replay = False
        self.bitrate = 2000
        self.fps = 60
        self.tablePreset = ['#AI自动识别', True]
        self.refreshMainAudioToken = False

        self.assSelect = assSelect()
        self.assSelect.assSummary.connect(self.addASSSub)
        self.previewSubtitle = PreviewSubtitle()
        self.separate = Separate()
        self.separate.voiceList.connect(self.setAutoSubtitle)
        self.separate.voiceWave.connect(self.addVoiceWave)  # AI分离出来的人声波形
        self.separate.tablePreset.connect(self.setTablePreset)
        self.dnldWindow = YoutubeDnld()
        self.exportWindow = exportSubtitle()
        self.videoDecoder = VideoDecoder()
        self.exportWindow.exportArgs.connect(self.exportSubtitle)
        self.stack = QStackedWidget()
        self.mainLayout.addWidget(self.stack, 0, 0, 8, 4)
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
        self.videoWindowSizePreset = {0: (640, 480), 1: (800, 600), 2: (1280, 720), 3: (1366, 768),
                                      4: (1600, 900), 5: (1920, 1080), 6: (2560, 1600)}
        self.videoWindowSizeIndex = 2
        self.sepMain = sepMainAudio(self.videoPath, self.duration)  # 创建切片主音频线程对象
        self.setPlayer()
        self.setGraph()
        self.graphTimer = QTimer()  # 刷新音频图的timer
        self.graphTimer.setInterval(20)
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
        self.playerWidget = GraphicsVideoItem()
        self.playerWidget.wheel.connect(self.changeVideoWindowSize)
        w, h = self.videoWindowSizePreset[self.videoWindowSizeIndex]
        self.playerWidget.setSize(QSizeF(w, h))
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.scene.addItem(self.playerWidget)
        self.stack.addWidget(self.view)
        self.player = QMediaPlayer(self, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.playerWidget)
        self.view.installEventFilter(self)
        self.view.show()
        self.srtTextItemDict = {0: QGraphicsTextItem(), 1: QGraphicsTextItem(), 2: QGraphicsTextItem(),
                                3: QGraphicsTextItem(), 4: QGraphicsTextItem()}
        for _, srtTextItem in self.srtTextItemDict.items():
            self.scene.addItem(srtTextItem)
        self.tipText = QGraphicsTextItem()
        self.scene.addItem(self.tipText)
        w = self.width()
        h = self.height()
        self.view.setFixedSize(w, h)
        self.scene.setSceneRect(5, 5, w - 10, h - 10)
        self.playerWidget.setSize(QSizeF(w, h))

    def changeVideoWindowSize(self, delta):
        if delta < 0:
            self.videoWindowSizeIndex -= 1
            if self.videoWindowSizeIndex < 0:
                self.videoWindowSizeIndex = 0
        else:
            self.videoWindowSizeIndex += 1
            if self.videoWindowSizeIndex > 6:
                self.videoWindowSizeIndex = 6
        w, h = self.videoWindowSizePreset[self.videoWindowSizeIndex]
        if w > self.width() * 0.6:
            w = self.width() * 0.6
        if h > self.height() * 0.6:
            h = self.height() * 0.6
        self.stack.setFixedSize(w, h)
        self.view.setFixedSize(w, h)
        self.scene.setSceneRect(5, 5, w - 10, h - 10)
        self.playerWidget.setSize(QSizeF(w, h))

    def setGraph(self):  # 绘制音频图
        self.mainAudio = graph()
        self.mainAudio.setMaximumHeight(self.height() / 3)
        self.mainLayout.addWidget(self.mainAudio, 8, 0, 1, 4)
        self.voiceAudio = graph()
        self.voiceAudio.setMaximumHeight(self.height() / 3)
        self.mainLayout.addWidget(self.voiceAudio, 9, 0, 1, 4)

    def setSubtitle(self):
        self.subtitleDict = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}}  # 初始字幕字典
        self.subTimer = QTimer()
        self.subTimer.setInterval(100)
        self.subtitle.setAutoScroll(False)
        self.subtitle.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mainLayout.addWidget(self.subtitle, 0, 4, 10, 16)
        self.subtitle.setColumnCount(5)
        self.subtitle.setRowCount(101)
        for index in range(5):
            self.subtitle.setColumnWidth(index, 130)
        self.refreshTable()
        self.row = 0
        self.subtitle.selectRow(self.row)
        self.subtitle.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.subtitle.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.subtitle.horizontalHeader().sectionClicked.connect(self.addSubtitle)
        self.subtitle.doubleClicked.connect(self.startEdit)  # 双击单元格开始编辑
        self.subtitle.verticalHeader().sectionClicked.connect(self.subHeaderClick)
        self.subtitle.setContextMenuPolicy(Qt.CustomContextMenu)
        self.subtitle.customContextMenuRequested.connect(self.popTableMenu)

    def refreshTable(self, position=0, select=0, scroll=0):  # 实时刷新表格
        self.subtitle.clearSpans()
        self.subtitle.clear()
        if not position:
            self.position = self.player.position()
        else:
            self.position = position
        self.row = self.position // self.globalInterval  # 当前进度行号
        self.subtitle.selectRow(select)  # 永远选在第一行
        self.subtitle.verticalScrollBar().setValue(scroll)  # 滚动条选在第一行
        self.subtitle.setVerticalHeaderLabels([cnt2Time(i, self.globalInterval) for i in range(self.row, self.row + 101)])  # 刷新行号
        subtitleViewUp = self.position  # 表格视窗开始时间（ms）
        subtitleViewDown = self.position + 100 * self.globalInterval  # 表格视窗结束时间（ms）
        for x, subData in self.subtitleDict.items():  # 只刷新进度 +100行范围内的字幕
            for start in sorted(subData):  # 字幕字典格式 {开始时间（ms）：[持续时间（ms），字幕]}
                delta, text = subData[start]
                if delta and text:  # 间隔和字幕均有值
                    if start >= subtitleViewDown:  # 超出表格视窗则跳出
                        break
                    elif start + delta >= subtitleViewUp:  # 计算字幕条位于表格视窗的位置
                        startRow = start // self.globalInterval - self.row  # 起始行
                        endRow = startRow + delta // self.globalInterval  # 结束行
                        if startRow < 0:  # 防止超出表格视窗
                            startRow = 0
                        if endRow > 101:
                            endRow = 101
                        if endRow > startRow:  # 小于一行的跳过
                            for y in range(startRow, endRow):
                                self.subtitle.setItem(y, x, QTableWidgetItem(text))
                            self.subtitle.item(startRow, x).setBackground(QColor('#35545d'))
                            self.subtitle.setSpan(startRow, x, endRow - startRow, 1)  # 跨行合并
                            self.subtitle.item(startRow, x).setTextAlignment(Qt.AlignTop)  # 字幕居上

    def addSubtitle(self, index):
        subtitlePath = QFileDialog.getOpenFileName(self, "请选择字幕", None, "字幕文件 (*.srt *.vtt *.ass)")[0]
        if subtitlePath:
            subData = {}
            if subtitlePath.endswith('.ass'):
                self.assSelect.setDefault(subtitlePath, index)
                self.assSelect.hide()
                self.assSelect.show()
            else:
                with open(subtitlePath, 'r', encoding='utf-8') as f:
                    f = f.readlines()
                subText = ''
                YoutubeAutoSub = False
                for l in f:
                    if '<c>' in l:
                        YoutubeAutoSub = True
                        break
                for cnt, l in enumerate(f):
                    if '<c>' in l:  # 油管vtt字幕格式——逐字识别字幕
                        lineData = l.split('c>')
                        if len(lineData) > 3:
                            subText, start, _ = lineData[0].split('<')
                            start = calSubTime(start[:-1]) // 20 * 20
                            if start not in self.subtitleDict[index]:
                                end = calSubTime(lineData[-3][1:-2]) // 20 * 20
                                for i in range(len(lineData) // 2):
                                    subText += lineData[i * 2 + 1][:-2]
                                subData[start] = [end - start, subText]
                        else:  # 油管自动识别出来的那种超短单行字幕
                            subText, start, _ = lineData[0].split('<')
                            start = calSubTime(start[:-1]) // 20 * 20
                            if start not in self.subtitleDict[index]:
                                subText += lineData[1][:-2]
                                subData[start] = [self.globalInterval, subText]
                    elif '-->' in l and f[cnt + 2].strip() and '<c>' not in f[cnt + 2]:  # 油管vtt字幕——单行类srt格式字幕
                        subText = f[cnt + 2][:-1]
                        start, end = l.strip().replace(' ', '').split('-->')
                        start = calSubTime(start) // 20 * 20
                        if start not in self.subtitleDict[index]:
                            if 'al' in end:  # align
                                end = end.split('al')[0]
                            end = calSubTime(end) // 20 * 20
                            subData[start] = [end - start, subText]
                    if '-->' in l and f[cnt + 1].strip() and not YoutubeAutoSub:  # srt字幕格式
                        start, end = l.strip().replace(' ', '').split('-->')
                        start = calSubTime(start) // 20 * 20
                        if start not in self.subtitleDict[index]:
                            end = calSubTime(end) // 20 * 20
                            delta = end - start
                            if delta > 10:
                                if '<b>' in f[cnt + 1]:  # 有的字幕里带<b> 好像是通过ffmpeg把ass转srt出来的
                                    subData[start] = [delta, f[cnt + 1].split('<b>')[1].split('<')[0]]
                                else:
                                    subData[start] = [delta, f[cnt + 1][:-1]]
                self.subtitleDict[index].update(subData)
                self.refreshTable()

    def addASSSub(self, assSummary):  # 解析返回的ass字幕
        index = assSummary[0]
        assDict = assSummary[1]
        self.videoDecoder.setSubDictStyle(assSummary)
        subData = assDict['Events']
        self.subtitleDict[index].update(subData)  # 更新读取ass的对话字典
        self.refreshTable()

    def subTimeOut(self):  # 刷新预览字幕
        fontColor = self.previewSubtitle.fontColor  # 预览字幕样式
        fontSize = (self.previewSubtitle.fontSize + 5) / 2.5
        fontBold = self.previewSubtitle.bold
        fontItalic = self.previewSubtitle.italic
        fontShadowOffset = self.previewSubtitle.shadowOffset
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(fontSize)
        font.setBold(fontBold)
        font.setItalic(fontItalic)
        for _, srtTextItem in self.srtTextItemDict.items():
            srtTextItem.setDefaultTextColor(fontColor)
            srtTextItem.setFont(font)
            srtTextShadow = QGraphicsDropShadowEffect()  # 设置阴影
            srtTextShadow.setOffset(fontShadowOffset)
            srtTextItem.setGraphicsEffect(srtTextShadow)
        self.tipText.setDefaultTextColor(fontColor)
        self.tipText.setFont(font)
        self.tipText.setGraphicsEffect(srtTextShadow)
        try:
            selected = self.subtitle.selectionModel().selection().indexes()
            for x, i in enumerate(selected):  # 刷新各列字幕
                if self.subtitle.item(i.row(), x):
                    txt = self.subtitle.item(i.row(), x).text()
                    if txt:
                        self.srtTextItemDict[x].setPlainText('#%s：' % (x + 1) + txt)
                        txtSize = self.srtTextItemDict[x].boundingRect().size()
                        posY = self.playerWidget.size().height() - txtSize.height() * (x + 1)  # 调整位置
                        posX = (self.playerWidget.size().width() - txtSize.width()) / 2
                        self.srtTextItemDict[x].setPos(posX, posY)
                    else:
                        self.srtTextItemDict[x].setPlainText('')
                else:
                    self.srtTextItemDict[x].setPlainText('')
            if self.replay:  # 循环播放提示
                self.tipText.setPlainText('循环播放: %s —— %s' % tuple(map(ms2Time, self.playRange)))
            else:
                self.tipText.setPlainText('')
        except:
            pass

    def subHeaderClick(self, row):  # 点击行号跳转
        if self.player.duration():
            position = row * self.globalInterval + self.position  # 进度为 点击行号x间隔 +全局进度 
            self.player.setPosition(position)
            self.videoSlider.setValue(position * 1000 // self.player.duration())
            self.setTimeLabel(position)

    def startEdit(self):
        self.releaseKeyboard()
        try:
            self.subtitle.cellChanged.disconnect(self.subEdit)  # 在连接cellchanged信号前先尝试断开
        except:
            pass
        self.subtitle.cellChanged.connect(self.subEdit)

    def subEdit(self, row, col):
        self.subtitle.cellChanged.disconnect(self.subEdit)
        repeat = self.subtitle.rowSpan(row, col)  # 获取合并格数
        text = self.subtitle.item(row, col).text()
        self.setSubtitleDict(row, col, repeat, text)  # 更新字典
        for y in range(repeat):
            self.subtitle.setItem(row + y, col, QTableWidgetItem(text))  # 更新表格
            self.subtitle.item(row + y, col).setTextAlignment(Qt.AlignTop)  # 字幕居上
        if text:
            self.subtitle.item(row, col).setBackground(QColor('#35545d'))
        else:
            self.subtitle.item(row, col).setBackground(QColor('#232629'))
        self.grabKeyboard()

    def setSubtitleDict(self, row, col, repeat, text):
        newSRow = row + self.row  # 编辑起始位置（行数）
        newERow = newSRow + repeat  # 编辑结束位置（行数）
        keyList = copy.deepcopy(list(self.subtitleDict[col].keys()))
        for oldS in keyList:
            oldSRow = oldS // self.globalInterval
            oldERow = oldSRow + self.subtitleDict[col][oldS][0] // self.globalInterval  # 字典里的结束位置
            if (newSRow < oldSRow and newERow > oldSRow) or (newSRow < oldSRow and newERow > oldERow)\
            or (newSRow < oldERow and newERow > oldERow) or (newSRow >= oldSRow and newERow <= oldERow):  # 防止覆盖字典
                del self.subtitleDict[col][oldS]  # 删除
        if text:
            self.subtitleDict[col][newSRow * self.globalInterval] = [repeat * self.globalInterval, text]  # 更新字典

    def popTableMenu(self, pos):  # 右键菜单
        pos = QPoint(pos.x() + 55, pos.y() + 30)
        menu = QMenu()
        setSpan = menu.addAction('合并')
        clrSpan = menu.addAction('拆分')
        copy = menu.addAction('复制')
        paste = menu.addAction('粘贴')
        delete = menu.addAction('删除')
        addSub = menu.addAction('导入')
        cutSub = menu.addAction('裁剪')
        replay = menu.addAction('循环播放')
        cancelReplay = menu.addAction('取消循环')
        action = menu.exec_(self.subtitle.mapToGlobal(pos))
        selected = self.subtitle.selectionModel().selection().indexes()
        xList = []  # 选中行
        for i in range(len(selected)):
            x = selected[i].column()
            if x not in xList:  # 剔除重复选择
                xList.append(x)
        if len(selected) == 1:  # 特殊情况 当刚合并完后选择该单个单元格 选中的只有第一个格子 需要修正一下
            x = xList[0]
            y = selected[0].row()
            yList = [y, y + self.subtitle.rowSpan(y, x) - 1]
        else:
            yList = [selected[0].row(), selected[-1].row()]
        if action == copy:  # 复制
            for x in xList:
                self.clipBoard = []
                for y in range(yList[0], yList[1] + 1):
                    if self.subtitle.item(y, x):
                        self.clipBoard.append(self.subtitle.item(y, x).text())
                    else:
                        self.clipBoard.append('')
                break  # 只复制选中的第一列
        elif action == paste:  # 粘贴
            for x in xList:
                for cnt, text in enumerate(self.clipBoard):
                    y  = yList[0] + cnt
                    self.subtitle.setSpan(y, x, 1, 1)
                    self.subtitle.setItem(y, x, QTableWidgetItem(text))
                    self.setSubtitleDict(y, x, 1, text)  # 更新表格
                    if text:
                        self.subtitle.item(y, x).setBackground(QColor('#35545d'))  # 有内容颜色
                    else:
                        self.subtitle.item(y, x).setBackground(QColor('#232629'))  # 没内容颜色
        elif action == delete:  # 删除选中
            for x in xList:
                for y in range(yList[0], yList[1] + 1):
                    if self.subtitle.item(y, x):
                        self.subtitle.setSpan(y, x, 1, 1)
                        if self.subtitle.item(y, x).text():
                            self.subtitle.setItem(y, x, QTableWidgetItem(''))
                            self.subtitle.item(y, x).setBackground(QColor('#232629'))  # 没内容颜色
                    self.setSubtitleDict(y, x, 1, '')  # 删除
        elif action == setSpan:  # 合并函数
            for x in xList:  # 循环所有选中的列
                firstItem = ''
                for y in range(yList[0], yList[1] + 1):  # 从选中行开始往下查询到第一个有效值后退出 一直没找到则为空
                    if self.subtitle.item(y, x):
                        if self.subtitle.item(y, x).text():
                            firstItem = self.subtitle.item(y, x).text()
                            break
                for y in range(yList[0], yList[1] + 1):
                    if self.subtitle.rowSpan(y, x) > 1:
                        self.subtitle.setSpan(y, x, 1, 1)  # 清除合并格子
                    self.subtitle.setItem(y, x, QTableWidgetItem(firstItem))  # 全部填上firstItem
                    self.subtitle.item(y, x).setTextAlignment(Qt.AlignTop)  # 字幕居上
                self.subtitle.setSpan(yList[0], x, yList[1] - yList[0] + 1, 1)  # 合并单元格
                self.subtitle.item(yList[0], x).setBackground(QColor('#35545d'))  # 第一个单元格填上颜色即可
                self.setSubtitleDict(yList[0], x, yList[1] - yList[0] + 1, firstItem)  # 更新表格
        elif action == clrSpan:  # 拆分
            for x in xList:
                for cnt, y in enumerate(range(yList[0], yList[1] + 1)):
                    repeat = self.subtitle.rowSpan(y, x)
                    if repeat > 1:  # 检测到合并单元格
                        self.subtitle.setSpan(y, x, 1, 1)
                        for repeatY in range(repeat):  # 循环单元格
                            newY = y + repeatY
                            if self.subtitle.item(newY, x):
                                text = self.subtitle.item(newY, x).text()
                                self.setSubtitleDict(newY, x, 1, text)
                                if text:
                                    self.subtitle.item(newY, x).setBackground(QColor('#35545d'))  # 有内容颜色
                                else:
                                    self.subtitle.item(newY, x).setBackground(QColor('#232629'))  # 没内容颜色
        elif action == addSub:  # 添加字幕
            for x in xList:
                self.addSubtitle(x)
                break  # 只添加选中的第一列
        elif action == cutSub:  # 裁剪字幕
            for x in xList:
                start = yList[0] * self.globalInterval
                end = yList[1] * self.globalInterval
                self.exportSubWindow(start, end, x + 1)
        elif action == replay:  # 循环播放
            self.replay = True
            self.playRange = [(yList[0] + self.row) * self.globalInterval, (yList[1] + self.row + 1) * self.globalInterval]

        elif action == cancelReplay:  # 取消循环
            self.replay = False
            self.playRange = [0, self.duration]

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
        separateAction = QAction(QIcon.fromTheme('document-open'), '&AI自动打轴', self, triggered=self.popSeparate)
        playMenu.addAction(separateAction)
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
        self.timer.setInterval(200)
        self.videoSlider = Slider()
        self.videoSlider.setEnabled(False)
        self.videoSlider.setOrientation(Qt.Horizontal)
        self.videoSlider.setFixedWidth(self.width())
        self.videoSlider.setMaximum(self.videoSlider.width())
        self.videoSlider.sliderMoved.connect(self.timeStop)
        self.videoSlider.sliderReleased.connect(self.timeStart)
        self.videoSlider.pointClicked.connect(self.videoSliderClick)
        toolBar.addWidget(self.videoSlider)

        toolBar.addWidget(QLabel('   '))
        self.globalIntervalComBox = QComboBox()
        self.globalIntervalComBox.addItems(['间隔 20ms', '间隔 50ms', '间隔 100ms', '间隔 200ms', '间隔 500ms', '间隔 1s'])
        self.globalIntervalComBox.setCurrentIndex(3)
        self.globalIntervalComBox.currentIndexChanged.connect(self.setGlobalInterval)
        toolBar.addWidget(self.globalIntervalComBox)
        toolBar.addWidget(QLabel('  '))
        self.subEditComBox = QComboBox()
        for i in range(self.subtitle.columnCount()):
            self.subEditComBox.addItem('字幕 ' + str(i + 1))
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
        self.globalInterval = {0: 20, 1: 50, 2: 100, 3: 200, 4: 500, 5: 1000}[index]
        self.timer.setInterval(self.globalInterval)
        self.subTimer.setInterval(self.globalInterval)
        self.refreshTable()

    def moveForward(self):
        index = self.subEditComBox.currentIndex()
        for y in range(self.subtitle.rowCount()):
            if self.subtitle.rowSpan(y, index) > 1:
                self.subtitle.setSpan(y, index, 1, 1)
            self.subtitle.setItem(y, index, QTableWidgetItem(''))
            self.subtitle.item(y, index).setBackground(QColor('#232629'))
        tmpDict = self.subtitleDict[index]
        self.subtitleDict[index] = {}
        for start, rowData in tmpDict.items():
            self.subtitleDict[index][start - self.globalInterval] = rowData
        for start, rowData in self.subtitleDict[index].items():
            startRow = start // self.globalInterval
            endRow = startRow + rowData[0] // self.globalInterval
            for row in range(startRow, endRow):
                self.subtitle.setItem(row, index, QTableWidgetItem(rowData[1]))
                try:
                    self.subtitle.item(row, index).setBackground(QColor('#35545d'))
                except:
                    pass
            if endRow - startRow > 1:
                self.subtitle.setSpan(startRow, index, endRow - startRow, 1)

    def moveAfterward(self):
        index = self.subEditComBox.currentIndex()
        for y in range(self.subtitle.rowCount()):
            if self.subtitle.rowSpan(y, index) > 1:
                self.subtitle.setSpan(y, index, 1, 1)
            self.subtitle.setItem(y, index, QTableWidgetItem(''))
            self.subtitle.item(y, index).setBackground(QColor('#232629'))
        tmpDict = self.subtitleDict[index]
        self.subtitleDict[index] = {}
        for start, rowData in tmpDict.items():
            self.subtitleDict[index][start + self.globalInterval] = rowData
        for start, rowData in self.subtitleDict[index].items():
            startRow = start // self.globalInterval
            endRow = startRow + rowData[0] // self.globalInterval
            for row in range(startRow, endRow):
                self.subtitle.setItem(row, index, QTableWidgetItem(rowData[1]))
                try:
                    self.subtitle.item(row, index).setBackground(QColor('#35545d'))
                except:
                    pass
            if endRow - startRow > 1:
                self.subtitle.setSpan(startRow, index, endRow - startRow, 1)

    def clearSub(self):
        row = self.subEditComBox.currentIndex()
        reply = QMessageBox.information(self, '清空字幕', '清空第 %s 列字幕条？' % (row + 1), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.subtitleDict[row] = {}
            self.refreshTable()

    def exportSubWindow(self, start=0, end=0, index=None):
        self.releaseKeyboard()
        self.exportWindow.hide()
        self.exportWindow.show()
        start = '00:00.0' if not start else splitTime(start)
        end = splitTime(self.duration) if not end else splitTime(end)
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
        if exportArgs[-1]:  # 有效路径
            with open(exportArgs[-1], 'w', encoding='utf-8') as exportFile:
                for t in exportRange:
                    text = subData[t][1]
                    if text:
                        start = ms2SRTTime(t + subStart)
                        end = ms2SRTTime(t + subStart + subData[t][0])
                        exportFile.write('%s\n%s --> %s\n%s\n\n' % (subNumber, start, end, text))
                        subNumber += 1
            QMessageBox.information(self, '导出字幕', '导出完成', QMessageBox.Yes)
            self.exportWindow.hide()

    def open(self):
        self.videoPath = QFileDialog.getOpenFileName(self, "请选择视频文件", None, "视频文件 (*.mp4 *.avi *.mov);;音频文件(*.mp3 *.wav *.aac);;所有文件(*.*)")[0]
        if self.videoPath:
            cmd = ['utils/ffmpeg.exe', '-i', self.videoPath]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            try:
                for l in p.stdout.readlines():
                    l = l.decode('utf8')
                    if 'Duration' in l:
                        self.duration = calSubTime(l.split(' ')[3][:-1])
                        self.bitrate = int(l.split(' ')[-2])
                    if 'Stream' in l and 'DAR' in l:
                        args = l.split(',')
                        resolution = args[2].replace(' ', '')
                        if '[' in resolution:
                            resolution = resolution.split('[')[0]
                        self.videoWidth, self.videoHeight = map(int, resolution.split('x'))
                        for arg in args:
                            if 'fps' in arg:
                                self.fps = float(arg.split('fps')[0])
                        break
            except:
                pass
            url = QUrl.fromLocalFile(self.videoPath)
            self.stack.setCurrentIndex(1)
            self.player.setMedia(url)
            self.playStatus = True
            self.videoSlider.setEnabled(True)
            self.playRange = [0, self.duration]  # 播放范围
            if self.sepMain.isRunning:  # 检测上一个视频的切片主音频进程是否还在进行
                self.sepMain.terminate()
                self.sepMain.quit()
                self.sepMain.wait()
            self.sepMain = sepMainAudio(self.videoPath, self.duration)  # 开始切片主音频
            self.sepMain.mainAudioWave.connect(self.addMainAudioWave)
            self.sepMain.start()
            self.refreshMainAudioToken = False  # 刷新主音频
            self.mainAudioWaveX = []
            self.mainAudioWaveY = []
            self.refreshVoiceToken = False  # 刷新AI识别人声音频
            self.voiceWaveX = []
            self.voiceWaveY = []
            self.mainAudio.plot([0], [0])
            self.voiceAudio.plot([0], [0])
            self.mediaPlay()
            self.timer.start()
            self.timer.timeout.connect(self.timeOut)
            self.subTimer.start()
            self.subTimer.timeout.connect(self.subTimeOut)
            self.graphTimer.start()  # 音频图timer启动
            self.graphTimer.timeout.connect(self.refreshGraph)

    def popDnld(self):
        self.releaseKeyboard()
        self.dnldWindow.hide()
        self.dnldWindow.show()

    def popPreview(self):
        self.releaseKeyboard()
        self.previewSubtitle.hide()
        self.previewSubtitle.show()

    def popSeparate(self):
        self.releaseKeyboard()
        self.separate.setDefault(self.videoPath, self.duration)
        self.separate.hide()
        self.separate.show()

    def addMainAudioWave(self, x, y):  # 添加主音频数据
        self.mainAudioWaveX = x
        self.mainAudioWaveY = y
        self.refreshMainAudioToken = True

    def addVoiceWave(self, x, y):  # 添加人声音轨
        self.voiceWaveX += x
        self.voiceWaveY += y
        self.refreshVoiceToken = True

    def refreshGraph(self):
        if self.refreshMainAudioToken:
            start = int((self.player.position() / self.duration) * len(self.mainAudioWaveX))
            end = start + self.globalInterval * 10  # 显示当前间隔x10的区域
            if end > len(self.mainAudioWaveX):
                end = len(self.mainAudioWaveX)
            xList = self.mainAudioWaveX[start:end]
            yList = self.mainAudioWaveY[start:end]
            self.mainAudio.plot(xList, yList)
        if self.refreshVoiceToken:
            start = int((self.player.position() / self.duration) * len(self.voiceWaveX))
            end = start + self.globalInterval * 10  # 显示当前间隔x10的区域
            if end > len(self.voiceWaveX):
                end = len(self.voiceWaveX)
            xList = self.voiceWaveX[start:end]
            yList = self.voiceWaveY[start:end]
            self.voiceAudio.plot(xList, yList, '#B0E2FF')

    def setTablePreset(self, preset):
        self.tablePreset = preset  # 填充字符 输出列

    def setAutoSubtitle(self, voiceList):  # AI自动打轴更新至字幕字典里
        for t in voiceList:
            start, delta = t
            txt, index = self.tablePreset
            self.subtitleDict[index][start] = [delta, txt]
        self.refreshTable()  # 刷新表格

    def decode(self):
        self.releaseKeyboard()
        self.videoDecoder.setDefault(self.videoPath, self.videoWidth, self.videoHeight, self.duration, self.bitrate, self.fps, self.subtitleDict)
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
            timeText = self.videoPositionEdit.text().replace('：', ':').split(':')
            m, s = timeText[:2]
            if not m:
                m = '00'
            if not s:
                s = '00'
            if len(m) > 3:
                m = m[:3]
            if len(s) > 2:
                s = s[:2]
            m = int(m)
            s = int(s)
            if s > 60:
                s = 60
            total_m = self.player.duration() // 60000
            if m > total_m:
                m = total_m
            self.player.setPosition(m * 60000 + s * 1000)
            self.videoSlider.setValue(self.player.position() * self.videoSlider.width() / self.player.duration())
        except:
            pass
        self.videoPositionEdit.setReadOnly(True)

    def mediaPauseOnly(self):
        self.releaseKeyboard()
        self.videoPositionEdit.setReadOnly(False)
        self.player.pause()
        self.timeStop()
        self.playStatus = True
        self.playAction.setIcon(self.playIcon)
        self.playAction.setText('播放')

    def timeOut(self):
        if self.player.position() <= self.playRange[0] or self.player.position() >= self.playRange[1]:  # 循环播放
            self.player.setPosition(self.playRange[0])
        self.refreshTable()
        if self.dnldWindow.isHidden() or self.exportWindow.isHidden() or self.videoDecoder.isHidden():
            self.grabKeyboard()
        try:
            self.videoSlider.setValue(self.player.position() * self.videoSlider.width() / self.player.duration())
            self.setTimeLabel()
        except:
            pass

    def timeStop(self):
        self.timer.stop()

    def timeStart(self):
        self.timer.start()

    def videoSliderClick(self, p):
        x = p.x()
        if x < 0:  # 限制
            x = 0
        if x > self.videoSlider.width():
            x = self.videoSlider.width()
        self.videoSlider.setValue(x)
        position = x * self.duration // self.videoSlider.width()
        self.player.setPosition(position)
        self.refreshTable(position)
        self.setTimeLabel(position)

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

    def setTimeLabel(self, pos=0):
        if not pos:
            now = splitTime(self.player.position())
        else:
            now = splitTime(pos)
        total = splitTime(self.player.duration())
        self.videoPositionEdit.setText(now)
        self.videoPositionLabel.setText(' / %s  ' % total)

    def eventFilter(self, obj, event):
        if obj == self.view:
            if event.type() == QEvent.MouseButtonPress:
                self.mediaPlay()
        if obj == self.subtitle.verticalScrollBar():  # 过滤表格滚轮事件 用于刷新超出表格视窗范围的滚动
            if event.type() == QEvent.Wheel:
                scrollBarValue = self.subtitle.verticalScrollBar().value()
                if scrollBarValue == self.oldScrollBarValue:
                    delta = event.delta() // 30  # 滚轮四倍速！！！（120 / 30）
                    if scrollBarValue > 0 and delta < 0:  # 向下滚动超出范围
                        self.position = self.player.position() - delta * self.globalInterval  # 前进3行 同时重置视频进度及刷新
                        if self.position > self.duration:
                            self.position = self.duration - self.globalInterval
                        self.player.setPosition(self.position)
                        self.videoSlider.setValue(self.position * self.videoSlider.width() / self.duration)
                        self.refreshTable(self.position, select=100, scroll=scrollBarValue)  # 向下滚的时候选择要特殊处理下
                        self.setTimeLabel(self.position)
                    elif scrollBarValue == 0 and delta > 0:  # 向上滚动超出范围
                        self.position = self.player.position() - delta * self.globalInterval  # 倒退3行 同时重置视频进度及刷新
                        if self.position < 0:
                            self.position = 0
                        self.player.setPosition(self.position)
                        self.videoSlider.setValue(self.position * self.videoSlider.width() / self.duration)
                        self.refreshTable(self.position)
                        self.setTimeLabel(self.position)
                self.oldScrollBarValue = scrollBarValue
        return QMainWindow.eventFilter(self, obj, event)

    def keyPressEvent(self, QKeyEvent):
        key = QKeyEvent.key()
        if key == Qt.Key_Left:
            if self.videoSlider.isEnabled():
                self.position = self.player.position() - self.globalInterval  # ←键倒退1行 同时重置视频进度及刷新
                if self.position < 0:
                    self.position = 0
                self.player.setPosition(self.position)
                self.videoSlider.setValue(self.position * self.videoSlider.width() / self.duration)
                self.refreshTable(self.position)
                self.setTimeLabel(self.position)
        elif key == Qt.Key_Right:
            if self.videoSlider.isEnabled():
                self.position = self.player.position() + self.globalInterval  # →键前进1行 同时重置视频进度及刷新
                if self.position > self.duration:
                    self.position = self.duration - self.globalInterval
                self.player.setPosition(self.position)
                self.videoSlider.setValue(self.position * self.videoSlider.width() / self.duration)
                self.refreshTable(self.position)
                self.setTimeLabel(self.position)
        elif key == Qt.Key_Up:  # ↑键增加音量
            self.volumeValue += 10
            if self.volumeValue > 100:
                self.volumeValue = 100
            self.volSlider.setValue(self.volumeValue)
            self.player.setVolume(self.volumeValue)
        elif key == Qt.Key_Down:  # ↓键减少音量
            self.volumeValue -= 10
            if self.volumeValue < 0:
                self.volumeValue = 0
            self.volSlider.setValue(self.volumeValue)
            self.player.setVolume(self.volumeValue)
        elif key == Qt.Key_Space:  # 空格暂停/播放 需要主界面处于grabkeyboard状态
            self.mediaPlay()
