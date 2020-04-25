# DD烤肉机
一个给烤肉man使用的轻量级辅助烤肉打轴压制软件

# 它可以做什么？
从油管抓源-翻译打轴校对-压制视频 一条龙服务 不用再下载N个软件 而且完全免费开源

# 它有什么特色？
* 简洁友好的操作界面
  * 视频和字幕轨道同步预览 方便烤肉校对
  * 注：若出现视频无法播放的情况 请安装目录里提供的LAV解码器 即可正常播放
![image](https://github.com/jiafangjun/DD_KaoRou/blob/master/images/主界面.jpg)

* 自带一个油管下载器 可同时下载各种分辨率的视频/音频 以及油管自动识别的日语字幕轨道和封面
  * 注：油管自动翻译的中文轨道也可以抓取 但翻译质量实在拉胯。。并不推荐使用
  * 油管下载库基于youtube-dl开源项目
![image](https://github.com/jiafangjun/DD_KaoRou/blob/master/images/油管下载器.jpg)

* 采用固定时间间隔的方式来打轴 省下手动打轴的精力 拯救轴man。
  * 目前有100ms 200ms 500ms 1s四种间隔预设可选（注：间隔越短的话 更改时轴的操作所花费的时间越长）
  * 预览字幕的样式也可以做简单的调整 但最终效果要到合成视频的页面下预览
![image](https://github.com/jiafangjun/DD_KaoRou/blob/master/images/烤肉打轴预览样式.jpg)

* 从菜单栏打开合成视频界面 可调整预览字幕样式效果 以及视频压制参数调整 然后合成视频
  * 五条字幕轨道的样式单独分开调整 可同时压进一个视频里
  * 视频压制基于FFMpeg 字幕采用ASS格式 也可选择单独导出字幕到本地 然后自己手动合成
![image](https://github.com/jiafangjun/DD_KaoRou/blob/master/images/合成视频.jpg)

在此特别感谢本项目所使用到的以下开源项目：
* https://github.com/ytdl-org/youtube-dl
* https://wiki.qt.io/Qt_for_Python
* https://github.com/FFmpeg/FFmpeg
