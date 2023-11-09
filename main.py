import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog,QTableWidgetItem,QHeaderView
from PyQt5 import uic,QtGui
from file_watcher_service import FileWatcherService
from PyQt5.QtCore import pyqtSlot
import logging
import os
from database_manager import DatabaseManager
class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_ui.ui", self)  # Load your UI file
        self.watch_folder = ""
        self.btn_home.clicked.connect(self.show_home_page)
        self.btn_history.clicked.connect(self.show_history_page)
        self.btn_logs.clicked.connect(self.show_logs_page)
        self.btn_about.clicked.connect(self.show_about_page)
        self.btn_file_chooser.clicked.connect(self.choose_folder)
        self.btn_load_log.clicked.connect(self.load_logs)
        self.logs_view.setReadOnly(True)
        self.file_watcher = None
        self.is_watching = False  # Flag to track the service state
        self.is_history_loaded = False
        
        # Connect the Start and Stop buttons
        self.btn_start.clicked.connect(self.start_watching)
        self.btn_stop.clicked.connect(self.stop_watching)

        self.database_manager = DatabaseManager("secware.db")
        
        

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

    def load_logs(self):
        self.logs_view.setText("")
        log_lines = self.tail(100)
        for line in log_lines:
            self.logs_view.append(line.decode())
        log_lines = None

    def tail(self,n):
        with open('service.log', 'rb') as file:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            newline_count = 0
            buffer_size = 4096  # Adjust this value based on your needs

            while file_size > 0 and newline_count < n:
                if file_size < buffer_size:
                    buffer_size = file_size
                file.seek(-buffer_size, os.SEEK_CUR)
                buffer = file.read(buffer_size)
                newline_count += buffer.count(b'\n')
                file_size -= buffer_size

            file.seek(0, os.SEEK_SET)
            lines = file.read().splitlines()[-n:]
            return lines
    
    def show_home_page(self):
        self.stackedWidget.setCurrentIndex(0)

    def show_history_page(self):
        self.stackedWidget.setCurrentIndex(2)
        if not self.is_history_loaded:
            results = self.database_manager.fetch_data()
            for row_data in results:
                row_number = self.table_view.rowCount()
                self.table_view.insertRow(row_number)

                for col_number, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    self.table_view.setItem(row_number, col_number, item)
            self.is_history_loaded=True
            header = self.table_view.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)

        
    def show_logs_page(self):
        self.stackedWidget.setCurrentIndex(3)

    def show_about_page(self):
        self.stackedWidget.setCurrentIndex(1)

if __name__ == '__main__':
    logging.basicConfig(filename="service.log", level=logging.INFO, format='%(asctime)s - %(message)s')
    app = QApplication(sys.argv)
    window = MyApp()
    window.setWindowTitle("Secware")
    window.setWindowIcon(QtGui.QIcon("icons/favicon.ico"))
    window.show()
    window.stackedWidget.setCurrentIndex(0)
    sys.exit(app.exec_())
