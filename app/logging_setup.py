"""
logging_setup.py

Configuración de logging estilo Java: [TIMESTAMP] [LEVEL] [CLASS] MESSAGE
Escribe en archivo de logs con rotación diaria.
"""

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "tiltdetector.log"

# Formato estilo Java: [2026-05-04 15:30:45,123] [INFO] [ClassName] Message
JAVA_STYLE_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S,%f"


class JavaStyleFormatter(logging.Formatter):
    """Formateador que trunca microsegundos a 3 dígitos (milisegundos)."""

    def format(self, record):
        if record.created:
            ct = self.converter(record.created)
            if self.datefmt:
                s = self._style.format(record)
                # Usar el asctime original pero ajustar milisegundos
                ts = logging.Formatter.formatTime(self, record, self.datefmt)
                # ts tiene format YYYY-MM-DD HH:MM:SS,ffffff
                # Queremos solo los primeros 3 dígitos de microsegundos
                if "," in ts:
                    date_part, us = ts.split(",")
                    ms = us[:3]
                    s = s.replace(ts, f"{date_part},{ms}")
                return s
        return super().format(record)


def setup_logging():
    """Configura logging a archivo con rotación diaria."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Handler para archivo con rotación diaria
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    formatter = JavaStyleFormatter(JAVA_STYLE_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para consola (opcional, menos verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = JavaStyleFormatter(JAVA_STYLE_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


# Inicializar logging
logger = setup_logging()
