# File: C:/Users/holistech/Documents/GitHub/qgis_weather_dock/weather_dock.py
# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WeatherDock
 A QGIS plugin that displays weather information for the current map extent.
***************************************************************************/
"""

import os
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QAction, QMenu
from qgis.core import QgsProject, QgsCoordinateTransform, QgsCoordinateReferenceSystem
from .weather_dock_widget import WeatherDockWidget
from .settings_dialog import SettingsDialog


class WeatherDock:
    """QGIS Plugin Implementation."""

    UPDATE_DELAY_MS = 3000  # Delay in milliseconds (3 seconds)

    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'WeatherDock_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        self.dock_widget = None
        self.actions = []
        self.menu = self.tr(u'&Weather Dock')
        self.first_start = None

        self.update_timer = QTimer()
        self.update_timer.setInterval(self.UPDATE_DELAY_MS)
        self.update_timer.setSingleShot(True)  # Important: Fire only once after delay
        self.update_timer.timeout.connect(self.perform_delayed_update)  # Connect timeout to actual update

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('WeatherDock', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon/menu action."""
        icon = QIcon(icon_path) if icon_path else QIcon()
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # --- Main Action (Toolbar + Menu) ---
        icon_path = os.path.join(self.plugin_dir, 'icon.svg')
        self.add_action(
            icon_path,
            text=self.tr(u'Show Weather Dock'),
            callback=self.run,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True
        )

        # --- Settings Action (Menu Only) ---
        self.add_action(
            None,
            text=self.tr(u'Settings...'),
            callback=self.show_settings_dialog,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            add_to_menu=True
        )

        self.first_start = True
        # Connect extentsChanged to schedule_update instead of directly updating
        self.iface.mapCanvas().extentsChanged.connect(self.schedule_update)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        # --- STOP TIMER ---
        self.update_timer.stop()

        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            if action.icon():
                self.iface.removeToolBarIcon(action)

        try:
            # --- DISCONNECT CORRECT SLOT ---
            self.iface.mapCanvas().extentsChanged.disconnect(self.schedule_update)
        except TypeError:
            pass

        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget = None

    def run(self):
        """Run method that shows the dock widget and triggers initial weather update."""
        if self.first_start or self.dock_widget is None:
            self.first_start = False
            self.dock_widget = WeatherDockWidget(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
        else:
            if not self.iface.mainWindow().findChild(WeatherDockWidget):
                self.dock_widget = WeatherDockWidget(self.iface)
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

        self.dock_widget.show()
        self.dock_widget.raise_()

        # --- Trigger initial update immediately ---
        self.update_timer.stop()  # Cancel any pending timer from previous interactions
        self.perform_delayed_update()  # Call the actual update method directly

    def show_settings_dialog(self):
        """Create and show the settings dialog."""
        dialog = SettingsDialog(self.iface.mainWindow())
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # --- Trigger immediate update after settings change ---
            self.update_timer.stop()  # Cancel any pending delayed update
            self.perform_delayed_update()  # Call the actual update method directly

    def schedule_update(self):
        """Restarts the timer when the map extent changes."""
        # Don't need to check if widget is visible here,
        # the check happens in perform_delayed_update.
        # Simply restart the timer whenever the map moves.
        self.update_timer.start()  # Restarts the timer if already running

    def perform_delayed_update(self):
        """Update the weather data - called after the timer delay."""
        # Only update if the dock widget exists and is visible
        if self.dock_widget and self.dock_widget.isVisible():
            # Call the update method on the widget instance
            self.dock_widget.update_weather()
