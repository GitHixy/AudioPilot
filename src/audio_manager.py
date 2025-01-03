import os
import ctypes
from ctypes import wintypes
import win32gui
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from PyQt6.QtGui import QPixmap, QImage


class AudioManager:
    def __init__(self):
        self.devices = AudioUtilities.GetSpeakers()
        interface = self.devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        self.volume = interface.QueryInterface(IAudioEndpointVolume)

    def set_master_volume(self, level):
        """Set the master volume."""
        self.volume.SetMasterVolumeLevelScalar(level / 100, None)

    def get_master_volume(self):
        """Get the master volume."""
        return self.volume.GetMasterVolumeLevelScalar() * 100

    def get_audio_sessions(self):
        """Retrieve audio sessions for active processes."""
        sessions = AudioUtilities.GetAllSessions()
        return [
            {
                "name": self.capitalize_name(os.path.splitext(session.Process.name())[0])
                if session.Process else "System Sounds",
                "volume": session.SimpleAudioVolume.GetMasterVolume() * 100,
                "session": session,
                "icon": self.get_process_icon(session.Process)
            }
            for session in sessions if session.Process
        ]

    def capitalize_name(self, name):
        """Capitalize the name of the application."""
        return " ".join(word.capitalize() for word in name.split())

    def get_process_icon(self, process):
        """Retrieve the process icon."""
        try:
            exe_path = process.exe()
            large, _ = win32gui.ExtractIconEx(exe_path, 0)
            if large:
                hicon = large[0]
                pixmap = self.hicon_to_pixmap(hicon)
                win32gui.DestroyIcon(hicon)
                return pixmap
        except Exception as e:
            print(f"Failed to get icon for {process.name()}: {e}")
        return None

    def hicon_to_pixmap(self, hicon):
        """Convert HICON to QPixmap."""
        hdc = ctypes.windll.user32.GetDC(0)
        memdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
        bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, 256, 256)
        ctypes.windll.gdi32.SelectObject(memdc, bmp)

        # Draw icon on memory DC
        ctypes.windll.user32.DrawIconEx(memdc, 0, 0, hicon, 256, 256, 0, 0, 3)

        # Convert bitmap to QPixmap
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD),
            ]

        bmpinfo = BITMAPINFOHEADER()
        bmpinfo.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmpinfo.biWidth = 256
        bmpinfo.biHeight = -256
        bmpinfo.biPlanes = 1
        bmpinfo.biBitCount = 32
        bmpinfo.biCompression = 0

        buffer_len = 256 * 256 * 4
        buffer = ctypes.create_string_buffer(buffer_len)
        ctypes.windll.gdi32.GetDIBits(memdc, bmp, 0, 256, buffer, ctypes.byref(bmpinfo), 0)

        image = QImage(buffer, 256, 256, QImage.Format.Format_ARGB32)
        pixmap = QPixmap.fromImage(image)

        ctypes.windll.gdi32.DeleteObject(bmp)
        ctypes.windll.gdi32.DeleteDC(memdc)
        ctypes.windll.user32.ReleaseDC(0, hdc)

        return pixmap



