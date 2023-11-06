# main.py
import logging
from ttkbootstrap import Window
from app import MyApp

if __name__ == '__main__':
    log_filename = "service.log"
    logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')
    logging.info("Started...")
    root = Window(themename='darkly')  # Create a themed root window
    app = MyApp(root)
    root.mainloop()
