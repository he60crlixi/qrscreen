# 二维码速取

Windows 桌面小工具：框选屏幕上的二维码，识别内容后自动复制到剪贴板。单个结果为 HTTP/HTTPS 链接时，也可以从窗口中打开。

## 环境要求

- Windows 10 或更新版本
- Python 3.10 或更新版本

## 运行

在项目目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

点击“框选并识别”，在屏幕上拖动鼠标框出二维码。识别成功后，结果会显示在窗口中并自动复制到剪贴板。

## 测试二维码解码

```powershell
python main.py --self-test
```

## 依赖

二维码检测和解码由 OpenCV 提供；界面、剪贴板和屏幕区域截图使用 Python 标准库及 Windows API。
