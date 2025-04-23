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
from PyQt5.QtWidgets import QAction
from qgis.core import QgsProject, QgsCoordinateTransform, QgsCoordinateReferenceSystem

# Initialize Qt resources from file resources.py
# import resources

from .weather_dock_widget import WeatherDockWidget


class WeatherDock:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'WeatherDock_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Create the dock widget
        self.dock_widget = None

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Weather Dock')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
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
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        :type whats_this: str

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = os.path.join(self.plugin_dir, 'icon.svg')
        self.add_action(
            icon_path,
            text=self.tr(u'Weather Dock'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

        # Connect to the extentsChanged signal
        self.iface.mapCanvas().extentsChanged.connect(self.update_weather)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Weather Dock'),
                action)
            self.iface.removeToolBarIcon(action)

        # Disconnect signals
        self.iface.mapCanvas().extentsChanged.disconnect(self.update_weather)

        # Remove the dock widget
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget = None

    def run(self):
        """Run method that performs all the real work"""

        # Create the dock widget (after translation) and keep reference
        if self.first_start or self.dock_widget is None:
            self.first_start = False
            self.dock_widget = WeatherDockWidget(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

        # Show the dock widget
        self.dock_widget.show()

        # Update the weather data for the current extent
        self.update_weather()

    def update_weather(self):
        """Update the weather data for the current map extent"""
        if self.dock_widget:
            self.dock_widget.update_weather()
