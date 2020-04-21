from PySide2.QtWidgets import QGridLayout, QFileDialog, QDialog, QPushButton,\
        QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QProgressBar, QLabel,\
        QComboBox, QCheckBox, QWidget, QSlider, QFontDialog, QColorDialog, QTabWidget
from PySide2.QtCore import Qt, QTimer, Signal, QThread
from PySide2.QtGui import QFontInfo


class label(QLabel):
    clicked = Signal()

    def mouseReleaseEvent(self, QMouseEvent):
        self.clicked.emit()


class fontWidget(QWidget):
    def __init__(self, sliderValue):
        super().__init__()
        self.fontName = '微软雅黑'
        self.fontSize = 14
        self.fontBold = True
        self.fontItalic = False
        fontBold = '粗体' if self.fontBold else ''
        fontItalic = '斜体' if self.fontItalic else ''
        self.fontColor = '#ffffff'
        self.outlineColor = '#000000'
        self.shadowColor = '#696969'

        self.optionLayout = QGridLayout()
        self.setLayout(self.optionLayout)
        self.fontSelect = QPushButton('%s %s号 %s %s' % (self.fontName, self.fontSize, fontBold, fontItalic))
        self.fontSelect.setFixedWidth(150)
        self.fontSelect.clicked.connect(self.getFont)
        self.optionLayout.addWidget(self.fontSelect, 0, 0, 1, 2)
        self.optionLayout.addWidget(QLabel(''), 0, 2, 1, 1)
        self.fontColorSelect = label()
        self.fontColorSelect.setAlignment(Qt.AlignCenter)
        self.fontColorSelect.setText(self.fontColor)
        self.fontColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.fontColor, self.colorReverse(self.fontColor)))
        self.fontColorSelect.clicked.connect(self.getFontColor)
        self.optionLayout.addWidget(self.fontColorSelect, 0, 3, 1, 4)
        self.fontColorLabel = QLabel('字体颜色')
        self.optionLayout.addWidget(self.fontColorLabel, 0, 7, 1, 1)

        self.outlineSizeBox = QComboBox()
        self.outlineSizeBox.addItems(['0', '1', '2', '3', '4'])
        self.outlineSizeBox.setCurrentIndex(1)
        self.outlineSizeBox.setFixedWidth(100)
        self.optionLayout.addWidget(self.outlineSizeBox, 1, 0, 1, 1)
        self.outlineSizeLabel = QLabel('描边大小')
        self.optionLayout.addWidget(self.outlineSizeLabel, 1, 1, 1, 1)
        self.outlineColorSelect = label()
        self.outlineColorSelect.setAlignment(Qt.AlignCenter)
        self.outlineColorSelect.setText(self.outlineColor)
        self.outlineColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.outlineColor, self.colorReverse(self.outlineColor)))
        self.outlineColorSelect.clicked.connect(self.getOutlineColor)
        self.optionLayout.addWidget(self.outlineColorSelect, 1, 3, 1, 4)
        self.outlineColorLabel = QLabel('描边颜色')
        self.optionLayout.addWidget(self.outlineColorLabel, 1, 7, 1, 1)
        self.shadowSizeBox = QComboBox()
        self.shadowSizeBox.addItems(['0', '1', '2', '3', '4'])
        self.shadowSizeBox.setCurrentIndex(1)
        self.shadowSizeBox.setFixedWidth(100)
        self.optionLayout.addWidget(self.shadowSizeBox, 2, 0, 1, 1)
        self.shadowSizeLabel = QLabel('阴影大小')
        self.optionLayout.addWidget(self.shadowSizeLabel, 2, 1, 1, 1)
        self.shadowColorSelect = label()
        self.shadowColorSelect.setAlignment(Qt.AlignCenter)
        self.shadowColorSelect.setText(self.shadowColor)
        self.shadowColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.shadowColor, self.colorReverse(self.shadowColor)))
        self.shadowColorSelect.clicked.connect(self.getShadowColor)
        self.optionLayout.addWidget(self.shadowColorSelect, 2, 3, 1, 4)
        self.shadowColorLabel = QLabel('阴影颜色')
        self.optionLayout.addWidget(self.shadowColorLabel, 2, 7, 1, 1)
        self.align = QComboBox()
        self.align.addItems(['居中', '靠左', '靠右'])
        self.align.setFixedWidth(100)
        self.optionLayout.addWidget(self.align, 3, 0, 1, 1)
        self.alignLabel = QLabel('对齐方式')
        self.optionLayout.addWidget(self.alignLabel, 3, 1, 1, 1)
        self.VAlignSlider = QSlider()
        self.VAlignSlider.setValue(sliderValue)
        self.VAlignSlider.setFixedWidth(100)
        self.VAlignSlider.setTickPosition(QSlider.TicksAbove)
        self.VAlignSlider.setSingleStep(10)
        self.VAlignSlider.setTickInterval(20)
        self.optionLayout.addWidget(self.VAlignSlider, 3, 3, 1, 4)
        self.VAlignSlider.setOrientation(Qt.Horizontal)
        self.VAlignLabel = QLabel('竖直偏移')
        self.optionLayout.addWidget(self.VAlignLabel, 3, 7, 1, 1)

    def getFont(self):
        status, font = QFontDialog.getFont()
        if status:
            self.font = QFontInfo(font)
            self.fontName = self.font.family()
            self.fontSize = self.font.pointSize()
            self.fontBold = self.font.bold()
            self.fontItalic = self.font.italic()
            fontBold = '粗体' if self.fontBold else ''
            fontItalic = '斜体' if self.fontItalic else ''
            self.fontSelect.setText('%s %s号 %s %s' % (self.fontName, self.fontSize, fontBold, fontItalic))

    def getFontColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.fontColor = color.name()
            self.fontColorSelect.setText(self.fontColor)
            self.fontColorSelect.setStyleSheet('background-color:%s;color:%s' % (self.fontColor, self.colorReverse(self.fontColor)))

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

        super().__init__()
        self.setWindowTitle('字幕合成')
        self.resize(1400, 600)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.preview = QLabel('效果预览')
        self.layout.addWidget(self.preview, 0, 0, 6, 10)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("QLabel{background:white;}")

        self.option = QTabWidget()
        self.option.setFixedWidth(360)
        self.layout.addWidget(self.option, 0, 10, 3, 1)
        self.subDict = {x: fontWidget(x * 10 + 10) for x in range(1, 6)}
        for x, tabPage in self.subDict.items():
            self.option.addTab(tabPage, '字幕 %s' % x)

        self.startGrid = QWidget()
        self.layout.addWidget(self.startGrid, 3, 10, 2, 1)
        self.startLayout = QGridLayout()
        self.startGrid.setLayout(self.startLayout)
        self.sub1Check = QCheckBox('字幕 1')
        self.sub2Check = QCheckBox('字幕 2')
        self.sub3Check = QCheckBox('字幕 3')
        self.sub4Check = QCheckBox('字幕 4')
        self.sub5Check = QCheckBox('字幕 5')
        self.subCheckList = [self.sub1Check, self.sub2Check, self.sub3Check, self.sub4Check, self.sub5Check]
        self.startLayout.addWidget(self.sub1Check, 0, 0, 1, 1)
        self.startLayout.addWidget(self.sub2Check, 0, 1, 1, 1)
        self.startLayout.addWidget(self.sub3Check, 0, 2, 1, 1)
        self.startLayout.addWidget(self.sub4Check, 0, 3, 1, 1)
        self.startLayout.addWidget(self.sub5Check, 0, 4, 1, 1)
        self.startLayout.addWidget(QLabel('编码器：'), 1, 0, 1, 1)
        self.decodeSelect = QComboBox()
        self.decodeSelect.addItems(['CPU', 'GPU'])
        self.decodeSelect.setCurrentIndex(0)
        self.startLayout.addWidget(self.decodeSelect, 1, 1, 1, 1)
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
        self.processBar.setFixedWidth(350)
        self.layout.addWidget(self.processBar, 5, 10, 1, 1)

    def generatePreview(self):
        subList = []
        for cnt, subCheck in enumerate(self.subCheckList):
            if subCheck.isChecked():
                subList.append(self.subDict[cnt + 1])
        decodeArgs = {}
        for subNumber, font in enumerate(subList):
            decodeArgs[subNumber] = [font.fontName, font.fontSize, font.fontBold, font.fontItalic, font.fontColor,
                                     font.outlineSizeBox.currentIndex(), font.outlineColor,
                                     font.shadowSizeBox.currentIndex(), font.shadowColor,
                                     font.align.currentIndex(), font.VAlignSlider.value()]
        print(decodeArgs)
