"""The Tago integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, ATTR_ID
import homeassistant.helpers.config_validation as cv

import logging
import threading
import time
import os
from .tagoevents import TagoEvents
from .const import DOMAIN, CONF_NET_BRIDGE_URL
import voluptuous as vol


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                {
                    vol.Required(CONF_NET_BRIDGE_URL): cv.string,
                }
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)

stop_event = threading.Event()

def run_server(bridge_url, hass):
  global stop_event
  ## Extract port from host url if provided
  parts = bridge_url.split(':')
  if len(parts) > 1:
      bridge_port = int(parts[1])
  else:
      bridge_port = 27
  bridge_host = parts[0]

  MB_HOST = os.environ.get('MB_HOST', bridge_host)
  MB_PORT = int(os.environ.get('MB_PORT', bridge_port))

  def handle_events(keypad, key, duration):
    msg = {ATTR_ID: f'{keypad}-{key}-{duration}',
                                      'action': 'single', 
                                      'addr': '0x{:2x}'.format(keypad), 
                                      'key': key, 
                                      'duration': duration}
    hass.bus.fire("tago_event", msg)

  server = TagoEvents(MB_HOST, MB_PORT, stop_event)
  server.start(handle_events)
  
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
  hass.data.setdefault(DOMAIN, {})
  logging.info('Tago Shim Setup')

  cfg = config.get(DOMAIN)
  logging.info(f'Host cfg {cfg}')
  return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  config = entry.data
  url = config[CONF_NET_BRIDGE_URL]
  logging.info(f'Modbus Bridge URL {url}')

  run_server(bridge_url=url, hass=hass)

  return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    global stop_event
    if stop_event:
      logging.info('requesting stop')
      stop_event.set()
      time.sleep(0.5)

    return True
    