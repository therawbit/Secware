import os
import logging
import subprocess
import tempfile
import pandas as pd
from watchdog.events import FileSystemEventHandler
import tempfile
from collections import deque
from plyer import notification


class FileWatcher(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        self.file_queue = deque()
        self.processing = False
        

    def on_created(self, event):
        if not event.src_path.startswith(
            tempfile.gettempdir()
        ) and self.is_pe_executable(event.src_path):
            logging.info(f"New file: {event.src_path}")
            self.show_notification(event.src_path)
            self.file_queue.append(event.src_path)
            self.process_queue()

    def process_queue(self):
        if not self.processing and self.file_queue:
            self.processing = True
            file_path = self.file_queue.popleft()
            self.invoke_external_system_call(file_path)

    def show_notification(self, file_path):
        notification_title = "New .exe File Detected"
        notification_message = f"New .exe file detected: {os.path.basename(file_path)}. Please do not run it until we verify its safety"
        notification.notify(
            title=notification_title,
            message=notification_message,
            timeout=2
        )

    def invoke_external_system_call(self, file_path):
        objdump_path = "objdump.exe"
        arguments = f"-M intel -D {file_path}"
        assembly_code = subprocess.check_output([objdump_path, *arguments.split()], text=True)
        self.extract_features(assembly_code)
        assembly_code = None

    def is_pe_executable(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                data = file.read(2)
            return data == b'MZ'  # Check for the MZ magic number at the beginning of the file
        except Exception as e:
            return False



    def extract_features(self, assembly_code):
        fields = [
            "jmp",
            "mov",
            "retf",
            "push",
            "pop",
            "xor",
            "retn",
            "nop",
            "sub",
            "inc",
            "dec",
            "add",
            "imul",
            "xchg",
            "or",
            "shr",
            "cmp",
            "call",
            "shl",
            "ror",
            "rol",
            "jnb",
            "jz",
            "rtn",
            "lea",
            "movzx",
            "edx",
            "esi",
            "eax",
            "ebx",
            "ecx",
            "edi",
            "ebp",
            "esp",
            "eip",
        ]

        # Initialize a dictionary to store field counts and section line counts
        data = {field: 0 for field in fields}
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

        # Create a DataFrame from the dictionary
        df = pd.DataFrame([data])

        df.to_csv("test.csv", index=False)
