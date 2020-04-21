#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import time
import shutil
import subprocess
from PySide2.QtWidgets import QGridLayout, QFileDialog, QDialog, QPushButton,\
        QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QProgressBar, QLabel
from PySide2.QtCore import QTimer, Signal, QThread


class dnldThread(QThread):
    downloading = Signal(str)
    percent = Signal(str)
    done = Signal(str)

    def __init__(self, dnldNum, videoType, resolution, savePath, title, args, url, parent=None):
        super(dnldThread, self).__init__(parent)
        self.dnldNum = dnldNum
        self.videoType = videoType
        self.resolution = resolution
        self.savePath = savePath.replace('/', '\\')
        if not os.path.isdir(self.savePath):
            self.savePath = os.path.split(self.savePath)[0]
        self.title = title
        self.args = args
        self.url = url

    def run(self):
        for cnt, num in enumerate(self.dnldNum):
            modifyName = '%s_%s_%s.%s' % (self.title, num, self.resolution[cnt], self.videoType[cnt])
            outputPath = os.path.join(self.savePath, modifyName)
            if not os.path.exists(outputPath):
                self.downloading.emit(outputPath)
                cmd = ['youtube-dl.exe', '-f', num]
                if not cnt:
                    cmd += self.args
                cmd.append(self.url)
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                while p.poll() is None:
                    line = p.stdout.read(100).decode('utf8', 'ignore')
                    self.percent.emit(line)
                    time.sleep(1)
                _id = self.url.split('?v=')[1]
                if self.savePath != os.getcwd():
                    for f in os.listdir(os.getcwd()):
                        if _id in f and 'part' not in f:
                            if '.vtt' in f or '.srt' in f or '.jpg' in f:
                                if os.path.exists(os.path.join(self.savePath, f)):
                                    os.remove(f)
                                else:
                                    shutil.move(f, self.savePath)
                            else:
                                if os.path.exists(os.path.join(self.savePath, f)):
                                    os.remove(f)
                                else:
                                    shutil.move(f, outputPath)
                else:
                    for f in os.listdir(os.getcwd()):
                        if _id in f and 'part' not in f and '.vtt' not in f and '.srt' not in f:
                            if os.path.exists(modifyName):
                                os.remove(f)
                            else:
                                os.rename(f, modifyName)
                self.done.emit('下载完成')
            else:
                self.done.emit('文件已存在')


class dnldCheck(QThread):
    searchCnt = Signal(int)
    checkStatus = Signal(bool)
    videoTitle = Signal(str)
    videoResults = Signal(list)

    def __init__(self, url, parent=None):
        super(dnldCheck, self).__init__(parent)
        self.url = url

    def run(self):
        cnt = 0
        p = subprocess.Popen(['youtube-dl.exe', '-e', self.url], stdout=subprocess.PIPE)
        while not p.poll() in [0, 1]:
            cnt += 1
            self.searchCnt.emit(cnt % 3 + 1)
            time.sleep(0.3)
            pass
        if p.poll():
            self.checkStatus.emit(False)
            self.searchCnt.emit(0)
        else:
            self.checkStatus.emit(True)
            title = p.stdout.read().decode('gb18030').strip().replace('/', '_')
            self.videoTitle.emit(title)
            p = subprocess.Popen(['youtube-dl.exe', '-F', self.url], stdout=subprocess.PIPE)
            while not p.poll() in [0, 1]:
                cnt += 1
                self.searchCnt.emit(cnt % 3 + 1)
                time.sleep(0.3)
                pass
            results = p.stdout.read().decode().split('\n')
            self.videoResults.emit(results[::-1])
            self.searchCnt.emit(0)


class YoutubeDnld(QDialog):
    def __init__(self):
        super().__init__()
        self.downloadName = ''
        self.downloadPercent = ''
        self.downloadSpeed = ''
        self.setWindowTitle('Youtube下载器 （此窗口可关闭至后台下载 支持断点下载 需要自备梯子）')
        self.resize(1000, 600)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tipLabel = QLabel('Youtube链接：')
        self.layout.addWidget(self.tipLabel, 0, 0, 1, 2)
        self.urlInput = QLineEdit()
        self.layout.addWidget(self.urlInput, 0, 1, 1, 6)
        self.searchButton = QPushButton('检查')
        self.searchButton.clicked.connect(self.checkURL)
        self.layout.addWidget(self.searchButton, 0, 7, 1, 1)
        self.searchToken = False
        self.videoInfo = QTableWidget()
        self.videoInfo.verticalHeader().setHidden(True)
        self.videoInfo.setRowCount(10)
        self.videoInfo.setColumnCount(6)
        self.videoInfo.setColumnWidth(0, 100)
        self.videoInfo.setColumnWidth(1, 100)
        self.videoInfo.setColumnWidth(2, 100)
        self.videoInfo.setColumnWidth(3, 100)
        self.videoInfo.setColumnWidth(4, 100)
        self.videoInfo.setColumnWidth(5, 450)
        self.videoInfo.setHorizontalHeaderLabels(['序号', '后缀名', '分辨率', '码率', '类型', '备注'])
        self.layout.addWidget(self.videoInfo, 1, 0, 4, 8)
        self.dnldInput = QLineEdit()
        self.layout.addWidget(self.dnldInput, 5, 0, 1, 2)
        self.dnldLabel = QLabel('输入要下载的视频序号，多个序号用空格隔开    ')
        self.layout.addWidget(self.dnldLabel, 5, 2, 1, 2)
        self.jaCheck = QCheckBox('下载日语字幕(自动识别)')
        self.jaCheck.setChecked(True)
        self.layout.addWidget(self.jaCheck, 5, 4, 1, 1)
        self.zhCheck = QCheckBox('下载中文字幕(油管机翻)')
        self.zhCheck.setChecked(True)
        self.layout.addWidget(self.zhCheck, 5, 5, 1, 1)
        self.thumbnailCheck = QCheckBox('下载封面')
        self.thumbnailCheck.setChecked(True)
        self.layout.addWidget(self.thumbnailCheck, 5, 6, 1, 1)
        self.savePath = QLineEdit()
        self.layout.addWidget(self.savePath, 6, 0, 1, 4)
        self.saveButton = QPushButton('保存路径')
        self.saveButton.setFixedWidth(115)
        self.saveButton.clicked.connect(self.setSavePath)
        self.layout.addWidget(self.saveButton, 6, 4, 1, 1)
        self.processInfo = QLabel()
        self.layout.addWidget(self.processInfo, 6, 5, 1, 2)
        self.progress = QProgressBar()
        self.layout.addWidget(self.progress, 7, 0, 1, 7)
        self.startButton = QPushButton('开始下载')
        self.startButton.setFixedWidth(140)
        self.startButton.setFixedHeight(54)
        self.startButton.setEnabled(False)
        self.startButton.clicked.connect(self.dnldStart)
        self.layout.addWidget(self.startButton, 6, 7, 2, 1)
        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.start()
        self.timer.timeout.connect(self.dnldProgress)

    def checkURL(self):
        self.url = self.urlInput.text()
        if self.url:
            if '&' in self.url:
                self.url = self.url.split('&')[0]
            self.videoInfo.clearContents()
            self.dnldCheck = dnldCheck(self.url)
            self.dnldCheck.searchCnt.connect(self.refreshSearchButton)
            self.dnldCheck.checkStatus.connect(self.setCheckStatus)
            self.dnldCheck.videoTitle.connect(self.setTitle)
            self.dnldCheck.videoResults.connect(self.setVideoInfo)
            self.dnldCheck.start()

    def refreshSearchButton(self, cnt):
        if cnt:
            self.searchButton.setText('搜索中' + '.' * cnt)
        else:
            self.searchButton.setText('检查')

    def setCheckStatus(self, checkStatus):
        if not checkStatus:
            self.searchToken = False
            self.videoInfo.setItem(0, 5, QTableWidgetItem('无效的视频链接 请重新输入'))
        else:
            self.searchToken = True

    def setTitle(self, title):
        self.title = title
        self.urlInput.setText(title)

    def setVideoInfo(self, results):
        self.videoInfo.setRowCount(len(results) - 4)
        for y, l in enumerate(results[1:-3]):
            l = l.split(' ')
            while '' in l:
                l.remove('')
            if ',' in l:
                l.remove(',')
            if 'tiny' in l:
                l.remove('tiny')
            lineData = l[:2]
            if l[2] == 'audio':
                lineData.append('无')
            else:
                lineData.append('%s %s' % tuple(l[2:4]))
            lineData.append(l[4])
            tip = ''
            for i in l[4:]:
                tip += i + ' '
            if l[2] == 'audio':
                lineData.append('audio only')
            elif 'video only' in tip:
                lineData.append('video only')
            else:
                lineData.append('video + audio')
            lineData.append(tip[:-1])
            for x, data in enumerate(lineData):
                self.videoInfo.setItem(y, x, QTableWidgetItem(data))

    def setSavePath(self):
        savePath = QFileDialog.getExistingDirectory(self, '选择视频保存文件夹')
        if savePath:
            self.savePath.setText(savePath)

    def dnldProgress(self):
        if self.searchToken and self.dnldInput.text() and self.savePath.text():
            self.startButton.setEnabled(True)
        else:
            self.startButton.setEnabled(False)

    def dnldStart(self):
        self.processInfo.setText('下载速度：')
        dnldNum = self.dnldInput.text().split(' ')
        videoType = []
        resolution = []
        for num in dnldNum:
            for y in range(self.videoInfo.rowCount()):
                if self.videoInfo.item(y, 0).text() == num:
                    videoType.append(self.videoInfo.item(y, 1).text())
                    resolution.append(self.videoInfo.item(y, 2).text())
                    break
        savePath = self.savePath.text()
        ja = self.jaCheck.isChecked()
        zh = self.zhCheck.isChecked()
        if ja and zh:
            args = ['--write-auto-sub', '--sub-lang', 'ja,zh-Hans']
        elif ja and not zh:
            args = ['--write-auto-sub', '--sub-lang', 'ja']
        elif zh and not ja:
            args = ['--write-auto-sub', '--sub-lang', 'zh-Hans']
        else:
            args = []
        if self.thumbnailCheck.isChecked():
            args.append('--write-thumbnail')
        self.dnldThread = dnldThread(dnldNum, videoType, resolution, savePath, self.title, args, self.url)
        self.dnldThread.downloading.connect(self.dnldName)
        self.dnldThread.percent.connect(self.dnldPercent)
        self.dnldThread.done.connect(self.dnldFinish)
        self.dnldThread.start()

    def dnldName(self, name):
        self.savePath.setText(name)

    def dnldPercent(self, percent):
        if r'%' in percent:
            self.downloadPercent = percent.split(r'%')[0].split(' ')[-1]
        if 'B/s' in percent:
            self.downloadSpeed = percent.split('B/s')[0].split(' ')[-1] + 'B/s'
        self.processInfo.setText('下载速度：%s' % self.downloadSpeed)
        if self.downloadPercent:
            self.progress.setValue(float(self.downloadPercent))

    def dnldFinish(self, done):
        self.processInfo.setText(done)
        self.progress.setValue(0)
