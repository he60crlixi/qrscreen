import ctypes
import os
import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from urllib.parse import urlparse

APP_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(APP_DIR, "deps"))

import cv2
import numpy as np

SRCCOPY = 0x00CC0020
CAPTUREBLT = 0x40000000
BI_RGB = 0
DIB_RGB_COLORS = 0
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79


class BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]


class RGBQuad(ctypes.Structure):
    _fields_ = [
        ("rgbBlue", ctypes.c_uint8),
        ("rgbGreen", ctypes.c_uint8),
        ("rgbRed", ctypes.c_uint8),
        ("rgbReserved", ctypes.c_uint8),
    ]


class BitmapInfo(ctypes.Structure):
    _fields_ = [("bmiHeader", BitmapInfoHeader), ("bmiColors", RGBQuad * 1)]


def capture_region(left, top, width, height):
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    user32.GetDC.argtypes = [ctypes.c_void_p]
    user32.GetDC.restype = ctypes.c_void_p
    user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.ReleaseDC.restype = ctypes.c_int
    gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
    gdi32.CreateCompatibleBitmap.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
    ]
    gdi32.CreateCompatibleBitmap.restype = ctypes.c_void_p
    gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    gdi32.SelectObject.restype = ctypes.c_void_p
    gdi32.BitBlt.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint32,
    ]
    gdi32.BitBlt.restype = ctypes.c_int
    gdi32.GetDIBits.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint,
    ]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
    gdi32.DeleteObject.restype = ctypes.c_int
    gdi32.DeleteDC.argtypes = [ctypes.c_void_p]
    gdi32.DeleteDC.restype = ctypes.c_int
    screen_dc = user32.GetDC(None)
    memory_dc = gdi32.CreateCompatibleDC(screen_dc)
    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    previous = gdi32.SelectObject(memory_dc, bitmap)
    try:
        if not gdi32.BitBlt(
            memory_dc,
            0,
            0,
            width,
            height,
            screen_dc,
            left,
            top,
            SRCCOPY | CAPTUREBLT,
        ):
            raise ctypes.WinError()

        info = BitmapInfo()
        info.bmiHeader = BitmapInfoHeader(
            ctypes.sizeof(BitmapInfoHeader),
            width,
            -height,
            1,
            32,
            BI_RGB,
            0,
            0,
            0,
            0,
            0,
        )
        pixels = (ctypes.c_uint8 * (width * height * 4))()
        if not gdi32.GetDIBits(
            memory_dc,
            bitmap,
            0,
            height,
            pixels,
            ctypes.byref(info),
            DIB_RGB_COLORS,
        ):
            raise ctypes.WinError()
        return np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 4)[
            :, :, :3
        ].copy()
    finally:
        gdi32.SelectObject(memory_dc, previous)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(None, screen_dc)


def decode_qr(image):
    detector = cv2.QRCodeDetector()
    found, values, _, _ = detector.detectAndDecodeMulti(image)
    decoded = [value for value in values if value] if found else []
    if not decoded:
        value, _, _ = detector.detectAndDecode(image)
        if value:
            decoded.append(value)
    return decoded


class QRUtility:
    def __init__(self, root):
        self.root = root
        self.root.title("二维码速取")
        self.root.geometry("600x390")
        self.root.minsize(520, 340)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        frame = ttk.Frame(root, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="框选屏幕上二维码所在区域，识别结果会自动复制到剪贴板。",
            wraplength=550,
        ).pack(anchor="w", pady=(0, 12))

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(0, 12))
        self.scan_button = ttk.Button(
            controls, text="框选并识别", command=self.begin_selection
        )
        self.scan_button.pack(side="left")
        self.copy_button = ttk.Button(
            controls, text="复制结果", command=self.copy_result, state="disabled"
        )
        self.copy_button.pack(side="left", padx=(8, 0))
        self.open_button = ttk.Button(
            controls, text="打开链接", command=self.open_link, state="disabled"
        )
        self.open_button.pack(side="left", padx=(8, 0))

        self.result = tk.Text(frame, height=10, wrap="word", undo=False)
        self.result.pack(fill="both", expand=True)
        self.status = tk.StringVar(value="就绪")
        ttk.Label(frame, textvariable=self.status).pack(anchor="w", pady=(8, 0))
        self.values = []

    def begin_selection(self):
        self.values = []
        self.copy_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        user32 = ctypes.windll.user32
        left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        self.root.withdraw()
        self.root.update_idletasks()

        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.attributes("-alpha", 0.25)
        overlay.geometry(f"{width}x{height}{left:+d}{top:+d}")
        canvas = tk.Canvas(
            overlay, cursor="crosshair", background="#222222", highlightthickness=0
        )
        canvas.pack(fill="both", expand=True)
        canvas.create_text(
            24,
            24,
            anchor="nw",
            text="拖动框选二维码区域，按 Esc 取消",
            fill="white",
            font=("Segoe UI", 16, "bold"),
        )
        selection = {"start": None, "rectangle": None}

        def on_press(event):
            selection["start"] = (event.x, event.y)
            if selection["rectangle"] is not None:
                canvas.delete(selection["rectangle"])
            selection["rectangle"] = canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline="#35e58a",
                width=3,
                fill="#35e58a",
                stipple="gray50",
            )

        def on_drag(event):
            if selection["start"] is not None:
                x, y = selection["start"]
                canvas.coords(selection["rectangle"], x, y, event.x, event.y)

        def on_release(event):
            if selection["start"] is None:
                return
            x1, y1 = selection["start"]
            x2, y2 = event.x, event.y
            region = (
                min(x1, x2) + left,
                min(y1, y2) + top,
                abs(x2 - x1),
                abs(y2 - y1),
            )
            overlay.destroy()
            self.root.deiconify()
            if region[2] < 8 or region[3] < 8:
                self.status.set("已取消：请选择一个区域。")
                return
            self.status.set("正在识别…")
            self.scan_button.configure(state="disabled")
            self.root.after(180, lambda: self.scan_region(region))

        def cancel(_event=None):
            overlay.destroy()
            self.root.deiconify()
            self.status.set("已取消")

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        overlay.bind("<Escape>", cancel)
        overlay.focus_force()

    def scan_region(self, region):
        try:
            image = capture_region(*region)
            values = decode_qr(image)
        except (OSError, cv2.error) as error:
            self.scan_button.configure(state="normal")
            self.status.set("识别失败")
            messagebox.showerror("二维码速取", f"截图或识别失败：{error}", parent=self.root)
            return
        finally:
            self.root.update_idletasks()

        self.scan_button.configure(state="normal")
        if not values:
            self.status.set("未识别到二维码，请重新框选并确保二维码清晰。")
            messagebox.showinfo("二维码速取", self.status.get(), parent=self.root)
            return

        self.values = values
        self.result.delete("1.0", "end")
        self.result.insert("1.0", "\n\n".join(values))
        self.copy_button.configure(state="normal")
        self.open_button.configure(
            state="normal" if len(values) == 1 and self.is_web_url(values[0]) else "disabled"
        )
        self.copy_result()
        self.status.set(f"识别到 {len(values)} 个二维码，结果已复制。")

    @staticmethod
    def is_web_url(value):
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    def copy_result(self):
        text = self.result.get("1.0", "end-1c").strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        self.status.set("结果已复制到剪贴板。")

    def open_link(self):
        if len(self.values) == 1 and self.is_web_url(self.values[0]):
            webbrowser.open(self.values[0])


def self_test():
    encoder = cv2.QRCodeEncoder_create()
    expected = "https://example.com/qr-utility-test"
    image = encoder.encode(expected)
    image = cv2.resize(image, None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST)
    image = cv2.copyMakeBorder(
        image, 32, 32, 32, 32, cv2.BORDER_CONSTANT, value=255
    )
    decoded = decode_qr(image)
    if decoded != [expected]:
        raise RuntimeError(f"QR decoder self-test failed: {decoded!r}")
    print("QR decoder self-test passed.")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            pass
        window = tk.Tk()
        QRUtility(window)
        window.mainloop()
