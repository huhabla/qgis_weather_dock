# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WeatherDock
 A QGIS plugin that displays weather information for the current map extent.
***************************************************************************/
"""

import os
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QAction, QMenu  # Added QMenu import
from qgis.core import QgsProject, QgsCoordinateTransform, QgsCoordinateReferenceSystem
from .weather_dock_widget import WeatherDockWidget
from .settings_dialog import SettingsDialog


class WeatherDock:
    """QGIS Plugin Implementation."""

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
        # --- MODIFIED: Allow adding only to menu ---
        icon = QIcon(icon_path) if icon_path else QIcon()  # Allow no icon
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
            text=self.tr(u'Show Weather Dock'),  # Renamed for clarity
            callback=self.run,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,  # Explicitly add to toolbar
            add_to_menu=True  # Explicitly add to menu
        )

        # --- Settings Action (Menu Only) ---
        self.add_action(
            None,  # No icon for settings menu item
            text=self.tr(u'Settings...'),
            callback=self.show_settings_dialog,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,  # Do not add to toolbar
            add_to_menu=True  # Add only to menu
        )

        self.first_start = True
        self.iface.mapCanvas().extentsChanged.connect(self.update_weather)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            if action.icon():  # Only remove toolbar icon if it exists
                self.iface.removeToolBarIcon(action)

        try:  # Use try-except for disconnect robustness
            self.iface.mapCanvas().extentsChanged.disconnect(self.update_weather)
        except TypeError:
            pass  # Signal was not connected

        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget = None

    def run(self):
        """Run method that shows the dock widget and updates weather."""
        if self.first_start or self.dock_widget is None:
            self.first_start = False
            self.dock_widget = WeatherDockWidget(self.iface)
            # Ensure dock widget is created before adding it
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
        else:
            # If dock exists but was closed, recreate it
            if not self.iface.mainWindow().findChild(WeatherDockWidget):
                self.dock_widget = WeatherDockWidget(self.iface)
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

        self.dock_widget.show()
        # Ensure focus or raise if already visible
        self.dock_widget.raise_()
        self.update_weather()

    def show_settings_dialog(self):
        """Create and show the settings dialog."""
        dialog = SettingsDialog(self.iface.mainWindow())
        # If dialog is accepted (OK clicked), trigger a weather update
        # to reflect the new settings immediately.
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.update_weather()

    def update_weather(self):
        """Update the weather data for the current map extent"""
        # Only update if the dock widget exists and is visible
        if self.dock_widget and self.dock_widget.isVisible():
            self.dock_widget.update_weather()
