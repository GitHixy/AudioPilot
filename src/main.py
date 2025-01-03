from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QSlider, QLabel, QPushButton
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from audio_manager import AudioManager




class AudioPilot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AudioPilot - Mixer")
        self.setGeometry(100, 100, 800, 600)

        # Set the window icon to the logo
        self.setWindowIcon(QIcon('src/assets/audiopilot.png'))

        # Initialize the audio manager and sessions
        self.audio_manager = AudioManager()
        self.audio_sessions = self.audio_manager.get_audio_sessions()
        self.hidden_channels = []  # Tracks hidden channels

        # Main layout
        self.main_layout = QVBoxLayout()

        # Add Reset button
        reset_button = QPushButton("Show All Channels", self)
        reset_button.setStyleSheet("font-size: 12px; padding: 7px;")
        reset_button.clicked.connect(self.reset_hidden_channels)
        self.main_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Layout for sliders
        self.sliders_layout = QHBoxLayout()
        self.update_sliders()

        self.main_layout.addLayout(self.sliders_layout)

        # Footer
        footer = QLabel("AudioPilot by GitHixy", self)
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
        self.timer.start(1000)  # Check every 1 second

    def update_sliders(self):
        """Update the slider layout to reflect current sessions."""
        # Clear current layout
        for i in reversed(range(self.sliders_layout.count())):
            widget = self.sliders_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add sliders for each active session
        for session in self.audio_sessions:
            if session["name"] not in self.hidden_channels:
                slider_widget = self.create_vertical_slider(session)
                self.sliders_layout.addWidget(slider_widget)

    def create_vertical_slider(self, session):
        """Create a vertical slider with associated controls."""
        layout = QVBoxLayout()

        # Icon (if available)
        if session["icon"]:
            icon_label = QLabel(self)
            icon_label.setPixmap(session["icon"].scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # App name
        label = QLabel(session["name"], self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Value label
        value_label = QLabel(f"{int(session['volume'])}%", self)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setFont(QFont("Arial", 10))
        value_label.setStyleSheet("color: white;")
        layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Slider
        slider = QSlider(Qt.Orientation.Vertical, self)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(int(session["volume"]))
        slider.valueChanged.connect(lambda value, s=session: self.slider_value_changed(value, s, value_label))
        layout.addWidget(slider, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Mute button
        mute_button = QPushButton("Mute", self)
        mute_button.setCheckable(True)  # Allows toggling
        mute_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 7px;
                border: 1px solid #888888;
            }
            QPushButton:checked {
                background-color: #ff5555; /* Red for muted */
            }
        """)
        mute_button.clicked.connect(lambda _, s=session["session"], b=mute_button, sl=slider: self.mute_channel(s, b, sl))
        layout.addWidget(mute_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Hide channel button
        hide_button = QPushButton("Hide Channel", self)
        hide_button.clicked.connect(lambda _, name=session["name"]: self.hide_channel(name))
        hide_button.setStyleSheet("font-size: 12px; padding: 7px;")
        layout.addWidget(hide_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Container widget
        slider_widget = QWidget()
        slider_widget.setLayout(layout)
        return slider_widget

    def slider_value_changed(self, value, session, value_label):
        """Update the volume of the session and the displayed value."""
        value_label.setText(f"{value}%")
        session["session"].SimpleAudioVolume.SetMasterVolume(value / 100, None)

    def mute_channel(self, session, button, slider):
        """Mute or unmute the session and provide visual feedback."""
        if not hasattr(session, "previous_volume"):
            # Save the previous volume level if not already saved
            session.previous_volume = session.SimpleAudioVolume.GetMasterVolume()

        if button.isChecked():
            # Mute the channel
            session.SimpleAudioVolume.SetMasterVolume(0, None)
            slider.setValue(0)
        else:
            # Restore the previous volume
            previous_volume = session.previous_volume * 100  # Convert to percentage
            session.SimpleAudioVolume.SetMasterVolume(session.previous_volume, None)
            slider.setValue(int(previous_volume))  # Update the slider to previous volume



    def hide_channel(self, name):
        """Hide the selected channel."""
        self.hidden_channels.append(name)
        self.update_sliders()

    def reset_hidden_channels(self):
        """Reset all hidden channels."""
        self.hidden_channels = []
        self.update_sliders()

    def check_new_sessions(self):
        """Dynamically add new sessions and remove closed ones."""
        current_sessions = self.audio_manager.get_audio_sessions()

        # Add new sessions
        new_sessions = [
            session for session in current_sessions
            if session["name"].lower() not in [s["name"].lower() for s in self.audio_sessions]
        ]

        # Remove closed sessions
        closed_sessions = [
            session for session in self.audio_sessions
            if session["name"].lower() not in [s["name"].lower() for s in current_sessions]
        ]

        # Update the session list
        if new_sessions or closed_sessions:
            self.audio_sessions = [
                session for session in current_sessions
            ]
            self.update_sliders()


if __name__ == "__main__":
    app = QApplication([])
    main_window = AudioPilot()
    main_window.show()
    app.exec()



