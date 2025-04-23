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
from datetime import datetime, timezone

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QSettings

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

from .settings_dialog import SettingsDialog


class WeatherDockWidget(QtWidgets.QDockWidget):
    """Weather dock widget implementation."""

    def __init__(self, iface):
        """Constructor."""
        super(WeatherDockWidget, self).__init__()
        self.iface = iface
        self.setWindowTitle("Weather Dock")
        self.setMinimumWidth(350)
        self.text_browser = QtWidgets.QTextBrowser()
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)
        self.setWidget(self.text_browser)
        self.show_message("Loading weather data...")
        # Store the fetch thread to prevent multiple simultaneous requests
        self.fetch_thread = None

    def show_message(self, message):
        """Show a message in the text browser."""
        html = f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body {{font-family: Arial, sans-serif; margin: 10px; color: black; background-color: white;}}</style>
        </head><body><p>{message}</p></body></html>
        """
        self.text_browser.setHtml(html)

    def show_error(self, message):
        """Show an error message in the text browser."""
        html = f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>
            body {{font-family: Arial, sans-serif; margin: 10px; color: black; background-color: white;}}
            .error {{color: #e74c3c; padding: 10px; border-left: 4px solid #e74c3c; background-color: #fae5e5; border-radius: 4px;}}
        </style>
        </head><body>
            <div class="error"><strong>Error:</strong> {message}</div>
            <p>Please try again later, check your network connection, or review settings.</p>
        </body></html>
        """
        self.text_browser.setHtml(html)

    def update_weather(self):
        """Update the weather data for the current map extent."""
        # Prevent starting a new fetch if one is already running
        if self.fetch_thread and self.fetch_thread.isRunning():
            # Optionally: print("Fetch already in progress, skipping.")
            return

        canvas = self.iface.mapCanvas()
        extent = canvas.extent()
        center = extent.center()
        source_crs = canvas.mapSettings().destinationCrs()
        dest_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        if source_crs != dest_crs:
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
            center = transform.transform(center)
        latitude = center.y()
        longitude = center.x()
        self.show_message(f"Loading weather data for coordinates: {latitude:.4f}, {longitude:.4f}...")

        # Get forecast days from settings
        forecast_days = SettingsDialog.get_forecast_days()

        # Start the fetch thread
        self.fetch_thread = FetchWeatherThread(latitude, longitude, forecast_days) # Pass days
        self.fetch_thread.weatherDataReceived.connect(self.on_weather_data_received)
        self.fetch_thread.weatherDataError.connect(self.on_weather_data_error)
        # Optional: Connect finished signal to allow new fetches after completion
        # self.fetch_thread.finished.connect(self.on_fetch_finished)
        self.fetch_thread.start()

    def on_weather_data_received(self, weather_data):
        """Handle received weather data."""
        self.display_weather_html(weather_data)
        self.fetch_thread = None # Allow new fetch

    def on_weather_data_error(self, error_message):
        """Handle weather data fetch errors."""
        self.show_error(error_message)
        self.fetch_thread = None # Allow new fetch

    def display_weather_html(self, weather_data):
        """Display the weather data as HTML using tables."""
        # Extract current weather data
        current = weather_data.get('current', {})
        current_time_str = current.get('time', '')
        current_temp = current.get('temperature_2m', 'N/A')
        current_wind = current.get('wind_speed_10m', 'N/A')

        # Extract hourly forecast data
        hourly = weather_data.get('hourly', {})
        hourly_times = hourly.get('time', [])
        hourly_temps = hourly.get('temperature_2m', [])
        hourly_wind_speeds = hourly.get('wind_speed_10m', [])
        hourly_humidity = hourly.get('relative_humidity_2m', [])

        # Format current time (display in local time)
        formatted_time = "Unknown Time"
        if current_time_str:
            try:
                local_dt = datetime.now()
                formatted_time = local_dt.strftime("%A, %B %d, %Y %H:%M %Z%z") # Include timezone info
            except (ValueError, TypeError):
                formatted_time = current_time_str # Fallback

        # Get units
        units = weather_data.get('current_units', {})
        temp_unit = units.get('temperature_2m', '°C')
        wind_unit = units.get('wind_speed_10m', 'km/h')
        hourly_units = weather_data.get('hourly_units', {})
        hourly_temp_unit = hourly_units.get('temperature_2m', temp_unit)
        hourly_wind_unit = hourly_units.get('wind_speed_10m', wind_unit)
        hourly_humidity_unit = hourly_units.get('relative_humidity_2m', '%')

        # --- Generate HTML table rows for the forecast ---
        forecast_table_rows = ""
        # The number of rows is now determined by the length of the returned data
        if hourly_times: # Check if there's any hourly data
            for i in range(len(hourly_times)):
                # Format time to local timezone
                time_str = "N/A"
                if i < len(hourly_times):
                     try:
                         # Parse as naive, assume UTC, convert to local
                         utc_dt = datetime.fromisoformat(hourly_times[i]).replace(tzinfo=timezone.utc)
                         local_dt = utc_dt.astimezone(None)
                         # Format as "Day HH:MM" e.g., "Mon 14:00"
                         time_str = local_dt.strftime("%a %H:%M") # Use %a for abbreviated weekday
                     except (ValueError, TypeError):
                         time_str = hourly_times[i] # Fallback

                temp_str = f"{hourly_temps[i]:.1f}" if i < len(hourly_temps) and hourly_temps[i] is not None else "N/A"
                wind_str = f"{hourly_wind_speeds[i]:.1f}" if i < len(hourly_wind_speeds) and hourly_wind_speeds[i] is not None else "N/A"
                humidity_str = f"{hourly_humidity[i]}" if i < len(hourly_humidity) and hourly_humidity[i] is not None else "N/A"

                row_style = "background-color: #f0f0f0;" if i % 2 != 0 else ""

                forecast_table_rows += f"""
                <tr style="{row_style}">
                    <td class="time-cell">{time_str}</td>
                    <td class="data-cell">{temp_str} {hourly_temp_unit}</td>
                    <td class="data-cell">{wind_str} {hourly_wind_unit}</td>
                    <td class="data-cell">{humidity_str}{hourly_humidity_unit}</td>
                </tr>
                """
        else:
            forecast_table_rows = '<tr><td colspan="4" style="text-align: center;">No hourly forecast data available.</td></tr>'

        forecast_days = SettingsDialog.get_forecast_days()
        forecast_title = f"Hourly Forecast ({forecast_days} Day{'s' if forecast_days > 1 else ''})"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                /* CSS styles remain largely the same as previous version */
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: white; color: black; font-size: 16px; }}
                .container {{ padding: 15px; }}
                .header {{ background-color: white; color: black; padding: 15px; border-radius: 8px 8px 0 0; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-bottom: 1px solid #ccc; }}
                .header h2 {{ margin-top: 0; margin-bottom: 5px; }}
                .header p {{ margin-bottom: 0; font-size: 0.9em; }}
                .current-weather {{ background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow: hidden; }}
                .temp-display {{ font-size: 2.0em; /* Slightly smaller */ font-weight: bold; margin-bottom: 10px; color: black; }} /* Adjusted size and added margin */
                .weather-details p {{ margin: 5px 0; font-size: 1.1em; color: black; }}
                .forecast-container {{ background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                h3 {{ margin-top: 0; color: black; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-bottom: 15px; font-size: 1.4em; }}
                .forecast-table table {{ width: 100%; border-collapse: collapse; font-size: 1em; border: 1px solid black; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .forecast-table th, .forecast-table td {{ border: none; border-bottom: 1px solid #ddd; padding: 10px 8px; color: black; }}
                .forecast-table thead tr {{ border-bottom: 2px solid black; }}
                .forecast-table th {{ background-color: white; font-weight: bold; border-bottom: 2px solid black; }}
                .forecast-table th.time-header {{ text-align: left; }}
                .forecast-table th.data-header {{ text-align: right; padding-right: 12px; }}
                .forecast-table td.time-cell {{ text-align: left; }}
                .forecast-table td.data-cell {{ text-align: right; padding-right: 12px; }}
                .forecast-table tbody tr:last-child td {{ border-bottom: none; }}
                .footer {{ font-size: 0.9em; text-align: center; margin-top: 20px; color: black; }}
                .footer a {{ color: black; text-decoration: underline; }}
                .label {{ font-weight: bold; color: black; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Weather Forecast</h2>
                    <p>{formatted_time}</p>
                </div>

                <div class="current-weather">
                     <!-- Display current temp and wind side-by-side using a simple table for layout -->
                     <table style="width:100%; border:none;"><tr>
                       <td style="width:50%; border:none; vertical-align:top;">
                         <div class="temp-display"><span class="label">Now:</span><br><strong>{current_temp}{temp_unit}</strong></div>
                       </td>
                       <td style="width:50%; border:none; vertical-align:top;">
                         <div class="weather-details">
                           <p><span class="label">Wind:</span><br><strong>{current_wind} {wind_unit}</strong></p>
                         </div>
                       </td>
                     </tr></table>
                </div>
                <p></p>
                <p></p>
                <div class="forecast-container">
                    <!-- Use dynamic title -->
                    <h3>{forecast_title}</h3>
                    <div class="forecast-table">
                        <table>
                            <thead>
                                <tr>
                                    <th class="time-header">Time</th>
                                    <th class="data-header">Temp</th>
                                    <th class="data-header">Wind</th>
                                    <th class="data-header">Humidity</th>
                                </tr>
                            </thead>
                            <tbody>
                                {forecast_table_rows}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="footer">
                    Data provided by <a href="https://open-meteo.com/" target="_blank">Open-Meteo.com</a>
                </div>
            </div>
        </body>
        </html>
        """
        self.text_browser.setHtml(html)


class FetchWeatherThread(QtCore.QThread):
    """Thread for fetching weather data."""
    weatherDataReceived = QtCore.pyqtSignal(dict)
    weatherDataError = QtCore.pyqtSignal(str)

    def __init__(self, latitude, longitude, forecast_days):
        """Constructor."""
        super(FetchWeatherThread, self).__init__()
        self.latitude = latitude
        self.longitude = longitude
        self.forecast_days = forecast_days # Store forecast days

    def run(self):
        """Run the thread to fetch weather data."""
        try:
            # Use self.forecast_days in the API call
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.latitude}"
                f"&longitude={self.longitude}"
                f"&current=temperature_2m,wind_speed_10m"
                f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
                f"&forecast_days={self.forecast_days}" # Use the setting
                f"&timezone=auto" # Ask API to detect timezone if needed (though we convert manually)
            )
            # print(f"Fetching URL: {url}") # Uncomment for debugging API calls

            with urllib.request.urlopen(url, timeout=20) as response: # Increased timeout slightly
                data = response.read()
                weather_data = json.loads(data.decode('utf-8'))
            self.weatherDataReceived.emit(weather_data)
        except urllib.error.URLError as e:
            if hasattr(e, 'reason'):
                self.weatherDataError.emit(f"Network Error: {e.reason}")
            else:
                self.weatherDataError.emit(f"URL Error: {e}")
        except json.JSONDecodeError:
            self.weatherDataError.emit("Error: Could not parse weather data from the server.")
        except Exception as e:
            self.weatherDataError.emit(f"An unexpected error occurred: {str(e)}")

