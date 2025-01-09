from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QSlider, QLabel, QPushButton, QFrame
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QTimer
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
        # Set current master volume correctly as an integer
        current_master_volume = int(self.audio_manager.get_master_volume())  # Convert to int before setting
        self.master_slider.setValue(current_master_volume)  # Set slider value to actual master volume
        self.master_slider.valueChanged.connect(self.master_slider_changed)  # Link to update master volume
        
        # Value label for Master Volume
        self.master_value_label = QLabel(f"{current_master_volume}%", self)
        self.master_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.master_value_label.setStyleSheet("color: white; font-size: 14px;")
        
        # Customize slider width size
        self.master_slider.setFixedWidth(400)

        # Layout for Master Volume
        master_layout = QVBoxLayout()
        master_layout.addWidget(master_label, alignment=Qt.AlignmentFlag.AlignCenter)
        master_layout.addWidget(self.master_slider, alignment=Qt.AlignmentFlag.AlignCenter)
        master_layout.addWidget(self.master_value_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add master layout to the main layout
        self.main_layout.addLayout(master_layout)

        # Add a horizontal divider (QFrame) between Master Volume and Application Volumes
        divider = QFrame(self)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("background-color: #333;")  # Customize divider color
        self.main_layout.addWidget(divider)

        # Title for Application Volumes section
        self.app_title = QLabel("Application Volumes", self)
        self.app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.app_title.setStyleSheet("font-size: 16px; color: white; margin-top: 5px;")

        # Add title and layout for app sliders
        self.main_layout.addWidget(self.app_title)

        # Add Reset button
        reset_button = QPushButton("Show All Channels", self)
        reset_button.setStyleSheet("font-size: 12px; padding: 7px;")
        reset_button.clicked.connect(self.reset_hidden_channels)
        self.main_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Layout for sliders (applications)
        self.sliders_layout = QHBoxLayout()
        self.update_sliders()

        self.main_layout.addLayout(self.sliders_layout)

        # Footer
        footer = QLabel("AudioPilot v1.0.1 by GitHixy", self)
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
        visible_sessions = [session for session in self.audio_sessions if session["name"] not in self.hidden_channels]
        for session in visible_sessions:
            slider_widget = self.create_vertical_slider(session)
            self.sliders_layout.addWidget(slider_widget)

        # Hide the title if no sessions are visible
        if visible_sessions:
            self.app_title.show()
        else:
            self.app_title.hide()

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

    def master_slider_changed(self):
        """Update the master volume when the master slider is changed."""
        master_value = self.master_slider.value()
        self.audio_manager.set_master_volume(master_value)
        self.master_value_label.setText(f"{master_value}%") 

if __name__ == "__main__":
    app = QApplication([])
    main_window = AudioPilot()
    main_window.show()
    app.exec()
