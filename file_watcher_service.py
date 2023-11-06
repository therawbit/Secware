import threading
from watchdog.observers import Observer
import time
from file_watcher import FileWatcher

class FileWatcherService(threading.Thread):
    def __init__(self, app, watch_folder):
        super().__init__()
        self.app = app
        self.watch_folder = watch_folder
        self.running = True

    def run(self):
        observer = Observer()
        event_handler = FileWatcher(self.app)
        observer.schedule(event_handler, path=self.watch_folder, recursive=True)
        observer.start()

        while self.running:
            time.sleep(1)

        observer.stop()
        observer.join()

    def stop(self):
        self.running = False