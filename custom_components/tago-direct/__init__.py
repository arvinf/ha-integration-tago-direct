"""The Tago integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, ATTR_ID

import logging

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)

_thread = None

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    _LOGGER.info('Tago Direct setup v1.1')

    cfg = config.get(DOMAIN)
    _LOGGER.info('Host cfg {}'.format(cfg))
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Enphase Envoy from a config entry."""

    config = entry.data
    host = config[CONF_HOST]
    
    _LOGGER.info('Bridge address {}'.format(host))

    global _thread
    _thread = ButtonThread(hass, host)
    _thread.start()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    global _thread
    if _thread:
      _thread.stop()
      _thread.join()

    return True

import threading
import socket
import struct
import time
# import hexdump

class ButtonThread(threading.Thread):
  def __init__(self, hass, url):
    threading.Thread.__init__(self)

    ## Extract port from host url if provided
    parts = url.split(':')
    if len(parts) > 1:
        port = int(parts[1])
    else:
        port = 27
    host = parts[0]

    self.run_thread = True
    self.hass = hass
    self.host = host
    self.port = port

  def connect(self):
    _LOGGER.info ("Connecting to RS485 bridge {host} {port}".format(host=self.host, port=self.port))
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.settimeout(3)
    self.sock.connect((self.host, self.port))
    _LOGGER.info ("Connected")

  def modbus_get_next(self):
    # get header
    data = self.sock.recv(6)
    length = struct.unpack('>H', data[4:])[0]
    data = bytes()
    while len(data) < length:
        data += self.sock.recv(length - len(data))

    return data

  def stop(self):
    self.run_thread = False

  def run(self):
    while self.run_thread:
      try:
        self.connect()
        while self.run_thread:
          data = self.modbus_get_next()
          _LOGGER.info('\nPacket {} bytes'.format(len(data)))
          # hexdump.hexdump(data)

          (addr, fc) = struct.unpack('<BB', data[0:2])
          data = data[2:]
          ## tagonet message
          if fc == 3:
            key, presslength = struct.unpack('BB', data[4:])
            if presslength > 1:
              duration = 'long'
            else:
              duration = 'short'
            _LOGGER.info('Switch Event addr: 0x{:2x} key: {} duration: {}'.format(addr, key, duration))
                  
          data = {ATTR_ID: '{}-{}-{}'.format(addr,key,presslength), 
                  'action': 'single', 
                  'addr': '0x{:2x}'.format(addr), 
                  'key': key, 
                  'duration': duration}
          self.hass.bus.fire("tago_event", data)
      except Exception as e:
        _LOGGER.error(e)
        self.sock = None
      finally:
        if self.run_thread:
          time.sleep(2)
    logging.warning('Exiting')
