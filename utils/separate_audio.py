#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, subprocess, wave, time
import numpy as np
from spleeter.separator import Separator
from spleeter.audio.adapter import get_default_audio_adapter
from PySide2.QtWidgets import QGridLayout, QDialog, QPushButton, QProgressBar, QLabel, QComboBox,\
    QLineEdit
from PySide2.QtCore import QTimer, Signal, QThread
from PySide2.QtGui import QIntValidator


def getWave(audioPath):
    f = wave.open(audioPath, 'rb')  # 开始分析波形
    params = f.getparams()
    nchannels, _, framerate, nframes = params[:4]
    strData = f.readframes(nframes)
    f.close()
    w = np.fromstring(strData, dtype=np.int16)
    w = np.reshape(w, [nframes, nchannels])
    _time = [x * 1000 / framerate for x in range(0, nframes)]
    return _time, list(w[:, 0])


class sepMainAudio(QThread):
    mainAudioWave = Signal(list, list)

    def __init__(self, videoPath, duration):
        super().__init__()
        self.videoPath = videoPath
        self.duration = duration

    def run(self):
        if os.path.exists('temp_audio'):  # 创建和清空temp_audio文件夹
            try:
                for i in os.listdir('temp_audio'):
                    os.remove(r'temp_audio\%s' % i)
            except:
                pass
        else:
            os.mkdir('temp_audio')
        timeStamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
        wavePath = r'temp_audio\main_audio_%s.wav' % timeStamp
        cmd = ['utils/ffmpeg.exe', '-y', '-i', self.videoPath, '-vn', '-ar', '1000', wavePath]
        p = subprocess.Popen(cmd)
        p.wait()
        _time, _wave = getWave(wavePath)
        self.mainAudioWave.emit(_time, _wave)  # 发送主音频波形
        os.remove(wavePath)  # 删除wav文件  太大了


class separateQThread(QThread):
    position = Signal(int)
    percent = Signal(float)
    voiceList = Signal(list)
    voiceWave = Signal(list, list)
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
            audioPath = 'temp_audio.m4a'
            cmd = ['utils/ffmpeg.exe', '-y', '-i', self.videoPath, '-vn', '-ss', str(cut * 60), '-t', '60', audioPath]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            for line in p.stdout.readlines():
                try:
                    line = line.decode('gb18030', 'ignore')
                    if 'Audio:' in line:
                        break
                except:
                    pass
            try:
                line = line.lower()
                for hz in line.split(','):
                    if 'hz' in hz:
                        hz = int(hz.split('hz')[0])
                        break
            except:
                hz = 44100
            self.separate.separate_to_file(audioPath, '.\\', codec='wav', bitrate='1k')  # 分离人声音轨
            wavePath = r'temp_audio\vocals_%s.wav' % cut
            cmd = ['utils/ffmpeg.exe', '-y', '-i', r'temp_audio\vocals.wav', '-vn', '-ar', '1000', wavePath]  # 用ffmpeg再降一次采样
            p = subprocess.Popen(cmd)
            p.wait()
            _time, _wave = getWave(wavePath)  # 发送人声波形
            self.voiceWave.emit(_time, _wave)

            # AI识别部分
            waveform, _ = self.audioLoader.load(audioPath, sample_rate=hz)  # 加载音频
            prediction = self.separate.separate(waveform)  # 核心部分 调用spleeter分离音频
            msList = []
            varList = []
            voiceList = []
            hz20 = hz // 50  # 20ms
            for cnt, l in enumerate(prediction['vocals']):  # 只提取人声键值
                for i in l:
                    msList.append(i)
                if not cnt % hz20:  # 每20ms取一次方差
                    varList.append(np.var(msList))  # 每20ms内的方差值
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
                if avgVarList[cnt] >= med and avgVarList[cnt] >= 0.0001:  # 平均方差值超过1分钟内方差中位数
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
                    voiceList.append([start, end - start])  # 添加起止时间给信号槽发送
                else:
                    cnt += 1  # 没检测到人声则+1
            self.position.emit(cut + 1)
            self.percent.emit((cut + 1) / cuts * 100)
            self.voiceList.emit(voiceList)
        self.finish.emit(True)


class Separate(QDialog):
    videoPath = ''
    duration = 60000
    processToken = False
    voiceList = Signal(list)
    voiceWave = Signal(list, list)
    tablePreset = Signal(list)
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
        layout.addWidget(QLabel('填充字符'), 0, 6, 1, 1)
        self.fillWord = QLineEdit('#AI自动识别#')
        layout.addWidget(self.fillWord, 0, 7, 1, 1)
        layout.addWidget(QLabel(''), 0, 8, 1, 1)
        self.outputIndex = QComboBox()
        self.outputIndex.addItems(['输出至第%s列' % i for i in range(1, 6)])
        layout.addWidget(self.outputIndex, 0, 9, 1, 1)
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
                try:
                    fillWord = self.fillWord.text()
                except:
                    fillWord = ' '
                index = self.outputIndex.currentIndex()
                self.sepProc = separateQThread(self.videoPath, self.duration, before, after, self.multipleThread)
                self.sepProc.position.connect(self.setTitle)  # 设置标题分析至第几分钟
                self.sepProc.percent.connect(self.setProgressBar)  # 设置滚动条进度
                self.sepProc.voiceList.connect(self.sendVoiceList)  # 二次传球给主界面标记表格
                self.sepProc.voiceWave.connect(self.sendVoiceWave)  # 二次传球给主界面绘制人声音频图
                self.tablePreset.emit([fillWord, index]) # 填充文本 输出列
                self.sepProc.finish.connect(self.sepFinished)
                self.sepProc.start()
            else:
                self.setWindowTitle('AI智能打轴 (测试版)')
                self.processBar.setValue(0)
                self.checkButton.setText('开始')
                self.checkButton.setStyleSheet('background-color:#31363b')
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

    def sendVoiceWave(self, x, y):
        self.voiceWave.emit(x, y)

    def sepFinished(self, result):
        if result:
            self.processToken = not self.processToken
            self.setWindowTitle('AI智能打轴 (测试版)')
            self.processBar.setValue(100)
            self.checkButton.setText('开始')
            self.checkButton.setStyleSheet('background-color:#31363b')
            self.sepProc.terminate()
            self.sepProc.quit()
            self.sepProc.wait()

    def setMultipleThread(self):
        self.multipleThread = not self.multipleThread
        if self.multipleThread:
            self.multiCheck.setStyleSheet('background-color:#3daee9')
        else:
            self.multiCheck.setStyleSheet('background-color:#31363b')
