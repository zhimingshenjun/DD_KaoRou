import os, time, copy, codecs, subprocess, psutil
from PySide2.QtWidgets import QGridLayout, QFileDialog, QDialog, QPushButton,\
        QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QProgressBar, QLabel,\
        QComboBox, QCheckBox, QWidget, QSlider, QFontDialog, QColorDialog, QTabWidget, QMessageBox
from PySide2.QtCore import Qt, QTimer, Signal, QThread, QPoint
from PySide2.QtGui import QFontInfo, QPixmap, QIntValidator


def ms2Time(ms):
    '''
    receive int
    return str
    ms -> h:m:s.ms
    '''
    h, m = divmod(ms, 3600000)
    m, s = divmod(m, 60000)
    s, ms = divmod(s, 1000)
    h = ('0%s' % h)[-2:]
    m = ('0%s' % m)[-2:]
    s = ('0%s' % s)[-2:]
    ms = ('%s0' % ms)[:2]
    return '%s:%s:%s.%s' % (h, m, s, ms)


def calSubTime(t):
    '''
    receive str
    return int
    h:m:s.ms -> s in total
    '''
    h = int(t[:2])
    m = int(t[3:5])
    s = int(t[6:8])
    return h * 3600 + m * 60 + s


class Slider(QSlider):
    pointClicked = Signal(QPoint)

    def mousePressEvent(self, event):
        self.pointClicked.emit(event.pos())

    def mouseMoveEvent(self, event):
        self.pointClicked.emit(event.pos())


class videoEncoder(QThread):
    processBar = Signal(int)
    currentPos = Signal(str)
    encodeResult = Signal(bool)

    def __init__(self, videoPath, cmd, parent=None):
        super(videoEncoder, self).__init__(parent)
        self.videoPath = videoPath
        self.cmd = cmd

    def run(self):
        self.p = subprocess.Popen(['utils/ffmpeg.exe', '-i', self.videoPath, '-map', '0:v:0', '-c', 'copy', '-f', 'null', '-'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.p.wait()
        frames = self.p.stdout.readlines()[-2].decode('gb18030').split('frame=')[-1].split(' ')
        for f in frames:
            if f:
                totalFrames = int(f)
                break
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        cnt = 0
        while self.p.poll() is None:
            console = self.p.stdout.read(1000).decode('gb18030', 'ignore')
            if 'frame=' in console:
                break
        while self.p.poll() is None:
            console = self.p.stdout.read(300).decode('gb18030', 'ignore')
            if '\r' in console:
                console = console.split('\r')[-2]
                if 'frame=' in console:
                    frameArgs = console.split('frame=')[-1].split(' ')
                    for frame in frameArgs:
                        if frame:
                            self.processBar.emit(int(frame) * 100 // totalFrames)
                            break
                cnt += 1
                if not cnt % 4:
                    if 'time=' in console:
                        videoPos = console.split('time=')[-1].split(' ')[0]
                        self.currentPos.emit(videoPos)
        if self.p.poll() == 1:
            self.encodeResult.emit(False)
        elif self.p.poll() == 0:
            self.encodeResult.emit(True)


class label(QLabel):
    clicked = Signal()

    def mouseReleaseEvent(self, QMouseEvent):
        self.clicked.emit()


class encodeOption(QWidget):
    def __init__(self):
        self.anime4KToken = False
        super().__init__()
        self.resize(600, 300)
        self.setWindowTitle('编码设置')
        layout = QGridLayout()
        self.setLayout(layout)
        resolution = QWidget()
        resolutionLayout = QGridLayout()
        resolution.setLayout(resolutionLayout)
        layout.addWidget(resolution, 0, 0, 1, 1)
        resolutionLayout.addWidget(QLabel('分辨率 '), 0, 0, 1, 1)
        self.exportVideoWidth = QLineEdit()
        self.exportVideoWidth.setMaximumWidth(100)
        self.exportVideoWidth.setAlignment(Qt.AlignCenter)
        self.exportVideoWidth.setValidator(QIntValidator(100, 10000))
        self.exportVideoHeight = QLineEdit()
        self.exportVideoHeight.setMaximumWidth(100)
        self.exportVideoHeight.setAlignment(Qt.AlignCenter)
        self.exportVideoHeight.setValidator(QIntValidator(100, 10000))
        resolutionLayout.addWidget(self.exportVideoWidth, 0, 1, 1, 1)
        xLabel = QLabel('x')
        xLabel.setAlignment(Qt.AlignCenter)
        resolutionLayout.addWidget(xLabel, 0, 2, 1, 1)
        resolutionLayout.addWidget(self.exportVideoHeight, 0, 3, 1, 1)

        layout.addWidget(QLabel(), 0, 2, 1, 1)
        layout.addWidget(QLabel('码率(k)'), 0, 3, 1, 1)
        self.exportVideoBitrate = QLineEdit()
        self.exportVideoBitrate.setValidator(QIntValidator(100, 10000))
        layout.addWidget(self.exportVideoBitrate, 0, 4, 1, 1)
        layout.addWidget(QLabel(), 0, 5, 1, 1)
        layout.addWidget(QLabel('帧率'), 0, 6, 1, 1)
        self.exportVideoFPS = QLineEdit()
        self.exportVideoFPS.setValidator(QIntValidator(10, 200))
        layout.addWidget(self.exportVideoFPS, 0, 7, 1, 1)

        self.anime4k = QPushButton('使用Anime4K扩展画质 (Coming Soon)')
#         self.anime4k.clicked.connect(self.anime4kClick)
        layout.addWidget(self.anime4k, 1, 0, 1, 1)
        layout.addWidget(QLabel('压缩比'), 1, 3, 1, 1)
        self.exportVideoPreset = QComboBox()
        self.exportVideoPreset.addItems(['极致(最慢)', '较高(较慢)', '中等(中速)', '较低(较快)', '最低(最快)'])
        self.exportVideoPreset.setCurrentIndex(2)
        layout.addWidget(self.exportVideoPreset, 1, 4, 1, 1)
        layout.addWidget(QLabel(), 1, 5, 1, 1)
        layout.addWidget(QLabel('编码器'), 1, 6, 1, 1)
        self.encoder = QComboBox()
        self.encoder.addItems(['CPU', 'GPU N卡', 'GPU A卡'])
        self.encoder.currentIndexChanged.connect(self.encoderChange)
        layout.addWidget(self.encoder, 1, 7, 1, 1)

        self.mixAudioPath = QLineEdit()
        layout.addWidget(self.mixAudioPath, 2, 0, 1, 1)
        self.mixAudioButton = QPushButton('音频混流')
        self.mixAudioButton.clicked.connect(self.openAudio)
        layout.addWidget(self.mixAudioButton, 2, 1, 1, 1)
        self.confirm = QPushButton('确定')
        self.confirm.clicked.connect(self.hide)
        layout.addWidget(self.confirm, 2, 6, 1, 2)

    def anime4kClick(self):
        self.anime4KToken = not self.anime4KToken
        if self.anime4KToken:
            self.anime4k.setStyleSheet('background-color:#3daee9')
        else:
            self.anime4k.setStyleSheet('background-color:#31363b')

    def openAudio(self):
        self.audioPath = QFileDialog.getOpenFileName(self, "请选择音频文件", None, "音频文件 (*.m4a *.mp3 *.wav);;所有文件(*.*)")[0]
        if self.audioPath:
            self.mixAudioPath.setText(self.audioPath)

    def encoderChange(self, index):
        if not index:
            self.exportVideoPreset.setEnabled(True)
        else:
            self.exportVideoPreset.setCurrentIndex(2)
            self.exportVideoPreset.setEnabled(False)


class advanced(QWidget):
    def __init__(self, videoWidth, videoHeight):
        super().__init__()
        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel('Title:'), 0, 0, 1, 1)
        self.title = QLineEdit()
        layout.addWidget(self.title, 0, 1, 1, 4)
        layout.addWidget(QLabel('Script:'), 1, 0, 1, 1)
        self.originalScript = QLineEdit()
        layout.addWidget(self.originalScript, 1, 1, 1, 1)
        layout.addWidget(QLabel('Translation:'), 1, 3, 1, 1)
        self.translation = QLineEdit()
        layout.addWidget(self.translation, 1, 4, 1, 1)
        layout.addWidget(QLabel('Editing:'), 2, 0, 1, 1)
        self.editing = QLineEdit()
        layout.addWidget(self.editing, 2, 1, 1, 1)
        layout.addWidget(QLabel('Timing:'), 2, 3, 1, 1)
        self.timing = QLineEdit()
        layout.addWidget(self.timing, 2, 4, 1, 1)

        layout.addWidget(QLabel('Script Type:'), 3, 0, 1, 1)
        self.scriptType = QLineEdit('v4.00+')
        layout.addWidget(self.scriptType, 3, 1, 1, 1)
        layout.addWidget(QLabel('Collisions:'), 3, 3, 1, 1)
        self.collisions = QComboBox()
        self.collisions.addItems(['Normal', 'Reverse'])
        layout.addWidget(self.collisions, 3, 4, 1, 1)
        layout.addWidget(QLabel('PlayResX:'), 4, 0, 1, 1)
        self.playResX = QLineEdit(str(videoWidth))
        layout.addWidget(self.playResX, 4, 1, 1, 1)
        layout.addWidget(QLabel('PlayResY:'), 4, 3, 1, 1)
        self.playResY = QLineEdit(str(videoHeight))
        layout.addWidget(self.playResY, 4, 4, 1, 1)
        layout.addWidget(QLabel('Timer:'), 5, 0, 1, 1)
        self.timer = QLineEdit('100.0000')
        layout.addWidget(self.timer, 5, 1, 1, 1)
        layout.addWidget(QLabel('WrapStyle:'), 5, 3, 1, 1)
        self.warpStyle = QComboBox()
        self.warpStyle.addItems(['0: 上行更长', '1: 行尾换行', '2: 不换行', '3: 下行更长'])
        layout.addWidget(self.warpStyle, 5, 4, 1, 1)
        layout.addWidget(QLabel('Scaled Border And Shadow:'), 6, 0, 1, 3)
        self.scaleBS = QComboBox()
        self.scaleBS.addItems(['yes', 'no'])
        layout.addWidget(self.scaleBS, 6, 4, 1, 1)

    def setPlayRes(self, videoWidth, videoHeight):
        self.playResX.setText(str(videoWidth))
        self.playResY.setText(str(videoHeight))


class fontWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.fontName = '微软雅黑'
        self.fontSize = 60
        self.fontBold = True
        self.fontItalic = False
        self.fontUnderline = False
        self.fontStrikeout = False
        fontBold = '粗体' if self.fontBold else ''
        fontItalic = '斜体' if self.fontItalic else ''
        fontUnderline = '下划线' if self.fontUnderline else ''
        fontStrikeOut = '删除线' if self.fontStrikeout else ''
        self.fontColor = '#ffffff'
        self.secondColor = '#000000'
        self.outlineColor = '#000000'
        self.shadowColor = '#696969'

        self.optionLayout = QGridLayout()
        self.setLayout(self.optionLayout)
        self.fontSelect = QPushButton('%s%s号%s%s%s%s' % (self.fontName, self.fontSize, fontBold, fontItalic, fontUnderline, fontStrikeOut))
        self.fontSelect.setFixedWidth(150)
        self.fontSelect.clicked.connect(self.getFont)
        self.optionLayout.addWidget(self.fontSelect, 0, 0, 1, 2)
        self.optionLayout.addWidget(QLabel(''), 0, 2, 1, 1)
        self.fontColorSelect = label()
        self.fontColorSelect.setAlignment(Qt.AlignCenter)
        self.fontColorSelect.setText(self.fontColor)
        self.fontColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.fontColor, self.colorReverse(self.fontColor)))
        self.fontColorSelect.clicked.connect(self.getFontColor)
        self.optionLayout.addWidget(self.fontColorSelect, 0, 3, 1, 1)
        self.fontColorLabel = QLabel('字体颜色')
        self.optionLayout.addWidget(self.fontColorLabel, 0, 4, 1, 1)
        self.karaoke = QPushButton('卡拉OK模式')
        self.karaoke.setFixedWidth(150)
        self.karaokeStatus = False
        self.karaoke.clicked.connect(self.setKaraoke)
        self.optionLayout.addWidget(self.karaoke, 1, 0, 1, 2)
        self.secondColorSelect = label()
        self.secondColorSelect.setAlignment(Qt.AlignCenter)
        self.secondColorSelect.setText(self.secondColor)
        self.secondColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.secondColor, self.colorReverse(self.secondColor)))
        self.secondColorSelect.clicked.connect(self.getSecondFontColor)
        self.secondColorSelect.hide()
        self.optionLayout.addWidget(self.secondColorSelect, 1, 3, 1, 1)
        self.secondColorLabel = QLabel('次要颜色')
        self.secondColorLabel.hide()
        self.optionLayout.addWidget(self.secondColorLabel, 1, 4, 1, 1)

        self.outlineSizeBox = QComboBox()
        self.outlineSizeBox.addItems(['0', '1', '2', '3', '4'])
        self.outlineSizeBox.setCurrentIndex(1)
        self.outlineSizeBox.setFixedWidth(100)
        self.optionLayout.addWidget(self.outlineSizeBox, 2, 0, 1, 1)
        self.outlineSizeLabel = QLabel('描边大小')
        self.optionLayout.addWidget(self.outlineSizeLabel, 2, 1, 1, 1)
        self.outlineColorSelect = label()
        self.outlineColorSelect.setAlignment(Qt.AlignCenter)
        self.outlineColorSelect.setText(self.outlineColor)
        self.outlineColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.outlineColor, self.colorReverse(self.outlineColor)))
        self.outlineColorSelect.clicked.connect(self.getOutlineColor)
        self.optionLayout.addWidget(self.outlineColorSelect, 2, 3, 1, 1)
        self.outlineColorLabel = QLabel('描边颜色')
        self.optionLayout.addWidget(self.outlineColorLabel, 2, 4, 1, 1)
        self.shadowSizeBox = QComboBox()
        self.shadowSizeBox.addItems(['0', '1', '2', '3', '4'])
        self.shadowSizeBox.setCurrentIndex(1)
        self.shadowSizeBox.setFixedWidth(100)
        self.optionLayout.addWidget(self.shadowSizeBox, 3, 0, 1, 1)
        self.shadowSizeLabel = QLabel('阴影大小')
        self.optionLayout.addWidget(self.shadowSizeLabel, 3, 1, 1, 1)
        self.shadowColorSelect = label()
        self.shadowColorSelect.setAlignment(Qt.AlignCenter)
        self.shadowColorSelect.setText(self.shadowColor)
        self.shadowColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.shadowColor, self.colorReverse(self.shadowColor)))
        self.shadowColorSelect.clicked.connect(self.getShadowColor)
        self.optionLayout.addWidget(self.shadowColorSelect, 3, 3, 1, 1)
        self.shadowColorLabel = QLabel('阴影颜色')
        self.optionLayout.addWidget(self.shadowColorLabel, 3, 4, 1, 1)
        self.align = QComboBox()
        self.align.addItems(['1: 左下', '2: 中下', '3: 右下', '4: 中左', '5: 中间', '6: 中右', '7: 左上', '8: 中上', '9: 右上'])
        self.align.setCurrentIndex(1)
        self.align.setFixedWidth(100)
        self.optionLayout.addWidget(self.align, 4, 0, 1, 1)
        self.alignLabel = QLabel('对齐方式')
        self.optionLayout.addWidget(self.alignLabel, 4, 1, 1, 1)
        self.VAlignSlider = QSlider()
        self.VAlignSlider.setFixedWidth(100)
        self.VAlignSlider.setTickPosition(QSlider.TicksAbove)
        self.VAlignSlider.setSingleStep(10)
        self.VAlignSlider.setTickInterval(20)
        self.optionLayout.addWidget(self.VAlignSlider, 4, 3, 1, 1)
        self.VAlignSlider.setOrientation(Qt.Horizontal)
        self.VAlignLabel = QLabel('垂直边距')
        self.optionLayout.addWidget(self.VAlignLabel, 4, 4, 1, 1)

        self.LAlignSlider = QSlider()
        self.LAlignSlider.setFixedWidth(100)
        self.LAlignSlider.setTickPosition(QSlider.TicksAbove)
        self.LAlignSlider.setSingleStep(10)
        self.LAlignSlider.setTickInterval(20)
        self.optionLayout.addWidget(self.LAlignSlider, 5, 0, 1, 1)
        self.LAlignSlider.setOrientation(Qt.Horizontal)
        self.LAlignLabel = QLabel('左边距')
        self.optionLayout.addWidget(self.LAlignLabel, 5, 1, 1, 1)
        self.RAlignSlider = QSlider()
        self.RAlignSlider.setFixedWidth(100)
        self.RAlignSlider.setTickPosition(QSlider.TicksAbove)
        self.RAlignSlider.setSingleStep(10)
        self.RAlignSlider.setTickInterval(20)
        self.optionLayout.addWidget(self.RAlignSlider, 5, 3, 1, 1)
        self.RAlignSlider.setOrientation(Qt.Horizontal)
        self.RAlignLabel = QLabel('右边距')
        self.optionLayout.addWidget(self.RAlignLabel, 5, 4, 1, 1)

    def getFont(self):
        status, font = QFontDialog.getFont()
        if status:
            self.font = QFontInfo(font)
            self.fontName = self.font.family()
            self.fontSize = self.font.pointSize()
            self.fontBold = self.font.bold()
            self.fontItalic = self.font.italic()
            self.fontUnderline = self.font.underline()
            self.fontStrikeout = self.font.strikeOut()
            fontBold = '粗体' if self.fontBold else ''
            fontItalic = '斜体' if self.fontItalic else ''
            fontUnderline = '下划线' if self.fontUnderline else ''
            fontStrikeOut = '删除线' if self.fontStrikeout else ''
            self.fontSelect.setText('%s%s号%s%s%s%s' % (self.fontName, self.fontSize, fontBold, fontItalic, fontUnderline, fontStrikeOut))

    def setKaraoke(self):
        self.karaokeStatus = not self.karaokeStatus
        if self.karaokeStatus:
            self.secondColorSelect.show()
            self.secondColorLabel.show()
            self.karaoke.setStyleSheet('background-color:#3daee9')
        else:
            self.secondColorSelect.hide()
            self.secondColorLabel.hide()
            self.karaoke.setStyleSheet('background-color:#31363b')

    def getFontColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.fontColor = color.name()
            self.fontColorSelect.setText(self.fontColor)
            self.fontColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.fontColor, self.colorReverse(self.fontColor)))

    def getSecondFontColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.secondColor = color.name()
            self.secondColorSelect.setText(self.fontColor)
            self.secondColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.secondColor, self.colorReverse(self.secondColor)))

    def getOutlineColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.outlineColor = color.name()
            self.outlineColorSelect.setText(self.outlineColor)
            self.outlineColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.outlineColor, self.colorReverse(self.outlineColor)))

    def getShadowColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.shadowColor = color.name()
            self.shadowColorSelect.setText(self.shadowColor)
            self.shadowColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.shadowColor, self.colorReverse(self.shadowColor)))

    def colorReverse(self, color):
        r = 255 - int(color[1:3], 16)
        g = 255 - int(color[3:5], 16)
        b = 255 - int(color[5:7], 16)
        return '#%s%s%s' % (hex(r)[2:], hex(g)[2:], hex(b)[2:])


class VideoDecoder(QDialog):
    def __init__(self):
        self.videoPath = ''
        self.videoWidth = 1920
        self.videoHeight = 1080
        self.subtitles = {x: {} for x in range(5)}
        self.setEncode = encodeOption()

        super().__init__()
        self.setWindowTitle('字幕输出及合成')
        self.resize(1750, 800)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.preview = QLabel('效果预览')
        self.preview.setMaximumHeight(750)
        self.preview.setMaximumWidth(1300)
        self.layout.addWidget(self.preview, 0, 0, 6, 10)
        self.preview.setScaledContents(True)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("QLabel{background:white;}")

        self.previewSlider = Slider()
        self.previewSlider.setOrientation(Qt.Horizontal)
        self.previewSlider.setMinimum(0)
        self.previewSlider.setMaximum(1000)
        self.previewSlider.pointClicked.connect(self.setPreviewSlider)
        self.layout.addWidget(self.previewSlider, 6, 0, 1, 10)

        self.option = QTabWidget()
        self.option.setMaximumWidth(450)
        self.layout.addWidget(self.option, 0, 10, 3, 1)
        self.subDict = {x: fontWidget() for x in range(5)}
        for subNumber, tabPage in self.subDict.items():
            self.option.addTab(tabPage, '字幕 %s' % (subNumber + 1))
        self.advanced = advanced(self.videoWidth, self.videoHeight)
        self.option.addTab(self.advanced, 'ASS字幕信息')

        self.startGrid = QWidget()
        self.layout.addWidget(self.startGrid, 3, 10, 3, 1)
        self.startLayout = QGridLayout()
        self.startGrid.setLayout(self.startLayout)
        self.sub1Check = QPushButton('字幕 1')
        self.sub1Check.setStyleSheet('background-color:#3daee9')
        self.sub2Check = QPushButton('字幕 2')
        self.sub3Check = QPushButton('字幕 3')
        self.sub4Check = QPushButton('字幕 4')
        self.sub5Check = QPushButton('字幕 5')
        self.sub1CheckStatus = True
        self.sub2CheckStatus = False
        self.sub3CheckStatus = False
        self.sub4CheckStatus = False
        self.sub5CheckStatus = False
        self.sub1Check.clicked.connect(self.sub1CheckButtonClick)
        self.sub2Check.clicked.connect(self.sub2CheckButtonClick)
        self.sub3Check.clicked.connect(self.sub3CheckButtonClick)
        self.sub4Check.clicked.connect(self.sub4CheckButtonClick)
        self.sub5Check.clicked.connect(self.sub5CheckButtonClick)
        self.startLayout.addWidget(self.sub1Check, 0, 0, 1, 1)
        self.startLayout.addWidget(self.sub2Check, 0, 1, 1, 1)
        self.startLayout.addWidget(self.sub3Check, 0, 2, 1, 1)
        self.startLayout.addWidget(self.sub4Check, 0, 3, 1, 1)
        self.startLayout.addWidget(self.sub5Check, 0, 4, 1, 1)
        self.layerCheck = QPushButton('禁止字幕重叠')
        self.layerCheck.setStyleSheet('background-color:#3daee9')
        self.layerCheckStatus = True
        self.layerCheck.clicked.connect(self.layerButtonClick)
        self.startLayout.addWidget(self.layerCheck, 1, 0, 1, 2)
        self.encodeSetup = QPushButton('编码设置')
        self.encodeSetup.clicked.connect(self.setEncodeArgs)
        self.startLayout.addWidget(self.encodeSetup, 1, 3, 1, 2)
        self.outputEdit = QLineEdit()
        self.startLayout.addWidget(self.outputEdit, 2, 0, 1, 4)
        self.outputButton = QPushButton('保存路径')
        self.startLayout.addWidget(self.outputButton, 2, 4, 1, 1)
        self.outputButton.clicked.connect(self.setSavePath)
        self.exportSubButton = QPushButton('导出字幕')
        self.exportSubButton.clicked.connect(self.exportSub)
        self.exportSubButton.setFixedHeight(50)
        self.startLayout.addWidget(self.exportSubButton, 3, 0, 1, 2)
        self.startButton = QPushButton('开始合成')
        self.startButton.clicked.connect(self.exportVideo)
        self.startButton.setFixedHeight(50)
        self.startLayout.addWidget(self.startButton, 3, 3, 1, 2)

        self.processBar = QProgressBar()
        self.processBar.setStyleSheet("QProgressBar{border:1px;text-align:center;background:white}")
        self.processBar.setMaximumWidth(450)
        self.layout.addWidget(self.processBar, 6, 10, 1, 1)

        self.totalFrames = 0
        self.old_decodeArgs = []
        self.videoPos = 1
        self.old_videoPos = 1
        self.duration = 0
        self.previewTimer = QTimer()
        self.previewTimer.setInterval(50)
        self.previewTimer.start()
        self.previewTimer.timeout.connect(self.generatePreview)

    def sub1CheckButtonClick(self):
        self.sub1CheckStatus = not self.sub1CheckStatus
        if self.sub1CheckStatus:
            self.sub1Check.setStyleSheet('background-color:#3daee9')
        else:
            self.sub1Check.setStyleSheet('background-color:#31363b')

    def sub2CheckButtonClick(self):
        self.sub2CheckStatus = not self.sub2CheckStatus
        if self.sub2CheckStatus:
            self.sub2Check.setStyleSheet('background-color:#3daee9')
        else:
            self.sub2Check.setStyleSheet('background-color:#31363b')

    def sub3CheckButtonClick(self):
        self.sub3CheckStatus = not self.sub3CheckStatus
        if self.sub3CheckStatus:
            self.sub3Check.setStyleSheet('background-color:#3daee9')
        else:
            self.sub3Check.setStyleSheet('background-color:#31363b')

    def sub4CheckButtonClick(self):
        self.sub4CheckStatus = not self.sub4CheckStatus
        if self.sub4CheckStatus:
            self.sub4Check.setStyleSheet('background-color:#3daee9')
        else:
            self.sub4Check.setStyleSheet('background-color:#31363b')

    def sub5CheckButtonClick(self):
        self.sub5CheckStatus = not self.sub5CheckStatus
        if self.sub5CheckStatus:
            self.sub5Check.setStyleSheet('background-color:#3daee9')
        else:
            self.sub5Check.setStyleSheet('background-color:#31363b')

    def layerButtonClick(self):
        self.layerCheckStatus = not self.layerCheckStatus
        if self.layerCheckStatus:
            self.layerCheck.setStyleSheet('background-color:#3daee9')
        else:
            self.layerCheck.setStyleSheet('background-color:#31363b')

    def setSavePath(self):
        savePath = QFileDialog.getSaveFileName(self, "选择视频输出文件夹", None, "MP4格式 (*.mp4)")[0]
        if savePath:
            self.outputEdit.setText(savePath)

    def setDefault(self, videoPath, videoWidth, videoHeight, duration, bitrate, fps, subtitles):
        self.videoPath = videoPath
        self.videoWidth = videoWidth
        self.videoHeight = videoHeight
        self.setEncode.exportVideoWidth.setText(str(videoWidth))
        self.setEncode.exportVideoHeight.setText(str(videoHeight))
        self.setEncode.exportVideoBitrate.setText(str(bitrate))
        self.setEncode.exportVideoFPS.setText(str(fps))
        self.duration = duration
        self.advanced.setPlayRes(videoWidth, videoHeight)
        self.subtitles = copy.deepcopy(subtitles)
        for index in self.subtitles:
            if -1 in self.subtitles[index]:
                del self.subtitles[index][-1]

    def setPreviewSlider(self, p):
        pos = p.x() / self.previewSlider.width() * 1000
        if pos > 1000:
            pos = 1000
        elif pos < 0:
            pos = 0
        self.previewSlider.setValue(pos)
        self.videoPos = pos * self.duration // 1000000

    def ffmpegColor(self, color):
        color = color.upper()
        r = color[1:3]
        g = color[3:5]
        b = color[5:7]
        return '&H00%s%s%s' % (b, g, r)

    def collectArgs(self):
        self.decodeArgs = [[self.advanced.title.text(), self.advanced.originalScript.text(), self.advanced.translation.text(),
                           self.advanced.editing.text(), self.advanced.timing.text(), self.advanced.scriptType.text(),
                           self.advanced.collisions.currentText(), self.advanced.playResX.text(), self.advanced.playResY.text(),
                           self.advanced.timer.text(), self.advanced.warpStyle.currentText().split(':')[0], self.advanced.scaleBS.currentText()]]
        self.selectedSubDict = {}
        for subNumber, subCheck in enumerate([self.sub1CheckStatus, self.sub2CheckStatus, self.sub3CheckStatus, self.sub4CheckStatus, self.sub5CheckStatus]):
            if subCheck:
                self.selectedSubDict[subNumber] = self.subDict[subNumber]
        self.subtitleArgs = {}
        for subNumber, font in self.selectedSubDict.items():
            if font.karaoke.isChecked():
                secondColor = self.ffmpegColor(font.secondColor)
            else:
                secondColor = '&H00000000'
            fontBold = -1 if font.fontBold else 0
            fontItalic = -1 if font.fontItalic else 0
            fontUnderline = -1 if font.fontUnderline else 0
            fontStrikeout = -1 if font.fontStrikeout else 0
            self.subtitleArgs[subNumber] = [font.fontName, font.fontSize, self.ffmpegColor(font.fontColor), secondColor,
                                            self.ffmpegColor(font.outlineColor), self.ffmpegColor(font.shadowColor),
                                            fontBold, fontItalic, fontUnderline, fontStrikeout, 100, 100, 0, 0, 1,
                                            font.outlineSizeBox.currentText(), font.shadowSizeBox.currentText(),
                                            font.align.currentText().split(':')[0],
                                            int(self.videoWidth * (font.LAlignSlider.value() / 100)),
                                            int(self.videoWidth * (font.RAlignSlider.value() / 100)),
                                            int(self.videoHeight * (font.VAlignSlider.value() / 100)), 1]
        self.decodeArgs.append(self.subtitleArgs)
        self.decodeArgs.append([self.videoPath, self.layerCheckStatus])

    def exportSub(self):
        subtitlePath = QFileDialog.getSaveFileName(self, "选择字幕输出文件夹", None, "ASS字幕文件 (*.ass)")[0]
        if subtitlePath:
            self.writeAss(subtitlePath, False, True)
            QMessageBox.information(self, '导出字幕', '导出完成', QMessageBox.Yes)

    def writeAss(self, outputPath='temp_sub.ass', preview=True, tip=False, pos=0):
        ass = codecs.open(outputPath, 'w', 'utf_8_sig')
        ass.write('[Script Info]\n')
        ass.write('Title: %s\n' % self.advanced.title.text())
        ass.write('OriginalScript: %s\n' % self.advanced.originalScript.text())
        ass.write('OriginalTranslation: %s\n' % self.advanced.translation.text())
        ass.write('OriginalEditing: %s\n' % self.advanced.editing.text())
        ass.write('OriginalTiming: %s\n' % self.advanced.timing.text())
        ass.write('ScriptType: %s\n' % self.advanced.scriptType.text())
        ass.write('Collisions: %s\n' % self.advanced.collisions.currentText())
        ass.write('PlayResX: %s\n' % self.advanced.playResX.text())
        ass.write('PlayResY: %s\n' % self.advanced.playResY.text())
        ass.write('Timer: %s\n' % self.advanced.timer.text())
        ass.write('WrapStyle: %s\n' % self.advanced.warpStyle.currentText().split(':')[0])
        ass.write('ScaledBorderAndShadow: %s\n\n' % self.advanced.scaleBS.currentText())

        ass.write('[V4+ Styles]\n')
        ass.write('Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ')
        ass.write('ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n')
        for subNumber, fontArgs in self.subtitleArgs.items():
            style = 'Style: Subtitle_%s' % (subNumber + 1)
            for i in fontArgs:
                style += ',%s' % i
            ass.write('%s\n\n' % style)

        ass.write('[Events]\n')
        ass.write('Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
        if preview:
            for subNumber in self.subtitleArgs:
                num = subNumber + 1
                if self.layerCheckStatus:
                    line = 'Dialogue: 0,0:00:00.00,0:00:10.00,%s,#%s,0,0,0,,%s\n' % ('Subtitle_%s' % num, num, r'Hi! 我是第%s列字幕。' % num)
                else:
                    line = 'Dialogue: %s,0:00:00.00,0:00:10.00,%s,#%s,0,0,0,,%s\n' % (subNumber, 'Subtitle_%s' % num, num, 'Hi! 我是第%s列字幕。' % num)
                ass.write(line)
            if tip:
                QMessageBox.information(self, '导出字幕', '导出完成', QMessageBox.Yes)
        else:
            if not pos:
                for subNumber in self.subtitleArgs:
                    for start, subData in self.subtitles[subNumber].items():
                        num = subNumber + 1
                        if self.layerCheckStatus:
                            line = 'Dialogue: 0,%s,%s,%s,#%s,0,0,0,,%s\n' % (ms2Time(start), ms2Time(start + subData[0]), 'Subtitle_%s' % num, num, subData[1])
                        else:
                            line = 'Dialogue: %s,%s,%s,%s,#%s,0,0,0,,%s\n' % (subNumber, ms2Time(start), ms2Time(start + subData[0]), 'Subtitle_%s' % num, num, subData[1])
                        ass.write(line)
            else:
                for subNumber in self.subtitleArgs:
                    startKeys = list(self.subtitles[subNumber].keys())
                    for cnt, start in enumerate(startKeys):
                        if start / 1000 > pos and cnt:
                            start = startKeys[cnt - 1]
                            subData = self.subtitles[subNumber][start]
                            num = subNumber + 1
                            if self.layerCheckStatus:
                                line = 'Dialogue: 0,0:00:00.00,0:00:10.00,%s,#%s,0,0,0,,%s\n' % ('Subtitle_%s' % num, num, subData[1])
                            else:
                                line = 'Dialogue: %s,0:00:00.00,0:00:10.00,%s,#%s,0,0,0,,%s\n' % (subNumber, 'Subtitle_%s' % num, num, subData[1])
                            ass.write(line)
                            break
        ass.close()

    def generatePreview(self, force=False):
        self.collectArgs()
        if not self.selectedSubDict:
            self.exportSubButton.setEnabled(False)
        else:
            self.exportSubButton.setEnabled(True)
        if not self.videoPath or not self.outputEdit.text():
            self.startButton.setEnabled(False)
        else:
            self.startButton.setEnabled(True)
        if self.decodeArgs != self.old_decodeArgs or self.videoPos != self.old_videoPos or force:
            if os.path.exists('temp_sub.jpg'):
                os.remove('temp_sub.jpg')
            if self.decodeArgs != self.old_decodeArgs:
                self.old_decodeArgs = self.decodeArgs
                self.writeAss()
            elif self.videoPos != self.old_videoPos:
                self.old_videoPos = self.videoPos
                self.writeAss(preview=False, pos=self.videoPos)
            else:
                self.writeAss()
            videoWidth = self.setEncode.exportVideoWidth.text()
            videoHeight = self.setEncode.exportVideoHeight.text()
            bit = self.setEncode.exportVideoBitrate.text() + 'k'
            preset = ['veryslow', 'slower', 'medium', 'faster', 'ultrafast'][self.setEncode.exportVideoPreset.currentIndex()]
            cmd = ['utils/ffmpeg.exe', '-y', '-ss', str(self.videoPos), '-i', self.videoPath, '-frames', '1', '-vf', 'ass=temp_sub.ass',
                   '-s', '%sx%s' % (videoWidth, videoHeight), '-b:v', bit, '-preset', preset, '-q:v', '1', '-f', 'image2', 'temp_sub.jpg']
            if not self.videoPath:
                self.preview.setText('请先在主界面选择视频')
                self.preview.setStyleSheet("QLabel{background:white;color:#232629}")
            else:
                p = subprocess.Popen(cmd)
                p.wait()
                pixmap = QPixmap('temp_sub.jpg')
                self.preview.setPixmap(pixmap)
        else:
            pass

    def setEncodeArgs(self):
        self.setEncode.hide()
        self.setEncode.show()

    def exportVideo(self):
        self.startButton.setText('停止')
        self.startButton.setStyleSheet('background-color:#3daee9')
        self.startButton.clicked.disconnect(self.exportVideo)
        self.startButton.clicked.connect(self.terminateEncode)
        self.processBar.setValue(0)
        outputPath = self.outputEdit.text()
        if os.path.exists(outputPath):
            os.remove(outputPath)
        if os.path.exists('temp_sub.ass'):
            os.remove('temp_sub.ass')
        self.previewTimer.stop()
        self.collectArgs()
        self.writeAss(preview=False)

        videoWidth = self.setEncode.exportVideoWidth.text()
        videoHeight = self.setEncode.exportVideoHeight.text()
        preset = ['veryslow', 'slower', 'medium', 'faster', 'ultrafast'][self.setEncode.exportVideoPreset.currentIndex()]
        audio = ''
        if self.setEncode.mixAudioPath.text():
            audio = self.setEncode.mixAudioPath.text()
        self.anime4k = self.setEncode.anime4KToken
        encoder = self.setEncode.encoder.currentIndex()
        bit = self.setEncode.exportVideoBitrate.text() + 'k'
        fps = self.setEncode.exportVideoFPS.text()
        cmd = ['utils/ffmpeg.exe', '-y', '-i', self.videoPath, '-b:v', bit, '-r', fps]
        if audio:
            cmd += ['-i', audio, '-c:a', 'aac']
        cmd += ['-s', '%sx%s' % (videoWidth, videoHeight), '-preset', preset, '-vf', 'ass=temp_sub.ass']
        if encoder == 1:
            cmd += ['-c:v', 'h264_nvenc']
        elif encoder == 2:
            cmd += ['-c:v', 'h264_amf']
        cmd.append(outputPath)

        self.videoEncoder = videoEncoder(self.videoPath, cmd)
        self.videoEncoder.processBar.connect(self.setProcessBar)
        self.videoEncoder.currentPos.connect(self.setEncodePreview)
        self.videoEncoder.encodeResult.connect(self.encodeFinish)
        self.videoEncoder.start()

    def setProcessBar(self, value):
        self.processBar.setValue(value)
        self.previewSlider.setValue(value * 10)

    def setEncodePreview(self, currentPos):
        self.writeAss(preview=False, pos=calSubTime(currentPos))
        cmd = ['utils/ffmpeg.exe', '-y', '-ss', currentPos, '-i', self.videoPath, '-frames', '1', '-vf', 'ass=temp_sub.ass', '-q:v', '1', '-f', 'image2', 'temp_sub.jpg']
        p = subprocess.Popen(cmd)
        p.wait()
        pixmap = QPixmap('temp_sub.jpg')
        self.preview.setPixmap(pixmap)

    def encodeFinish(self, result):
        self.startButton.setText('开始合成')
        self.startButton.setStyleSheet('background-color:#31363b')
        self.startButton.clicked.disconnect(self.terminateEncode)
        self.startButton.clicked.connect(self.exportVideo)
        if result:
            self.previewTimer.start()
            self.processBar.setValue(100)
            QMessageBox.information(self, '导出视频', '导出完成', QMessageBox.Yes)
        else:
            self.previewTimer.start()
            self.processBar.setValue(0)
            QMessageBox.information(self, '导出视频', '导出视频失败！请检查参数或编码器是否选择正确', QMessageBox.Yes)
        self.generatePreview(force=True)

    def terminateEncode(self):
        self.startButton.setText('开始合成')
        self.startButton.setStyleSheet('background-color:#31363b')
        self.startButton.clicked.disconnect(self.terminateEncode)
        self.startButton.clicked.connect(self.exportVideo)
        try:
            p = psutil.Process(self.videoEncoder.p.pid)
            for proc in p.children(True):
                proc.kill()
            p.kill()
        except:
            pass
        self.videoEncoder.terminate()
        self.videoEncoder.quit()
        self.videoEncoder.wait()
        del self.videoEncoder
        self.processBar.setValue(0)
        QMessageBox.information(self, '导出视频', '中止导出', QMessageBox.Yes)
        self.generatePreview(force=True)
        self.previewTimer.start()
