import logging
import os
from logging.handlers import RotatingFileHandler

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger("streamlit_app")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=100000, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.info("Логирование запущено")