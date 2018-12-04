import logging

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.sensor import DOMAIN
from homeassistant.const import CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_INCLUDE
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pyzway==0.2.0']

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_USERNAME, default='admin'): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_INCLUDE): cv.string
})

SUPPORT_ZWAY = {
    'switchBinary': 0,
    'switchMultilevel': SUPPORT_BRIGHTNESS,
    'switchRGBW': SUPPORT_RGB_COLOR
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup Z-Way Light platform."""

    import zway

    zwc = zway.controller.Controller(baseurl=config.get(CONF_URL),
                                     username=config.get(CONF_USERNAME),
                                     password=config.get(CONF_PASSWORD))

    include = config.get(CONF_INCLUDE)
    devices = []
    for dev in zwc.devices:
        if dev.is_tagged(include):
            if (isinstance(dev, zway.devices.SwitchBinary) or
                    isinstance(dev, zway.devices.SwitchMultilevel) or
                    isinstance(dev, zway.devices.SwitchRGBW)):
                _LOGGER.info("Including %s %s: %s", dev.devicetype, dev.id, dev.title)
                devices.append(ZWayLight(dev))
    add_devices(devices)


class ZWayLight(Light):
    """Representation of an Z-Way Light"""

    def __init__(self, device):
        self._zlight = device

    @property
    def unique_id(self):
        """Return the ID of this light."""
        return self._zlight.id.lower()

    @property
    def name(self):
        """Return the display name of this light."""
        return self._zlight.title

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_ZWAY.get(self._zlight.devicetype, 0)

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._zlight.on

    @property
    def brightness(self):
        """Brightness of the light (an integer in the range 1-255)."""
        if self._zlight.devicetype == 'switchMultilevel':
            return self._zlight.level
        else:
            return None

    @property
    def rgb_color(self):
        """Return the RGB color value."""
        if self._zlight.devicetype == 'switchRGBW' and self._zlight.rgb is not None:
            return list(self._zlight.rgb)
        else:
            return None

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        if self._zlight.devicetype == 'switchMultilevel':
            self._zlight.level = kwargs.get(ATTR_BRIGHTNESS, 255)
        elif self._zlight.devicetype == 'switchRGBW':
            self._zlight.rgb = tuple(kwargs.get(ATTR_RGB_COLOR))
        else:
            self._zlight.on = True

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._zlight.on = False

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._zlight.update()
