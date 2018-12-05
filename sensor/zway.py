import logging

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.sensor import DOMAIN
from homeassistant.const import CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_INCLUDE
from homeassistant.const import (
    DEVICE_CLASS_BATTERY, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_PRESSURE)
from homeassistant.helpers.icon import icon_for_battery_level

import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['https://github.com/ardeus-ua/pyzway/archive/master.zip#pyzway==0.3.0']

SENSOR_TYPES = {
    'battery': ['Battery Level', '%'],
    'humidity': ['Humidity', '%'],
    'temperature': ['Temperature', 'C'],
    

DEFAULT_ICON_LEVEL = 'mdi:battery'
DEFAULT_ICON_STATE = 'mdi:power-plug'

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_USERNAME, default='admin'): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_INCLUDE): cv.string
})

SUPPORT_ZWAY = {
    'sensorMultilevel': SUPPORT_BRIGHTNESS,
    'battery': SUPPORT_RGB_COLOR
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup Z-Way Sensor platform."""

    import zway

    zwc = zway.controller.Controller(baseurl=config.get(CONF_URL),
                                     username=config.get(CONF_USERNAME),
                                     password=config.get(CONF_PASSWORD))

    include = config.get(CONF_INCLUDE)
    devices = []
    for dev in zwc.devices:
        if dev.is_tagged(include):
            if (isinstance(dev, zway.devices.sensorMultilevel) or
                    isinstance(dev, zway.devices.battery)):
                _LOGGER.info("Including %s %s: %s", dev.devicetype, dev.id, dev.title)
                devices.append(ZWaySensor(dev))
    add_devices(devices)


class ZWaySensor(Sensor):
    """Representation of an Z-Way Sensor"""

    def __init__(self, device):
        self._zsensor = device

    @property
    def unique_id(self):
        """Return the ID of this light."""
        return self._zsensor.id.lower()

    @property
    def name(self):
        """Return the display name of this sensor."""
        return self._zsensor.title

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_ZWAY.get(self._zsensor.devicetype, 0)

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._zsensor.on

    @property
    def brightness(self):
        """Brightness of the sensor (an integer in the range 1-255)."""
        if self._zsensor.devicetype == 'switchMultilevel':
            return self._zsensor.level
        else:
            return None

    @property
    def rgb_color(self):
        """Return the RGB color value."""
        if self._zsensor.devicetype == 'switchRGBW' and self._zsensor.rgb is not None:
            return list(self._zsensor.rgb)
        else:
            return None

    def turn_on(self, **kwargs):
        """Instruct the sensor to turn on."""
        if self._zsensor.devicetype == 'switchMultilevel':
            self._zsensor.level = kwargs.get(ATTR_BRIGHTNESS, 255)
        elif self._zsensor.devicetype == 'switchRGBW':
            self._zsensor.rgb = tuple(kwargs.get(ATTR_RGB_COLOR))
        else:
            self._zsensor.on = True

    def turn_off(self, **kwargs):
        """Instruct the sensor to turn off."""
        self._zsensor.on = False

    def update(self):
        """Fetch new state data for this sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._zsensor.update()
