## Lightman

针对视频号的视频分析工具。

取自《别对我说谎》的男主角 Cal Lightman. 寓意能看穿一切。

### 运行环境

| 依赖项 | 版本   | 说明                                                    |
| ------ | ------ | ------------------------------------------------------- |
| ubuntu | 20.04  | windows下安装whisper会失败                              |
| wsl    | 2      | 非必选。windows下跑ubuntu用的                           |
| conda  | 24.9.2 | 必须使用conda，避免ubuntu自带python版本错乱无法覆盖问题 |
| python | 3.9    | ubuntu默认自带python，有点混乱直接使用conda             |
| ffmpeg | 4.2.7  | 转换输入视频                                            |
|        |        |                                                         |



### 包管理

由于依赖的第三方库如(faster_whisper),他们的包管理各色各样，因此本项目纯手工导requirements.txt + pip 进行依赖管理. 不使用任何包管理如uv,Poetry等。

使用pipreqs精准导出依赖包，而不是全部。否则公用一个python的wsl会导致导出很多无用包

```bash
# 安装pipreqs
pip install pipreqs
# 只导出当前项目import的包
pipreqs ./ --encoding=utf8 --force
```

### 安装流程

wsl的ubuntu自动安装了，查看nvidia-smi是否正常

```bash
# 记住CUDA版本号 后面cuDNN需要匹配
nvidia-smi
```

安装conda

```bash
# 网上搜下
```

pip安装所有依赖

```bash
# 需要注意默认pip是否pip3命令
# 如果有bug请参见下面问题QA
pip install -r requirements.txt
```

(可选)安装ffpmeg

```bash
# 如果报错 Permission denied: 'ffprobe'
# apt安装ffpmeg即可
sudo apt install ffmpeg
```

安装cudnn,根据nvidia-smi输出安装配套的版本

```bash
# 使用在线版安装（非local）
# 安装地址 https://developer.nvidia.com/rdp/cudnn-download
# 需要FQ
```



### 安装问题

Q: pip安装requirements.txt报错could not find a version that satisfies the requirement xxx...

A: pip版本错误导致的。ubuntu下独立安装pip(非conda)，默认的pip并不是pip3版本，请使用pip3 install或者链接pip3为默认的pip

Q: error: uninstall-distutils-installed-package Cannot uninstall PyYAML 5.3.1

A: PyYAML 是通过系统包管理器（如 apt）安装的，而 pip 无法安全卸载系统级安装的包.卸载系统自带即可：sudo apt remove python3-yaml



### 执行命令

```bash
python main.py --vd /mnt/c/users/sam/desktop/lightman/piwei1
```



### 开发与测试

```bash
# 使用unittest执行测试文件
# 使用py直接运行会报错无法加载src目录内的文件
# unittest不用pip install
python -m unittest tests/llm_test.py
```

