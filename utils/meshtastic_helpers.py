# utils/meshtastic_helpers.py

import threading
import logging
import traceback
from pathlib import Path
import serial.tools.list_ports
import meshtastic.serial_interface


def _build_logger():
    """Create a file + console logger for connection diagnostics."""
    logger = logging.getLogger("mdeck.meshtastic")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "mdeck.log"

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


LOGGER = _build_logger()


def _serial_error_with_hints(error):
    """Build a readable serial error string with Linux troubleshooting hints."""
    message = str(error)
    lower_msg = message.lower()
    hints = []

    if "permission" in lower_msg or "access is denied" in lower_msg:
        hints.append("permission denied: add your user to dialout and re-login")
    if "resource busy" in lower_msg or "device or resource busy" in lower_msg:
        hints.append("device busy: close other serial apps and stop ModemManager")
    if "no such file" in lower_msg or "cannot open" in lower_msg:
        hints.append("port disappeared: unplug/replug USB and re-scan ports")

    if not hints:
        hints.append("check logs/mdeck.log for full traceback")

    return f"{message}. Hints: {'; '.join(hints)}"

# Try importing TCP interface
try:
    from meshtastic import tcp_interface
    TCP_AVAILABLE = True
except ImportError:
    TCP_AVAILABLE = False
    print("Warning: TCP interface not available. Network connections will not work.")
    LOGGER.warning("TCP interface import failed; network connections disabled")


class MeshtasticHandler:
    """Singleton handler for Meshtastic serial and network connections with connection callbacks."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.interface = None
                    cls._instance._connection_lock = threading.Lock()
                    cls._instance._connected_port = None
                    cls._instance._connection_type = None
                    cls._instance._connection_info = None
                    cls._instance._last_error = None
                    cls._instance._last_traceback = None
                    cls._instance._callbacks = []  # <-- list of connection state change callbacks
        return cls._instance

    # --- Callback registration ---
    def register_callback(self, callback):
        """Register a function to be called on connect/disconnect events."""
        if callable(callback) and callback not in self._callbacks:
            self._callbacks.append(callback)

    def _run_callbacks(self):
        """Call all registered callbacks in a thread-safe way."""
        for cb in self._callbacks:
            try:
                cb()
            except Exception as e:
                print(f"Callback error: {e}")
                LOGGER.exception("Connection callback failed")

    # --- Serial scanning ---
    def scan_serial_ports(self):
        """Scan available serial ports."""
        ports = serial.tools.list_ports.comports()
        LOGGER.debug("Serial scan found %d port(s)", len(ports))
        return [{"device": p.device, "description": p.description, "hwid": p.hwid} for p in ports]

    # --- Connect ---
    def connect(self, port=None, hostname=None, portnum=None):
        with self._connection_lock:
            if self.interface:
                raise Exception("Already connected. Disconnect first.")

            self._last_error = None
            self._last_traceback = None

            # --- Network connection ---
            if hostname:
                if not TCP_AVAILABLE:
                    raise Exception("TCP interface not available.")
                portnum = portnum or 4403
                LOGGER.info("Attempting TCP connection to %s:%s", hostname, portnum)
                try:
                    self.interface = tcp_interface.TCPInterface(hostname=hostname, portNumber=portnum)
                    self._connection_type = 'network'
                    self._connected_port = f"{hostname}:{portnum}"
                    self._connection_info = self._connected_port
                    LOGGER.info("TCP connection established to %s", self._connected_port)
                except Exception as e:
                    self._last_error = f"Failed to connect via TCP: {e}"
                    self._last_traceback = traceback.format_exc()
                    LOGGER.error(self._last_error)
                    LOGGER.debug(self._last_traceback)
                    raise Exception(f"Failed to connect via TCP: {e}")
                finally:
                    self._run_callbacks()
                return self.interface

            # --- Serial connection ---
            try:
                if port:
                    LOGGER.info("Attempting serial connection on %s", port)
                    self.interface = meshtastic.serial_interface.SerialInterface(devPath=port)
                else:
                    available_ports = self.scan_serial_ports()
                    if not available_ports:
                        raise Exception("No serial ports found.")
                    LOGGER.info("No serial port chosen; using first detected port %s", available_ports[0]["device"])
                    self.interface = meshtastic.serial_interface.SerialInterface(devPath=available_ports[0]["device"])

                # Set connected info
                if hasattr(self.interface, "port") and self.interface.port:
                    self._connected_port = self.interface.port
                    self._connection_info = self.interface.port
                elif hasattr(self.interface, "stream") and hasattr(self.interface.stream, "port"):
                    self._connected_port = self.interface.stream.port
                    self._connection_info = self.interface.stream.port

                self._connection_type = 'serial'
                LOGGER.info("Serial connection established on %s", self._connected_port)
            except Exception as e:
                self._last_error = f"Serial connection failed: {_serial_error_with_hints(e)}"
                self._last_traceback = traceback.format_exc()
                LOGGER.error(self._last_error)
                LOGGER.debug(self._last_traceback)
                raise Exception(self._last_error)
            finally:
                self._run_callbacks()  # <-- refresh tabs/UI on connect
            return self.interface

    # --- Disconnect ---
    def disconnect(self):
        with self._connection_lock:
            if self.interface:
                try:
                    LOGGER.info("Disconnecting from %s", self._connected_port)
                    self.interface.close()
                except:
                    pass
            self.interface = None
            self._connected_port = None
            self._connection_type = None
            self._connection_info = None
            self._run_callbacks()  # <-- refresh tabs/UI on disconnect

    # --- Status helpers ---
    def is_connected(self):
        if not self.interface:
            return False
        try:
            return hasattr(self.interface, 'port') or hasattr(self.interface, 'stream') or hasattr(self.interface, 'hostname')
        except:
            return False

    def get_interface(self):
        if not self.interface:
            raise Exception("Not connected.")
        return self.interface

    def get_connected_port(self):
        return self._connected_port

    def get_connection_type(self):
        return self._connection_type

    def get_connection_info(self):
        return self._connection_info

    def get_last_error(self):
        return self._last_error

    def get_last_traceback(self):
        return self._last_traceback

    @classmethod
    def get_instance(cls):
        return cls()
