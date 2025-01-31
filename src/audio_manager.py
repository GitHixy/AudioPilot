import os
import ctypes
from ctypes import wintypes
import win32gui
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume, IAudioMeterInformation
from comtypes import CLSCTX_ALL
from PyQt6.QtGui import QPixmap, QImage
import numpy as np
import sounddevice as sd
import scipy.signal


class AudioManager:
    def __init__(self):
        self.devices = AudioUtilities.GetSpeakers()
        interface = self.devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        self.volume = interface.QueryInterface(IAudioEndpointVolume)
        self.eq_settings = {}  # Store EQ settings for each session

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
    
    def get_session_level(self, session):
        """Get the current audio level (peak) of a session."""
        try:
            meter = session._ctl.QueryInterface(IAudioMeterInformation)
            peak = meter.GetPeakValue()  
            return int(peak * 100)  
        except Exception as e:
            print(f"Failed to get session level for {session.Process.name()}: {e}")
            return 0

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

    def set_eq(self, session_name, band, value):
        """Set the EQ value for a specific band."""
        if session_name not in self.eq_settings:
            self.eq_settings[session_name] = [0] * 10  # Initialize 10 bands
        self.eq_settings[session_name][band] = value

    def get_eq(self, session_name):
        """Get the EQ settings for a session."""
        return self.eq_settings.get(session_name, [0] * 10)

    def save_preset(self, session_name, preset_name):
        """Save the current EQ settings as a preset."""
        if session_name in self.eq_settings:
            with open(f"{session_name}_{preset_name}.eq", "w") as f:
                f.write(",".join(map(str, self.eq_settings[session_name])))

    def load_preset(self, session_name, preset_name):
        """Load an EQ preset."""
        try:
            with open(f"{session_name}_{preset_name}.eq", "r") as f:
                self.eq_settings[session_name] = list(map(int, f.read().split(",")))
        except FileNotFoundError:
            print(f"Preset {preset_name} not found for session {session_name}")

    def list_presets(self, session_name):
        """List available presets for a session."""
        presets = []
        for file in os.listdir():
            if file.startswith(session_name) and file.endswith(".eq"):
                presets.append(file[len(session_name) + 1:-3])  # Extract preset name
        return presets

    def apply_eq(self, session_name):
        """Apply the EQ settings to the audio output."""
        eq_values = self.get_eq(session_name)
        session = next((s for s in self.get_audio_sessions() if s["name"] == session_name), None)
        if not session:
            return

        # Apply EQ settings directly to the session
        def apply_band_pass_filter(audio_data, lowcut, highcut, fs, order=5):
            nyquist = 0.5 * fs
            low = lowcut / nyquist
            high = highcut / nyquist
            b, a = scipy.signal.butter(order, [low, high], btype='band')
            y = scipy.signal.lfilter(b, a, audio_data)
            return y

        # Placeholder for actual EQ application logic
        # Modify the audio data of the session directly using the appropriate audio APIs
        # Example placeholder code:
        # session["session"].SimpleAudioVolume.SetMasterVolume(eq_values[0] / 10.0, None)

        # Note: The actual implementation will depend on the audio APIs you are using
        # and how you can modify the audio data of the session directly
