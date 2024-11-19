import sys, os
import struct
import time
import socket
import logging
import threading

class TagoEvents(object):
    def __init__(self, host, port, stop):
        self.sock = None
        self.host = host
        self.port = port
        self.stop = stop

    def disconnect(self):
        if self.sock:
            logging.info(f'Disconnecting from {self.host}:{self.port} for events')
            self.sock.close()
        self.sock = None

    def connect(self):
        if self.sock is not None:
            return

        logging.debug(f'Connecting to {self.host}:{self.port} for events')
        self.sock= socket.create_connection(address=(self.host, self.port), timeout=3)
        self.sock.settimeout(None)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 5)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)
        except:
            pass

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        logging.info(f'Connected to {self.host}:{self.port}')

    def start(self, callback):
        self.callback = callback
        thread = threading.Thread(target=self.next).start()

    def next(self):
        while not self.stop.is_set():
            try:
                while not self.stop.is_set():
                    time.sleep(0.25)
                    self.connect()
                    data = self.sock.recv(6)
                    if len(data) == 0:
                        self.disconnect()
                        break

                    if len(data) < 6:
                        continue

                    length = struct.unpack('>H', data[4:])[0]
                    if length > 24:
                        continue

                    data = bytes()
                    while len(data) < length:
                        read_data = self.sock.recv(length - len(data))
                        if len(read_data) == 0:
                            self.disconnect()
                            break

                        data += read_data

                    logging.info(f'read {len(data)} bytes from MODBUS TCP')

                    (addr, fc) = struct.unpack('<BB', data[0:2])
                    data = data[2:]

                    now = int(time.time() * 1000)
                    ## RS485 Message
                    if fc == 3:
                        key, duration = struct.unpack('BB', data[4:])
                        if duration > 1:
                          duration = 'long'
                        else:
                          duration = 'short'

                        self.callback(addr, key, duration)

            except Exception as e:
                logging.error(f'TagoEvents Exception: {e}')
                time.sleep(1)
            finally:
                try:
                    self.disconnect()
                except:
                    pass
        