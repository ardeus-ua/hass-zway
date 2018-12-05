import logging

import voluptuous as vol

from homeassistant.components.climate import (ClimateDevice, PLATFORM_SCHEMA, 
    SUPPORT_TARGET_TEMPERATURE, ATTR_OPERATION_MODE, SUPPORT_OPERATION_MODE, 
    ATTR_AWAY_MODE, SUPPORT_AWAY_MODE, DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP, 
    STATE_AUTO)
from homeassistant.const import CONF_NAME, CONF_URL, CONF_USERNAME, CONF_PASSWORD, 
    ATTR_UNIT_OF_MEASUREMENT, ATTR_TEMPERATURE
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['https://github.com/ardeus-ua/pyzway/archive/master.zip#pyzway==0.3.0']

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_USERNAME, default='admin'): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_INCLUDE): cv.string
})

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_AWAY_MODE)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup Z-Way Climate platform."""

    import zway

    zwc = zway.controller.Controller(baseurl=config.get(CONF_URL),
                                     username=config.get(CONF_USERNAME),
                                     password=config.get(CONF_PASSWORD))

    include = config.get(CONF_INCLUDE)
    devices = []
    for dev in zwc.devices:
        if dev.is_tagged(include):
            if (isinstance(dev, zway.devices.Climate):
                _LOGGER.info("Including %s %s: %s", dev.devicetype, dev.id, dev.title)
                devices.append(ZWayClimate(dev))
    add_devices(devices)


class ZWayClimate(Climate):
    """Representation of an Z-Way Climate"""

    def __init__(self, device):
        self._zlight = device

    @property
    def unique_id(self):
        """Return the ID of this climate."""
        return self._zclimate.id.lower()

    @property
    def name(self):
        """Return the display name of this climate."""
        return self._zclimate.title

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_ZWAY.get(self._zclimate.devicetype, 0)

    @property
    def is_on(self):
        """Return true if climate is on."""
        return self._zclimate.on

    @property
    def temperature(self):
        """Temparature"""
        if self._zclimate.devicetype == 'climate':
            return self._zclimate.level
        else:
            return None

    @property
    def rgb_color(self):
        """Return the RGB color value."""
        if self._zclimate.devicetype == 'switchRGBW' and self._zclimate.rgb is not None:
            return list(self._zclimate.rgb)
        else:
            return None

    def turn_on(self, **kwargs):
        """Instruct the climate to turn on."""
        if self._zclimate.devicetype == 'switchMultilevel':
            self._zclimate.level = kwargs.get(ATTR_BRIGHTNESS, 255)
        elif self._zclimate.devicetype == 'switchRGBW':
            self._zclimate.rgb = tuple(kwargs.get(ATTR_RGB_COLOR))
        else:
            self._zclimate.on = True

    def turn_off(self, **kwargs):
        """Instruct the climate to turn off."""
        self._zclimate.on = False

    def update(self):
        """Fetch new state data for this climate.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._zclimate.update()
