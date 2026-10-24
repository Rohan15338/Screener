import socket
import threading
from typing import Callable, Optional

DEFAULT_PORT = 49281

class SingleInstance:
    """
    Ensures only one instance of Screener runs on the system.
    If another instance is launched, it notifies the running instance to show its window and exits.
    """
    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self.sock: Optional[socket.socket] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._is_running = False

    def check_or_register(self, on_show_requested: Optional[Callable[[], None]] = None) -> bool:
        """
        Returns True if this is the primary instance.
        Returns False if another instance is already running (after signaling it).
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(("127.0.0.1", self.port))
            self.sock.listen(5)
            self._is_running = True

            if on_show_requested:
                self._start_listener(on_show_requested)
            return True
        except socket.error:
            # Another instance already bound to the port
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            self._notify_existing_instance()
            return False

    def _notify_existing_instance(self):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect(("127.0.0.1", self.port))
            sock.sendall(b"SHOW\n")
        except Exception:
            pass
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    def _start_listener(self, on_show_requested: Callable[[], None]):
        def _listen():
            while self._is_running and self.sock:
                try:
                    conn, _ = self.sock.accept()
                    data = conn.recv(1024)
                    if b"SHOW" in data:
                        on_show_requested()
                    conn.close()
                except Exception:
                    break

        self._listener_thread = threading.Thread(target=_listen, daemon=True)
        self._listener_thread.start()

    def close(self):
        self._is_running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
