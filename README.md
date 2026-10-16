# 二维码速取 | QR Screen

**中文** | [English](#english)

Windows 桌面小工具：框选屏幕上的二维码，识别内容后自动复制到剪贴板。单个结果为 HTTP/HTTPS 链接时，也可以从窗口中打开。

## 功能

- 框选屏幕区域，识别其中的二维码
- 自动复制识别结果到剪贴板
- 一键打开识别出的 HTTP/HTTPS 链接

## 环境要求

- Windows 10 或更新版本
- Python 3.10 或更新版本

## 安装与运行

安装 Python 3.10 或更新版本后，在项目目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

点击“框选并识别”，在屏幕上拖动鼠标框出二维码。识别成功后，结果会显示在窗口中并自动复制到剪贴板。

## 运行测试

```powershell
python main.py --self-test
```

## 技术与依赖

二维码检测和解码由 OpenCV 提供；界面使用 Tkinter，剪贴板与屏幕区域截图使用 Python 标准库及 Windows API。

---

## English

QR Screen is a lightweight Windows desktop utility that lets you select an area of your screen, decode QR codes, and automatically copy the results to your clipboard. You can also open a decoded HTTP/HTTPS link directly from the app.

### Features

- Select an area of the screen to scan for QR codes
- Automatically copy decoded results to the clipboard
- Open decoded HTTP/HTTPS links with one click

### Requirements

- Windows 10 or later
- Python 3.10 or later

### Install and run

Open PowerShell in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Click **框选并识别** (“Select and scan”), then drag to select the QR code on your screen. The decoded result appears in the window and is copied to the clipboard automatically.

### Run the decoder self-test

```powershell
python main.py --self-test
```

### Technology and dependencies

QR detection and decoding are powered by OpenCV. The UI uses Tkinter, and clipboard access and screen capture use the Python standard library and Windows APIs.
