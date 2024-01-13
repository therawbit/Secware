import os
import logging
import subprocess
import tempfile
import pandas as pd
from watchdog.events import FileSystemEventHandler
import tempfile
from collections import deque
from plyer import notification
import joblib
import hashlib
from database_manager import DatabaseManager


class FileWatcher(FileSystemEventHandler):
    def __init__(self, app):
        print("File watcher Created")
        self.app = app
        self.file_queue = deque()
        self.processing = False
        self.database_manager = None
        self.current_file = {}
        

    def on_created(self, event):
        if not event.src_path.startswith(
            tempfile.gettempdir()
        ) and self.is_pe_executable(event.src_path):
            logging.info(f"New file: {event.src_path}")
            
            sum = self.calculate_md5_sum(event.src_path)
            already_classified =self.is_classified(sum)
            if not already_classified:
                self.show_notification(event.src_path)
                self.current_file['hash'] = sum
                self.current_file['name'] = event.src_path.split('/')[-1]
                print(self.current_file)
                self.file_queue.append(event.src_path)
                self.process_queue()
            else:
                self.show_classified_notification(event.src_path.split('/')[-1],already_classified)
                print(f"{event.src_path} already classified as {already_classified}")

    def process_queue(self):
        if not self.processing and self.file_queue:
            while(self.file_queue):
                self.processing = True
                file_path = self.file_queue.popleft()
                self.invoke_external_system_call(file_path)
            self.processing = False
        

    def show_notification(self, file_path):
        notification_title = "New .exe File Detected"
        notification_message = f"New .exe file detected: {os.path.basename(file_path)}. Please do not run it until we verify its safety"
        notification.notify(
            title=notification_title,
            message=notification_message,
            timeout=2
        )
    
    def show_classified_notification(self,file_path,classified):
        notification_title = f" {classified} Identified"
        notification_message = f"{file_path}"
        notification.notify(
            title=notification_title,
            message=notification_message,
            timeout=2
        )

    def invoke_external_system_call(self, file_path):
        objdump_path = "objdump"
        arguments = f"-M intel -D {file_path}"
        assembly_code = subprocess.check_output([objdump_path, *arguments.split()], text=True)
        features = self.extract_features(assembly_code)
        assembly_code = None
        self.classify_sample(list(features.values()))


    def is_pe_executable(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                data = file.read(2)
            return data == b'MZ'  # Check for the MZ magic number at the beginning of the file
        except Exception as e:
            return False

    def classify_sample(self,features):
        self.model = joblib.load('model_ranfo_v1.joblib')
        prediction = self.model.predict([features])[0]
        self.current_file['class'] = prediction
        self.record_history(self.current_file)
        self.show_classified_notification(self.current_file['name'],prediction)
        self.current_file = None
        print(prediction)

    def extract_features(self, assembly_code):
        fields = ['.text:', '.idata:', '.data:', '.bss:', '.rdata:', '.edata:', '.rsrc:',
       '.tls:', '.reloc:', 'jmp', 'mov', 'retf', 'push', 'pop', 'xor', 'nop',
       'sub', 'inc', 'dec', 'add', 'imul', 'xchg', 'or', 'shr', 'cmp', 'call',
       'shl', 'ror', 'rol', 'jz', 'lea', 'movzx', 'edx', 'esi', 'eax', 'ebx',
       'ecx', 'edi', 'ebp', 'esp','size']

        # Initialize a dictionary to store field counts and section line counts
        data = {field: 0 for field in fields}
        size = len(assembly_code.encode('utf-8'))/(1024.0*1024.0)
        data['size'] = size
        self.current_file['size'] = size
        section_counts = {}
        section_name = None
        section_line_counts = {}  # Dictionary to store section line counts

        # Split the assembly code into lines
        lines = assembly_code.splitlines()

        # Loop through each line in the assembly code
        for line in lines:
            if line.startswith("Disassembly of section"):
                # If a new section is encountered, update the section name
                section_name = line.split()[-1].strip(":")
                section_line_counts[section_name] = 0  # Initialize the section line count
                if section_name in section_counts:
                    section_counts[section_name] += 1
                else:
                    section_counts[section_name] = 1
            elif section_name is not None:
                section_line_counts[section_name] += 1  # Increment the section line count
                for field in fields:
                    count = line.count(field)
                    data[field] += count

        # Add section line counts to the dictionary
        data.update(section_counts)
        data.update(section_line_counts)
        features = {k: v for k, v in data.items() if k in fields}
        # Create a DataFrame from the dictionary
        return features

    def is_classified(self,md5_sum):
        self.database_manager = DatabaseManager("secware.db")
        classifed = self.database_manager.check_if_exist(str(md5_sum))
        self.database_manager = None
        return classifed[0][0]

    def record_history(self,data):
        self.database_manager = DatabaseManager("secware.db")
        self.database_manager.insert_data(data)
        self.database_manager =  None

    def calculate_md5_sum(self,file_path):
        return hashlib.md5(open(file_path,"rb").read()).hexdigest()
        
