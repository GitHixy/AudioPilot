from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QSlider, QLabel, QPushButton, QFrame, QProgressBar
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation
from audio_manager import AudioManager

class AudioPilot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AudioPilot - Mixer")
        self.setGeometry(100, 100, 800, 600)

        # Set the window icon to the logo
        self.setWindowIcon(QIcon('src/assets/audiopilot.ico'))

        # Initialize the audio manager and sessions
        self.audio_manager = AudioManager()
        self.audio_sessions = self.audio_manager.get_audio_sessions()
        self.hidden_channels = []  # Tracks hidden channels

        # Main layout
        self.main_layout = QVBoxLayout()

        # Master volume section (horizontal)
        master_label = QLabel("Master Volume", self)
        self.master_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.master_slider.setMinimum(0)
        self.master_slider.setMaximum(100)
        master_label.setStyleSheet("font-size: 16px; color: white; margin-top: 5px;")
        current_master_volume = int(self.audio_manager.get_master_volume())  # Convert to int before setting
        self.master_slider.setValue(current_master_volume)
        self.master_slider.valueChanged.connect(self.master_slider_changed)

        # Value label for Master Volume
        self.master_value_label = QLabel(f"{current_master_volume}%", self)
        self.master_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.master_value_label.setStyleSheet("color: white; font-size: 14px;")

        self.master_slider.setFixedWidth(400)

        # Layout for Master Volume
        master_layout = QVBoxLayout()
        master_layout.addWidget(master_label, alignment=Qt.AlignmentFlag.AlignCenter)
        master_layout.addWidget(self.master_slider, alignment=Qt.AlignmentFlag.AlignCenter)
        master_layout.addWidget(self.master_value_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addLayout(master_layout)

        # Divider
        divider = QFrame(self)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("background-color: #333;")
        self.main_layout.addWidget(divider)

        # Application volumes title
        self.app_title = QLabel("Application Volumes", self)
        self.app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.app_title.setStyleSheet("font-size: 16px; color: white; margin-top: 5px;")
        self.main_layout.addWidget(self.app_title)

        # Reset button
        reset_button = QPushButton("Show All Channels", self)
        reset_button.setStyleSheet("font-size: 12px; padding: 7px;")
        reset_button.clicked.connect(self.reset_hidden_channels)
        self.main_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Layout for sliders
        self.sliders_layout = QHBoxLayout()
        self.update_sliders()

        self.main_layout.addLayout(self.sliders_layout)

        # Footer
        footer = QLabel("AudioPilot v1.0.2 by GitHixy", self)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("font-size: 13px; color: #666; padding: 5px;")
        self.main_layout.addWidget(footer)

        # Set the main layout
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # Timer to dynamically check for new or closed sessions
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_new_sessions)
        self.timer.timeout.connect(self.update_level_bars)
        self.timer.start(1000)

    def update_sliders(self):
        """Update the slider layout to reflect current sessions."""
        for i in reversed(range(self.sliders_layout.count())):
            widget = self.sliders_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        visible_sessions = [session for session in self.audio_sessions if session["name"] not in self.hidden_channels]
        for session in visible_sessions:
            slider_widget = self.create_vertical_slider(session)
            self.sliders_layout.addWidget(slider_widget)

        if visible_sessions:
            self.app_title.show()
        else:
            self.app_title.hide()

    def create_vertical_slider(self, session):
        """Create a vertical slider with associated controls."""
        layout = QVBoxLayout()

        if session["icon"]:
            icon_label = QLabel(self)
            pixmap = session["icon"]
            if isinstance(pixmap, QPixmap):
                icon_label.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                icon_label.setText("No Icon")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        label = QLabel(session["name"], self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)

        slider_and_bar_layout = QHBoxLayout()

        slider = QSlider(Qt.Orientation.Vertical, self)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(int(session["volume"]))
        slider.valueChanged.connect(lambda value, s=session: self.slider_value_changed(value, s))
        slider_and_bar_layout.addWidget(slider)

        session["volume_label"] = QLabel(f"{session['volume']}%", self)
        session["volume_label"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        session["volume_label"].setStyleSheet("color: white; font-size: 12px;")
        layout.addWidget(session["volume_label"], alignment=Qt.AlignmentFlag.AlignHCenter)

        level_bar = self.create_output_level_bar()
        session["level_bar"] = level_bar
        slider_and_bar_layout.addWidget(level_bar)

        layout.addLayout(slider_and_bar_layout)

        mute_button = QPushButton("Mute", self)
        mute_button.setCheckable(True)
        mute_button.clicked.connect(lambda _, s=session["session"], b=mute_button, sl=slider: self.mute_channel(s, b, sl))
        layout.addWidget(mute_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        hide_button = QPushButton("Hide Channel", self)
        hide_button.clicked.connect(lambda _, name=session["name"]: self.hide_channel(name))
        layout.addWidget(hide_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        slider_widget = QWidget()
        slider_widget.setLayout(layout)
        session["widget"] = slider_widget  # Store reference to widget for safe deletion
        return slider_widget

    def create_output_level_bar(self):
        """Create a bar to show audio output level."""
        level_bar = QProgressBar(self)
        level_bar.setOrientation(Qt.Orientation.Vertical)
        level_bar.setMinimum(0)
        level_bar.setMaximum(100)
        level_bar.setValue(0)
        level_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #666;
                        background: #222;
                        border-radius: 3px;
                    }
                    QProgressBar::chunk {
                        background-color: green;
                    }
                """)
        level_bar.setFixedWidth(8)
        level_bar.setTextVisible(False)  # Hide numeric value
        level_bar.animation = QPropertyAnimation(level_bar, b"value")  
        level_bar.animation.setDuration(150)  
        return level_bar

    def slider_value_changed(self, value, session):
        session["session"].SimpleAudioVolume.SetMasterVolume(value / 100, None)
        session["volume_label"].setText(f"{value}%")

    def mute_channel(self, session, button, slider):
        if not hasattr(session, "previous_volume"):
            session.previous_volume = session.SimpleAudioVolume.GetMasterVolume()

        if button.isChecked():
            session.SimpleAudioVolume.SetMasterVolume(0, None)
            slider.setValue(0)
        else:
            previous_volume = session.previous_volume * 100
            session.SimpleAudioVolume.SetMasterVolume(previous_volume / 100, None)
            slider.setValue(int(previous_volume))

    def hide_channel(self, name):
        session_to_hide = next((s for s in self.audio_sessions if s["name"] == name), None)
        if session_to_hide:
            self.hidden_channels.append(name)
            if "widget" in session_to_hide:
                session_to_hide["widget"].deleteLater()  # Safely delete the widget
            self.update_sliders()

    def reset_hidden_channels(self):
        self.hidden_channels = []
        self.update_sliders()

    def check_new_sessions(self):
        current_sessions = self.audio_manager.get_audio_sessions()
        new_sessions = [
            session for session in current_sessions
            if session["name"].lower() not in [s["name"].lower() for s in self.audio_sessions]
        ]
        closed_sessions = [
            session for session in self.audio_sessions
            if session["name"].lower() not in [s["name"].lower() for s in current_sessions]
        ]
        if new_sessions or closed_sessions:
            self.audio_sessions = [session for session in current_sessions]
            self.update_sliders()

    def update_level_bars(self):
        """Update the output level bars for all visible sessions."""
        for session in self.audio_sessions:
            if "level_bar" in session and isinstance(session["level_bar"], QProgressBar):
                level_bar = session["level_bar"]

                try:
                    # Get the current audio level
                    current_level = self.audio_manager.get_session_level(session["session"])

                    # Smooth animation for value change
                    level_bar.animation.stop()  
                    level_bar.animation.setStartValue(level_bar.value())  
                    level_bar.animation.setEndValue(current_level)  
                    level_bar.animation.start()  

                    # Dynamically update only the chunk color
                    if current_level > 90:
                        color = "red"
                    elif current_level > 70:
                        color = "yellow"
                    else:
                        color = "green"

                    # Apply the chunk color dynamically
                    level_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid #666;
                        background: #222;
                        border-radius: 3px;
                    }}
                    QProgressBar::chunk {{
                        border-radius: 3px;
                        background-color: {color};
                    }}
                """)
                except RuntimeError:
                    continue


    def master_slider_changed(self):
        master_value = self.master_slider.value()
        self.audio_manager.set_master_volume(master_value)
        self.master_value_label.setText(f"{master_value}%")

if __name__ == "__main__":
    app = QApplication([])
    main_window = AudioPilot()
    main_window.show()
    app.exec()
