# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WeatherDock
 A QGIS plugin that displays weather information for the current map extent.
***************************************************************************/
"""


def classFactory(iface):
    """Load WeatherDock class from file weather_dock.py

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    :return: WeatherDock
    :rtype: WeatherDock
    """
    from .weather_dock import WeatherDock
    return WeatherDock(iface)
