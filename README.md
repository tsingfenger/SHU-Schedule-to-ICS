## 简介

这个工具能够获取教务系统的课表信息生成ics日历文件。

可将将此文件导入到手机/电脑/平板的日历软件和第三方课表app中。

## 开始使用

### 1.一键启动

你可以下载releases中已经打包好的exe文件，双击运行即可。

程序会在程序运行目录下生成ics文件。

### 2.使用源码

#### 前提

确保你的系统已经安装了Python 3.x。你可以通过在终端运行`python --version`来检查Python版本。

#### 使用

1. 克隆本仓库到本地

2. 项目目录下使用`pip install -r requirements.txt` 安装项目所需依赖

3.  `python main.py`  启动程序

	程序会在程序运行目录下生成ics文件

## 提醒

请认真检查生成的日历文件，防止漏课