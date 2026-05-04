"""
logging_setup.py

Configuración de logging estilo Java: [TIMESTAMP] [LEVEL] [CLASS] MESSAGE
Escribe en archivo de logs con rotación diaria.
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "tiltdetector.log"


class JavaStyleFormatter(logging.Formatter):
    """Formateador estilo Java con timestamp milisegundos."""

    def format(self, record):
        # Crear timestamp con milisegundos: YYYY-MM-DD HH:MM:SS,MMM
        dt = datetime.fromtimestamp(record.created)
        ms = int((record.created % 1) * 1000)
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S") + f",{ms:03d}"

        # Construir mensaje: [TIMESTAMP] [LEVEL] [LOGGER] MESSAGE
        level = record.levelname
        logger_name = record.name
        message = record.getMessage()

        return f"[{timestamp}] [{level}] [{logger_name}] {message}"


def setup_logging():
    """Configura logging a archivo con rotación diaria."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Limpiar handlers previos si existen
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    # Handler para archivo con rotación diaria
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    formatter = JavaStyleFormatter()
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para consola (solo INFO y superior)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = JavaStyleFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


# Inicializar logging
logger = setup_logging()
