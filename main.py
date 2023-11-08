import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5 import uic
from file_watcher_service import FileWatcherService
from PyQt5.QtCore import pyqtSlot
import logging

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_ui.ui", self)  # Load your UI file
        self.watch_folder = ""
        self.btn_home.clicked.connect(self.show_page1)
        self.btn_history.clicked.connect(self.show_page2)
        self.btn_file_chooser.clicked.connect(self.choose_folder)
        self.file_watcher = None
        self.is_watching = False  # Flag to track the service state
        
        # Connect the Start and Stop buttons
        self.btn_start.clicked.connect(self.start_watching)
        self.btn_stop.clicked.connect(self.stop_watching)

    @pyqtSlot()
    def start_watching(self):
        if not self.is_watching:
            watch_folder = self.edit_watch_folder.text()
            if watch_folder:
                self.file_watcher = FileWatcherService(self, watch_folder)
                self.file_watcher.start()
                self.is_watching = True
                self.btn_start.setEnabled(False)
                self.btn_stop.setEnabled(True)
                self.label_watch.setText("Watching")
            else:
                self.label_watch.setText("Select a folder to watch")
                
    @pyqtSlot()
    def stop_watching(self):
        if self.is_watching:
            self.file_watcher.stop()
            self.file_watcher.join()
            self.is_watching = False
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.label_watch.setText("Stopped")

    def choose_folder(self):
        self.watch_folder = QFileDialog.getExistingDirectory(self,"Select Folder")
        self.edit_watch_folder.setText(self.watch_folder)
    def show_page1(self):
        self.stackedWidget.setCurrentIndex(0)

    def show_page2(self):
        self.stackedWidget.setCurrentIndex(1)

    def show_page3(self):
        self.stackedWidget.setCurrentIndex(2)

if __name__ == '__main__':
    logging.basicConfig(filename="service.log", level=logging.INFO, format='%(asctime)s - %(message)s')
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    window.stackedWidget.setCurrentIndex(0)
    sys.exit(app.exec_())
