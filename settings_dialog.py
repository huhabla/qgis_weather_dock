# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SettingsDialog
 Settings dialog for the Weather Dock plugin.
 ***************************************************************************/
"""

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QSettings


class SettingsDialog(QtWidgets.QDialog):
    """Settings dialog implementation."""

    # Define setting keys as constants
    FORECAST_DAYS_KEY = "weatherdock/forecast_days"
    DEFAULT_FORECAST_DAYS = 1

    def __init__(self, parent=None):
        """Constructor."""
        super(SettingsDialog, self).__init__(parent)

        self.setWindowTitle("Weather Dock Settings")
        self.setMinimumWidth(300)

        # --- UI Elements ---
        layout = QtWidgets.QVBoxLayout(self)

        # Forecast Days Setting
        days_group = QtWidgets.QGroupBox("Forecast Duration")
        days_layout = QtWidgets.QHBoxLayout(days_group)

        days_label = QtWidgets.QLabel("Number of days to forecast (1-7):")
        self.days_spinbox = QtWidgets.QSpinBox()
        self.days_spinbox.setRange(1, 7)
        self.days_spinbox.setToolTip("Select how many days of hourly forecast data to fetch and display.")

        days_layout.addWidget(days_label)
        days_layout.addWidget(self.days_spinbox)
        layout.addWidget(days_group)

        # --- Dialog Buttons ---
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Load current settings when dialog opens
        self.load_settings()

    def load_settings(self):
        """Load settings from QSettings and update UI."""
        settings = QSettings()
        forecast_days = settings.value(self.FORECAST_DAYS_KEY, self.DEFAULT_FORECAST_DAYS, type=int)
        self.days_spinbox.setValue(forecast_days)

    def save_settings(self):
        """Save UI settings to QSettings."""
        settings = QSettings()
        settings.setValue(self.FORECAST_DAYS_KEY, self.days_spinbox.value())

    # Override accept() to save settings before closing
    def accept(self):
        """Save settings and close the dialog."""
        self.save_settings()
        super(SettingsDialog, self).accept()

    # Static method to easily get the current setting value elsewhere
    @staticmethod
    def get_forecast_days():
        """Gets the stored forecast days value from QSettings."""
        settings = QSettings()
        return settings.value(SettingsDialog.FORECAST_DAYS_KEY, SettingsDialog.DEFAULT_FORECAST_DAYS, type=int)
