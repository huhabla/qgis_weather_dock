# Weather Dock QGIS Plugin

A QGIS plugin that displays current weather information for the center of the map canvas.

## Features

- Displays current temperature and wind speed
- Shows hourly forecast for temperature and wind speed
- Updates automatically when the map canvas extent changes
- Uses the free open-meteo.com weather API
- Renders data in a beautiful HTML interface

## Requirements

- QGIS 3.34 or higher
- Internet connection to fetch weather data

## Installation

### From ZIP file

1. Download the ZIP file of the plugin
2. Open QGIS
3. Go to "Plugins" → "Manage and Install Plugins..."
4. Click on "Install from ZIP"
5. Browse to the downloaded ZIP file and click "Install Plugin"

### Manual Installation

1. Download or clone this repository
2. Copy the entire directory to your QGIS plugin directory:
   - Windows: `C:\Users\{username}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`
3. Restart QGIS
4. Enable the plugin in the QGIS Plugin Manager

## Usage

1. After installing the plugin, click on the Weather Dock icon in the plugin toolbar
2. A dock widget will appear on the right side of the QGIS window
3. The widget will display current weather information for the center of your map canvas
4. As you pan and zoom the map, the weather information will update automatically

## Data Source

This plugin uses the free [Open-Meteo Weather API](https://open-meteo.com/), which provides:
- Current weather conditions
- Hourly forecasts
- No API key required
- Free for non-commercial use

## License

This plugin is licensed under the [GNU General Public License v3.0](LICENSE).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.