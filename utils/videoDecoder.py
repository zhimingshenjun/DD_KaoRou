import os, codecs, subprocess
from PySide2.QtWidgets import QGridLayout, QFileDialog, QDialog, QPushButton,\
        QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QProgressBar, QLabel,\
        QComboBox, QCheckBox, QWidget, QSlider, QFontDialog, QColorDialog, QTabWidget
from PySide2.QtCore import Qt, QTimer, Signal, QThread
from PySide2.QtGui import QFontInfo, QPixmap


class label(QLabel):
    clicked = Signal()

    def mouseReleaseEvent(self, QMouseEvent):
        self.clicked.emit()


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
        self.align.addItems(['1: 左下', '2: 中下', '3: 右下', '5: 左上', '6: 中上', '7: 右上', '9: 中左', '10: 中间', '11: 中右'])
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
        self.previewSub = {x: {0: [1000, 'Hello! 我是第%s列字幕~' % (x + 1)]} for x in range(5)}

        super().__init__()
        self.setWindowTitle('字幕输出及合成')
        self.resize(1700, 750)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.preview = QLabel('效果预览')
        self.layout.addWidget(self.preview, 0, 0, 6, 10)
        self.preview.setScaledContents(True)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("QLabel{background:white;}")

        self.option = QTabWidget()
        self.option.setFixedWidth(415)
        self.layout.addWidget(self.option, 0, 10, 3, 1)
        self.subDict = {x: fontWidget() for x in range(5)}
        for subNumber, tabPage in self.subDict.items():
            self.option.addTab(tabPage, '字幕 %s' % (subNumber + 1))
        self.advanced = advanced(self.videoWidth, self.videoHeight)
        self.option.addTab(self.advanced, 'Script Info')

        self.startGrid = QWidget()
        self.layout.addWidget(self.startGrid, 3, 10, 2, 1)
        self.startLayout = QGridLayout()
        self.startGrid.setLayout(self.startLayout)
        self.sub1Check = QPushButton('字幕 1')
        self.sub1Check.setFixedWidth(75)
        self.sub1Check.setStyleSheet('background-color:#3daee9')
        self.sub2Check = QPushButton('字幕 2')
        self.sub2Check.setFixedWidth(75)
        self.sub3Check = QPushButton('字幕 3')
        self.sub3Check.setFixedWidth(75)
        self.sub4Check = QPushButton('字幕 4')
        self.sub4Check.setFixedWidth(75)
        self.sub5Check = QPushButton('字幕 5')
        self.sub5Check.setFixedWidth(75)
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
        self.layerCheck = QPushButton('使用同一个字幕图层')
        self.layerCheck.setStyleSheet('background-color:#3daee9')
        self.layerCheckStatus = True
        self.layerCheck.clicked.connect(self.layerButtonClick)
        self.startLayout.addWidget(self.layerCheck, 1, 0, 1, 2)
        self.startLayout.addWidget(QLabel('编码器：'), 1, 3, 1, 1)
        self.decodeSelect = QComboBox()
        self.decodeSelect.addItems(['CPU', 'GPU'])
        self.decodeSelect.setFixedWidth(75)
        self.decodeSelect.setCurrentIndex(0)
        self.startLayout.addWidget(self.decodeSelect, 1, 4, 1, 1)
        self.outputEdit = QLineEdit()
        self.startLayout.addWidget(self.outputEdit, 2, 0, 1, 4)
        self.outputButton = QPushButton('保存路径')
        self.startLayout.addWidget(self.outputButton, 2, 4, 1, 1)
        self.previewButton = QPushButton('生成预览')
        self.previewButton.clicked.connect(self.generatePreview)
        self.previewButton.setFixedHeight(50)
        self.startLayout.addWidget(self.previewButton, 3, 0, 1, 2)
        self.startButton = QPushButton('开始合成')
        self.startButton.setFixedHeight(50)
        self.startLayout.addWidget(self.startButton, 3, 3, 1, 2)

        self.processBar = QProgressBar()
        self.processBar.setStyleSheet("QProgressBar{border:1px;text-align:center;background:white}")
        self.processBar.setFixedWidth(380)
        self.layout.addWidget(self.processBar, 5, 10, 1, 1)

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
        print(self.sub3CheckStatus)

    def sub4CheckButtonClick(self):
        self.sub4CheckStatus = not self.sub4CheckStatus
        if self.sub4CheckStatus:
            self.sub4Check.setStyleSheet('background-color:#3daee9')
        else:
            self.sub4Check.setStyleSheet('background-color:#31363b')
        print(self.sub4CheckStatus)

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

    def setVideoArgs(self, videoPath, videoWidth, videoHeight, subtiltes):
        self.videoPath = videoPath
        self.videoWidth = videoWidth
        self.videoHeight = videoHeight
        self.advanced.setPlayRes(videoWidth, videoHeight)
        for index in subtiltes:
            if -1 in subtiltes[index]:
                del subtiltes[index][-1]
        self.subtitles = subtiltes

    def ffmpegColor(self, color):
        color = color.upper()
        r = color[1:3]
        g = color[3:5]
        b = color[5:7]
        return '&H00%s%s%s' % (b, g, r)

    def collectArgs(self):
        self.selectedSubDict = {}
        for subNumber, subCheck in enumerate([self.sub1CheckStatus, self.sub2CheckStatus, self.sub3CheckStatus, self.sub4CheckStatus, self.sub5CheckStatus]):
            if subCheck:
                self.selectedSubDict[subNumber] = self.subDict[subNumber]
        self.decodeArgs = {}
        for subNumber, font in self.selectedSubDict.items():
            if font.karaoke.isChecked():
                secondColor = self.ffmpegColor(font.secondColor)
            else:
                secondColor = '&H00000000'
            fontBold = -1 if font.fontBold else 0
            fontItalic = -1 if font.fontItalic else 0
            fontUnderline = -1 if font.fontUnderline else 0
            fontStrikeout = -1 if font.fontStrikeout else 0
            self.decodeArgs[subNumber] = [font.fontName, font.fontSize, self.ffmpegColor(font.fontColor), secondColor,
                                          self.ffmpegColor(font.outlineColor), self.ffmpegColor(font.shadowColor),
                                          fontBold, fontItalic, fontUnderline, fontStrikeout, 100, 100, 0, 0, 1,
                                          font.outlineSizeBox.currentText(), font.shadowSizeBox.currentText(),
                                          font.align.currentText().split(':')[0],
                                          int(self.videoWidth * (font.LAlignSlider.value() / 100)),
                                          int(self.videoWidth * (font.RAlignSlider.value() / 100)),
                                          int(self.videoHeight * (font.VAlignSlider.value() / 100)), 1]
#         self.decodeArgs['decoder'] = self.decodeSelect.currentIndex()

        ass = codecs.open('temp_sub.ass', 'w', 'utf_8_sig')
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
        for subNumber, fontArgs in self.decodeArgs.items():
            style = 'Style: Subtitle_%s' % (subNumber + 1)
            for i in fontArgs:
                style += ',%s' % i
            ass.write('%s\n\n' % style)
        ass.close()

    def generatePreview(self):
        if os.path.exists('temp_sub.jpg'):
            os.remove('temp_sub.jpg')
        self.collectArgs()
        ass = codecs.open('temp_sub.ass', 'a', 'utf_8_sig')
        ass.write('[Events]\n')
        ass.write('Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
        if self.layerCheckStatus:
            for subNumber in self.decodeArgs:
                num = subNumber + 1
                line = 'Dialogue: 0,0:00:00.00,0:00:10.00,%s,#%s,0,0,0,,%s\n' % ('Subtitle_%s' % num, num, 'Hi! 我是第%s列字幕。' % num)
                ass.write(line)
        else:
            for subNumber in self.decodeArgs:
                num = subNumber + 1
                line = 'Dialogue: %s,0:00:00.00,0:00:10.00,%s,#%s,0,0,0,,%s\n' % (subNumber, 'Subtitle_%s' % num, num, 'Hi! 我是第%s列字幕。' % num)
                ass.write(line)
        ass.close()
        cmd = ['ffmpeg.exe', '-t', '0.001', '-i', self.videoPath, '-vf', 'ass=temp_sub.ass', '-q:v', '2', '-f', 'image2', 'temp_sub.jpg']
        if not self.videoPath:
            self.preview.setText('请先在主界面选择加载视频')
        elif not self.selectedSubDict:
            self.preview.setText('请勾选要合成的字幕')
        else:
            p = subprocess.Popen(cmd)
            p.wait()
        pixmap = QPixmap('temp_sub.jpg')
        self.preview.setPixmap(pixmap)
