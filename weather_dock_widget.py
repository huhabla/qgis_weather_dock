# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WeatherDockWidget
 Widget that displays weather information for the current map extent.
***************************************************************************/
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime

from PyQt5 import QtGui, QtWidgets, QtCore, QtWebKitWidgets
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject


class WeatherDockWidget(QtWidgets.QDockWidget):
    """Weather dock widget implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: A QGIS interface instance.
        :type iface: QgsInterface
        """
        super(WeatherDockWidget, self).__init__()

        self.iface = iface

        # Set up the user interface
        self.setWindowTitle("Weather Dock")
        self.setMinimumWidth(350)

        # Create a web view widget to display HTML content
        self.web_view = QtWebKitWidgets.QWebView()
        self.web_view.page().setLinkDelegationPolicy(
            QtWebKitWidgets.QWebPage.DelegateAllLinks
        )
        self.web_view.linkClicked.connect(self.link_clicked)

        # Set the web view as the dock widget's main widget
        self.setWidget(self.web_view)

        # Show a loading message
        self.show_message("Loading weather data...")

    def link_clicked(self, url):
        """Handle link clicks in the web view.

        :param url: The clicked URL.
        :type url: QUrl
        """
        # Open links in the default web browser
        QtGui.QDesktopServices.openUrl(url)

    def show_message(self, message):
        """Show a message in the web view.

        :param message: The message to display.
        :type message: str
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    color: #333;
                }}
            </style>
        </head>
        <body>
            <p>{message}</p>
        </body>
        </html>
        """
        self.web_view.setHtml(html)

    def show_error(self, message):
        """Show an error message in the web view.

        :param message: The error message to display.
        :type message: str
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    color: #333;
                }}
                .error {{
                    color: #e74c3c;
                    padding: 10px;
                    border-left: 4px solid #e74c3c;
                    background-color: #fae5e5;
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <strong>Error:</strong> {message}
            </div>
            <p>Please try again later or check your network connection.</p>
        </body>
        </html>
        """
        self.web_view.setHtml(html)

    def update_weather(self):
        """Update the weather data for the current map extent."""
        # Get the current map canvas
        canvas = self.iface.mapCanvas()

        # Get the center of the current extent
        extent = canvas.extent()
        center = extent.center()

        # Transform coordinates to EPSG:4326 (WGS84) if needed
        source_crs = canvas.mapSettings().destinationCrs()
        dest_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        if source_crs != dest_crs:
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            center = transform.transform(center)

        # Get the latitude and longitude
        latitude = center.y()
        longitude = center.x()

        # Show a loading message
        self.show_message(f"Loading weather data for coordinates: {latitude:.4f}, {longitude:.4f}...")

        # Fetch weather data in a separate thread to avoid freezing the UI
        self.fetch_thread = FetchWeatherThread(latitude, longitude)
        self.fetch_thread.weatherDataReceived.connect(self.on_weather_data_received)
        self.fetch_thread.weatherDataError.connect(self.on_weather_data_error)
        self.fetch_thread.start()

    def on_weather_data_received(self, weather_data):
        """Handle received weather data.

        :param weather_data: The weather data as a dictionary.
        :type weather_data: dict
        """
        # Format the received weather data as HTML
        self.display_weather_html(weather_data)

    def on_weather_data_error(self, error_message):
        """Handle weather data fetch errors.

        :param error_message: The error message.
        :type error_message: str
        """
        self.show_error(error_message)

    def display_weather_html(self, weather_data):
        """Display the weather data as HTML.

        :param weather_data: The weather data as a dictionary.
        :type weather_data: dict
        """
        # Extract current weather data
        current = weather_data.get('current', {})
        current_time = current.get('time', '')
        current_temp = current.get('temperature_2m', 0)
        current_wind = current.get('wind_speed_10m', 0)

        # Extract hourly forecast data
        hourly = weather_data.get('hourly', {})
        hourly_times = hourly.get('time', [])
        hourly_temps = hourly.get('temperature_2m', [])
        hourly_wind_speeds = hourly.get('wind_speed_10m', [])
        hourly_humidity = hourly.get('relative_humidity_2m', [])

        # Format date/time
        try:
            dt = datetime.fromisoformat(current_time)
            formatted_time = dt.strftime("%A, %B %d, %Y %H:%M")
        except:
            formatted_time = current_time

        # Get units
        units = weather_data.get('current_units', {})
        temp_unit = units.get('temperature_2m', '°C')
        wind_unit = units.get('wind_speed_10m', 'km/h')

        # Prepare data for charts - limit to next 24 hours
        chart_times = []
        limit = min(24, len(hourly_times))

        for i in range(limit):
            try:
                dt = datetime.fromisoformat(hourly_times[i])
                chart_times.append(dt.strftime("%H:%M"))
            except:
                chart_times.append(hourly_times[i])

        chart_temps = hourly_temps[:limit]
        chart_wind_speeds = hourly_wind_speeds[:limit]
        chart_humidity = hourly_humidity[:limit]

        # Generate HTML with Chart.js
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f8f9fa;
                    color: #343a40;
                }}
                .container {{
                    padding: 15px;
                }}
                .header {{
                    background: linear-gradient(135deg, #3498db, #2980b9);
                    color: white;
                    padding: 15px;
                    border-radius: 8px 8px 0 0;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .current-weather {{
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .temp-display {{
                    font-size: 3em;
                    font-weight: bold;
                    margin-right: 20px;
                }}
                .weather-details {{
                    flex: 1;
                }}
                .weather-details p {{
                    margin: 5px 0;
                }}
                .chart-container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .footer {{
                    font-size: 0.8em;
                    text-align: center;
                    margin-top: 20px;
                    color: #6c757d;
                }}
                .footer a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                .footer a:hover {{
                    text-decoration: underline;
                }}
                .label {{
                    font-weight: bold;
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Weather Forecast</h2>
                    <p>{formatted_time}</p>
                </div>

                <div class="current-weather">
                    <div class="temp-display">{current_temp}{temp_unit}</div>
                    <div class="weather-details">
                        <p><span class="label">Wind Speed:</span> {current_wind} {wind_unit}</p>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>Temperature Forecast</h3>
                    <canvas id="tempChart"></canvas>
                </div>

                <div class="chart-container">
                    <h3>Wind Speed Forecast</h3>
                    <canvas id="windChart"></canvas>
                </div>

                <div class="footer">
                    Data provided by <a href="https://open-meteo.com/" target="_blank">Open-Meteo.com</a>
                </div>
            </div>

            <script>
                // Temperature Chart
                var tempCtx = document.getElementById('tempChart').getContext('2d');
                var tempChart = new Chart(tempCtx, {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(chart_times)},
                        datasets: [{{
                            label: 'Temperature ({temp_unit})',
                            data: {json.dumps(chart_temps)},
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            tension: 0.4,
                            fill: true
                        }}]
                    }},
                    options: {{
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'top'
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: false
                            }}
                        }}
                    }}
                }});

                // Wind Speed Chart
                var windCtx = document.getElementById('windChart').getContext('2d');
                var windChart = new Chart(windCtx, {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(chart_times)},
                        datasets: [{{
                            label: 'Wind Speed ({wind_unit})',
                            data: {json.dumps(chart_wind_speeds)},
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            tension: 0.4,
                            fill: true
                        }}]
                    }},
                    options: {{
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'top'
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """

        self.web_view.setHtml(html)


class FetchWeatherThread(QtCore.QThread):
    """Thread for fetching weather data."""

    # Define signals for weather data
    weatherDataReceived = QtCore.pyqtSignal(dict)
    weatherDataError = QtCore.pyqtSignal(str)

    def __init__(self, latitude, longitude):
        """Constructor.

        :param latitude: The latitude.
        :type latitude: float
        :param longitude: The longitude.
        :type longitude: float
        """
        super(FetchWeatherThread, self).__init__()

        self.latitude = latitude
        self.longitude = longitude

    def run(self):
        """Run the thread to fetch weather data."""
        try:
            # Construct the API URL
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.latitude}"
                f"&longitude={self.longitude}"
                f"&current=temperature_2m,wind_speed_10m"
                f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
            )

            # Fetch weather data
            with urllib.request.urlopen(url) as response:
                data = response.read()
                weather_data = json.loads(data.decode('utf-8'))

            # Emit signal with weather data
            self.weatherDataReceived.emit(weather_data)

        except urllib.error.URLError as e:
            self.weatherDataError.emit(f"Failed to connect to weather service: {str(e)}")
        except json.JSONDecodeError:
            self.weatherDataError.emit("Failed to parse weather data")
        except Exception as e:
            self.weatherDataError.emit(f"An error occurred: {str(e)}")
