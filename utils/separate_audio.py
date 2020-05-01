#!/usr/bin/python3
# -*- coding: utf-8 -*-

import psutil
import subprocess
import numpy as np
# from matplotlib import pyplot as plt
from spleeter.separator import Separator
from spleeter.audio.adapter import get_default_audio_adapter
from PySide2.QtWidgets import QGridLayout, QDialog, QPushButton, QProgressBar, QLabel, QComboBox,\
    QLineEdit
from PySide2.QtCore import QTimer, Signal, QThread
from PySide2.QtGui import QIntValidator


class separateQThread(QThread):
    position = Signal(int)
    percent = Signal(float)
    voiceList = Signal(list)
    avgList = Signal(list)
    finish = Signal(bool)

    def __init__(self, videoPath, duration, before, after, multiThread, parent=None):
        super(separateQThread, self).__init__(parent)
        self.videoPath = videoPath
        self.duration = duration
        self.beforeCnt = int(before) // 20
        self.afterCnt = int(after) // 20
        self.separate = Separator('spleeter:2stems', stft_backend='tensorflow', multiprocess=multiThread)
        self.audioLoader = get_default_audio_adapter()

    def run(self):
        cuts = self.duration // 60000 + 1
        for cut in range(cuts):
            cmd = ['utils/ffmpeg.exe', '-y', '-i', self.videoPath, '-vn', '-ss', str(cut * 60), '-t', '60', 'temp_audio.m4a']
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            for line in p.stdout.readlines():
                try:
                    line = line.decode('gb18030', 'ignore')
                    if 'Audio:' in line:
                        break
                except:
                    pass
            for hz in line.split(','):
                if 'Hz' in hz:
                    hz = int(hz.split('Hz')[0])
                    break
            hz20 = hz // 50  # 20ms
            waveform, _ = self.audioLoader.load('temp_audio.m4a')
            prediction = self.separate.separate(waveform)
            msList = []
            varList = []
            voiceList = []
            avgList = []
            for cnt, l in enumerate(prediction['vocals']):  # 只提取人声键值
                for i in l:
                    msList.append(i)
                if not cnt % hz20:  # 每20ms取一次方差
                    varList.append(np.var(msList))  # 每20ms内的方差值
                    avgList.append(np.mean(msList))  # 每20ms内的平均值
                    msList = []
            med = np.median(varList)  # 1分钟内所有方差中位数
            cnt = self.beforeCnt  # 用户设置打轴前侧预留时间  / 20ms的次数
            start = 0  # 人声开始时间
            end = 0  # 人声结束时间
            avgVarList = []  # 平滑方差值
            for varCnt in range(len(varList) - 5):
                avgVarList.append(np.mean(varList[varCnt:varCnt + 5]))  # 方差值+后四位一起取平均
            avgVarList += varList[-4:]  # 补上最后四个没计算的方差值
            while cnt < len(avgVarList) - self.afterCnt:  # 开始判断人声区域
                if avgVarList[cnt] >= med:  # 平均方差值超过1分钟内方差中位数
                    start = cut * 60000 + (cnt - self.beforeCnt) * 20  # 开始时间为当前时间-用户前侧留白时间
                    cnt += self.afterCnt  # 向后延伸用户后侧留白时间
                    if cnt < len(avgVarList):  # 没超出一分钟则开始往后查询
                        finishToken = False
                        while not finishToken:
                            try:  # 查询超出长度一律跳出循环
                                while avgVarList[cnt] >= med:  # 向后查询至平均方差值<中位数
                                    cnt += 1
                                cnt += self.afterCnt  # 补一次用户留白时间后再次判断平均方差值<中位数 是则通过
                                if avgVarList[cnt] < med:
                                    finishToken = True
                            except:
                                break
                    end = cut * 60000 + cnt * 20  # 结束时间即结束向后查询的时间
                    voiceList.append([start, end])  # 添加起止时间给信号槽发送
                else:
                    cnt += 1  # 没检测到人声则+1
            self.position.emit(cut + 1)
            self.percent.emit((cut + 1) / cuts * 100)
            self.voiceList.emit(voiceList)
            self.avgList.emit(avgList)
#             plt.subplot(311)
#             plt.plot([x for x in range(len(avgList))], avgList)
#             plt.subplot(312)
#             plt.plot([x for x in range(len(avgVarList))], avgVarList)
#             plt.axhline(med, label='median')
#             plt.subplot(313) 
#             x = []
#             y = []
#             modifyVoice = []
#             for l in voiceList:
#                 modifyVoice += l
#             trig = False
#             for i in range(self.duration):
#                 for l in modifyVoice:
#                     if i > l:
#                         trig = not trig
#                 x.append(i)
#                 if not trig:
#                     y.append(0)
#                 else:
#                     y.append(1)
#             plt.plot(x, y)
#             plt.legend()
#             plt.show()
        self.finish.emit(True)


class Separate(QDialog):
    videoPath = ''
    duration = 60000
    processToken = False
    voiceList = Signal(list)
    avgList = Signal(list)
    clrSep = Signal()
    tablePreset = Signal(list)
    autoFillToken = True
    autoSpanToken = True
    multipleThread = True


    def __init__(self):
        super().__init__()
        self.resize(800, 150)
        self.setWindowTitle('AI智能打轴 (测试版)')
        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel('前侧留白(ms)'), 0, 0, 1, 1)
        self.beforeEdit = QLineEdit('20')
        validator = QIntValidator()
        validator.setRange(0, 5000)
        self.beforeEdit.setValidator(validator)
        self.beforeEdit.setFixedWidth(50)
        layout.addWidget(self.beforeEdit, 0, 1, 1, 1)
        layout.addWidget(QLabel(''), 0, 2, 1, 1)
        layout.addWidget(QLabel('后侧留白(ms)'), 0, 3, 1, 1)
        self.afterEdit = QLineEdit('300')
        self.afterEdit.setValidator(validator)
        self.afterEdit.setFixedWidth(50)
        layout.addWidget(self.afterEdit, 0, 4, 1, 1)
        layout.addWidget(QLabel(''), 0, 5, 1, 1)
        self.autoFill = QPushButton('填充字符')
        self.autoFill.setStyleSheet('background-color:#3daee9')
        self.autoFill.clicked.connect(self.setAutoFill)
        layout.addWidget(self.autoFill, 0, 6, 1, 1)
        self.fillWord = QLineEdit('#AI自动识别#')
        layout.addWidget(self.fillWord, 0, 7, 1, 1)
        layout.addWidget(QLabel(''), 0, 8, 1, 1)
        self.autoSpan = QPushButton('自动合并')
        self.autoSpan.setStyleSheet('background-color:#3daee9')
        self.autoSpan.clicked.connect(self.setAutoSpan)
        layout.addWidget(self.autoSpan, 0, 9, 1, 1)
        self.multiCheck = QPushButton('启用多进程')
        self.multiCheck.setStyleSheet('background-color:#3daee9')
        self.multiCheck.clicked.connect(self.setMultipleThread)
        layout.addWidget(self.multiCheck, 0, 10, 1, 1)
        self.processBar = QProgressBar()
        layout.addWidget(self.processBar, 1, 0, 1, 10)
        self.checkButton = QPushButton('开始')
        self.checkButton.setFixedWidth(100)
        self.checkButton.clicked.connect(self.separateProcess)
        layout.addWidget(self.checkButton, 1, 10, 1, 1)

    def setDefault(self, videoPath, duration):
        self.videoPath = videoPath
        self.duration = duration

    def separateProcess(self):
        self.processToken = not self.processToken
        if self.videoPath:
            if self.processToken:
                self.processBar.setValue(0)
                self.checkButton.setText('初始化中')
                if not self.beforeEdit.text():
                    self.beforeEdit.setText('0')
                before = self.beforeEdit.text()
                if not self.afterEdit.text():
                    self.afterEdit.setText('0')
                after = self.afterEdit.text()
                if self.autoFillToken:
                    try:
                        fillWord = self.fillWord.text()
                    except:
                        fillWord = ''
                else:
                    fillWord = ''
                self.sepProc = separateQThread(self.videoPath, self.duration, before, after, self.multipleThread)
                self.clrSep.emit()  # 清空第一条字幕轴
                self.sepProc.position.connect(self.setTitle)  # 设置标题分析至第几分钟
                self.sepProc.percent.connect(self.setProgressBar)  # 设置滚动条进度
                self.sepProc.voiceList.connect(self.sendVoiceList)  # 二次传球给主界面标记表格
                self.sepProc.avgList.connect(self.sendAvgList)  # 平均音频响度 预留给后面画音频图
                self.tablePreset.emit([fillWord, self.autoSpanToken]) # 自动填充 填充文本 自动合并
                self.sepProc.finish.connect(self.sepFinished)
                self.sepProc.start()
            else:
                self.setWindowTitle('AI智能打轴 (测试版)')
                self.processBar.setValue(0)
                self.checkButton.setText('开始')
                self.checkButton.setStyleSheet('background-color:#31363b')
#                 self.sepProc.separate._pool.terminate()
#                 try:
#                     p = psutil.Process(self.sepProc.p.pid)
#                     for proc in p.children(True):
#                         proc.kill()
#                 except:
#                     pass
                self.sepProc.terminate()
                self.sepProc.quit()
                self.sepProc.wait()

    def setTitle(self, pos):
        self.setWindowTitle('AI智能打轴 (已分析至第%s分钟)' % pos)

    def setProgressBar(self, percent):
        self.checkButton.setText('停止')
        self.checkButton.setStyleSheet('background-color:#3daee9')
        self.processBar.setValue(percent)

    def sendVoiceList(self, voiceList):
        self.voiceList.emit(voiceList)

    def sendAvgList(self, avgList):
        self.avgList.emit(avgList)

    def sepFinished(self, result):
        if result:
            self.processToken = not self.processToken
            self.setWindowTitle('AI智能打轴 (测试版)')
            self.processBar.setValue(100)
            self.checkButton.setText('开始')
            self.checkButton.setStyleSheet('background-color:#31363b')
#             self.sepProc.separate._pool.terminate()
#             try:
#                 p = psutil.Process(self.sepProc.p.pid)
#                 for proc in p.children(True):
#                     proc.kill()
#             except:
#                 pass
            self.sepProc.terminate()
            self.sepProc.quit()
            self.sepProc.wait()

    def setAutoFill(self):
        self.autoFillToken = not self.autoFillToken
        if self.autoFillToken:
            self.autoFill.setStyleSheet('background-color:#3daee9')
            self.fillWord.setEnabled(True)
        else:
            self.autoFill.setStyleSheet('background-color:#31363b')
            self.fillWord.setEnabled(False)

    def setAutoSpan(self):
        self.autoSpanToken = not self.autoSpanToken
        if self.autoSpanToken:
            self.autoSpan.setStyleSheet('background-color:#3daee9')
        else:
            self.autoSpan.setStyleSheet('background-color:#31363b')

    def setMultipleThread(self):
        self.multipleThread = not self.multipleThread
        if self.multipleThread:
            self.multiCheck.setStyleSheet('background-color:#3daee9')
        else:
            self.multiCheck.setStyleSheet('background-color:#31363b')
