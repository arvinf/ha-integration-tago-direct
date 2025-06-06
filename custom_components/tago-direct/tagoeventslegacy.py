import asyncio
import logging
import json
import websockets

class TagoEventsLegacy(object):
    def __init__(self, hostname, stop, event_callback):
        self.stop = stop
        self.hostname = hostname
        self._cb = event_callback
        self._task = asyncio.create_task(self._device_task())

    async def _device_task(self):
        uri = f"ws://{self.hostname}/api/v1/ws"
        while not self.stop.is_set():
            try:
                logging.info(f"connecting to {self.hostname}")
                async with websockets.connect(
                    uri=uri, ping_timeout=5, ping_interval=5
                ) as ws:
                    logging.info(f"connected to {self.hostname}")
                    async for message in ws:
                        msg = json.loads(message)
                        # print(msg)
                        if msg.get('evt', '') == 'modbus_keypress':
                            duration = 'long' if msg.get(
                                'duration', 0) > 1 else 'short'
                            key = msg.get('key', 0)
                            src = msg.get('src', '')
                            address = msg.get('addr', '')
                            self._cb('keypress', f'{src}:{address}', key, duration)
            except Exception as e:
                logging.exception(e)
            await asyncio.sleep(2.0)
