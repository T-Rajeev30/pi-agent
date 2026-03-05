import logging
import threading
import time
import psutil
import shutil

from recorder import get_status

log = logging.getLogger(__name__)

class MonitoringManager:

    def __init__(self, config_manager):
        self.config_manager = config_manager

    def start_monitoring(self):
        threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        ).start()

    def _monitoring_loop(self):

        while True:

            try:

                status = get_status()

                disk = shutil.disk_usage("/")
                free_gb = disk.free / (1024**3)

                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory().percent

                log.info(
                    f"[Monitoring] Status={status} "
                    f"DiskFree={free_gb:.2f}GB "
                    f"CPU={cpu}% "
                    f"MEM={mem}%"
                )

            except Exception as e:
                log.error(f"[Monitoring] Error {e}")

            time.sleep(60)
