"""The Tago integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, ATTR_ID
import homeassistant.helpers.config_validation as cv

import logging
import threading
import asyncio
import os
from .tagoevents import TagoEvents
from .tagoeventslegacy import TagoEventsLegacy
from .const import DOMAIN, CONF_NET_BRIDGE_URL, CONF_IS_TAGO_LEGACY_DEVICE

stop_event = threading.Event()


def run_server(bridge_url, hass, is_legacy):
    global stop_event
    # Extract port from host url if provided
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

    if is_legacy:
        def handle_events(action, address, key, duration):
            data = {
                "action": action,
                "keypad": address,
                "key": key,
                "duration": duration,
            }
            hass.bus.fire("tago_event", data)
        server = TagoEventsLegacy(bridge_url, stop_event, handle_events)
    else:
        server = TagoEvents(MB_HOST, MB_PORT, stop_event)
        server.start(handle_events)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    url = entry.data.get(CONF_NET_BRIDGE_URL, '')
    is_legacy = entry.data.get(CONF_IS_TAGO_LEGACY_DEVICE, False)

    run_server(bridge_url=url, hass=hass, is_legacy=is_legacy)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    global stop_event
    if stop_event:
        logging.info('requesting stop')
        stop_event.set()
        await asyncio.sleep(1.0)

    return True
