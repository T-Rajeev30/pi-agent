import shutil
import logging
from config import VIDEO_DIR

log = logging.getLogger(__name__)

class StorageManager:

    def __init__(self, config_manager):
        self.config_manager = config_manager

    def check_storage_space(self):

        total, used, free = shutil.disk_usage(VIDEO_DIR)

        used_percent = used / total * 100

        log.info(f"[Storage] Used {used_percent:.2f}%")

        return used_percent
