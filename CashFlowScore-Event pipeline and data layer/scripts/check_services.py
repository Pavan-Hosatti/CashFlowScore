import socket
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SERVICES = {
    "redpanda": ("localhost", 9092),
    "redis": ("localhost", 6379),
    "postgres": ("localhost", 5432),
}


def probe(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    status = {name: probe(host, port) for name, (host, port) in SERVICES.items()}
    print(status)
