import pytest
import threading
import time
from unittest.mock import MagicMock

from your_module_path.deye_modbus import DeyeModbus  # Pfad anpassen


class DummyConnector:
    def __init__(self, delay=0.1):
        self.send_request = MagicMock(side_effect=self._mock_send)
        self.delay = delay
        self.requests_sent = []

    def _mock_send(self, frame):
        # Simuliere kurze Wartezeit wie beim echten Gerät
        time.sleep(self.delay)
        self.requests_sent.append(frame)
        # Simuliere eine gültige Modbus-Antwort (CRC ok, Adresse ok, Werte leer)
        # Hier einfache Fake-Daten passend zu den Parser-Anforderungen
        return b"\x01\x03\x02\x00\x00" + b"\x00\x00"  # CRC 0 für Test-Zwecke


def test_read_and_write_are_locked():
    connector = DummyConnector()
    modbus = DeyeModbus(connector)

    def read_job():
        modbus.read_registers(10, 11)

    def write_job():
        modbus.write_register_uint(20, 123)

    # Starte Lese- und Schreib-Threads fast gleichzeitig
    t1 = threading.Thread(target=read_job)
    t2 = threading.Thread(target=write_job)

    start_time = time.time()
    t1.start()
    time.sleep(0.01)  # minimaler Offset, um Überschneidung zu provozieren
    t2.start()
    t1.join()
    t2.join()
    elapsed = time.time() - start_time

    # Da beide Funktionen mit Lock laufen und DummyConnector.delay=0.1,
    # müssen die Zeiten addiert werden → Laufzeit > 0.2s
    assert elapsed >= 0.2, "Lock scheint nicht zu greifen, Operationen liefen parallel"

    # Prüfen, ob beide Requests tatsächlich gesendet wurden
    assert len(connector.requests_sent) == 2
