import time
import logging

class Timer:
    def __init__(self):
        self.start_time = time.time()
        self.last_checkpoint = self.start_time

    def checkpoint(self, label: str):
        now = time.time()
        duration = now - self.last_checkpoint
        total = now - self.start_time

        logging.info(f"⏱ {label} | step: {duration:.3f}s | total: {total:.3f}s")

        self.last_checkpoint = now