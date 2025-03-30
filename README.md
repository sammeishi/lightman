## 莱特曼 **Lightman**

针对视频号的视频分析工具。

取自《别对我说谎》的男主角 Cal Lightman. 寓意能看穿一切。



## 运行环境

*并没有使用conda，ubuntu下直装*

| 依赖项 | 版本  | 说明                                               |
| ------ | ----- | -------------------------------------------------- |
| ubuntu | 20.04 | windows下安装whisper会失败                         |
| wsl    | 2     | 非必选。windows下跑ubuntu用的                      |
| python | 3.9   | ubuntu默认自带python3.8，重装并覆盖默认python的bin |
| ffmpeg | 4.2.7 | 转换输入视频                                       |
|        |       |                                                    |
|        |       |                                                    |



## 安装流程

wsl的ubuntu自动安装了，查看nvidia-smi是否正常

```bash
nvidia-smi
```

pip安装所有依赖

```bash
# 需要注意默认pip是否pip3命令
# 如果有bug请参见下面问题QA
pip install -r requirements.txt
```

安装cudnn,根据nvidia-smi输出安装配套的版本

```bash
# 使用的网络安装
# 安装地址 https://developer.nvidia.com/rdp/cudnn-download
# 需要FQ
```



## 安装问题

Q: pip安装requirements.txt报错could not find a version that satisfies the requirement xxx...

A: pip版本错误导致的。ubuntu下独立安装pip(非conda)，默认的pip并不是pip3版本，请使用pip3 install或者链接pip3为默认的pip

Q: error: uninstall-distutils-installed-package Cannot uninstall PyYAML 5.3.1

A: PyYAML 是通过系统包管理器（如 apt）安装的，而 pip 无法安全卸载系统级安装的包.卸载系统自带即可：sudo apt remove python3-yaml



## 整体架构

1. stt 语音转文字 不切割直接转使用faster-whisper
1. 

## 执行

```bash
python main.py --vd /mnt/c/users/sam/desktop/lightman/piwei1
```

