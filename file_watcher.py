import os
import logging
from win10toast import ToastNotifier
import subprocess
import tempfile
import pandas as pd
from watchdog.events import FileSystemEventHandler
import tempfile
import pefile

class FileWatcher(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        logging.info("Event handler created")

    def on_created(self, event):
        if not event.src_path.startswith(tempfile.gettempdir()) and self.is_pe_executable(event.src_path):
            message = f"New .exe file created: {event.src_path}"
            logging.info(message)
            self.show_notification(event.src_path)
            self.invoke_external_system_call(event.src_path)

    def show_notification(self, file_path):
        notification_title = "New .exe File Detected"
        notification_message = f"New .exe file detected: {os.path.basename(file_path)}. Please do not run it until we verify its safety"
        toaster = ToastNotifier()
        toaster.show_toast(notification_title, notification_message)

    def invoke_external_system_call(self, file_path):
        objdump_path = r"C:\Users\Sudarshan\Downloads\Secware-main\Secware-main\src\objdump.exe"
        arguments = f"-M intel -D {file_path}"
        file_name_without_extension = os.path.splitext(os.path.basename(file_path))[0]
        temp_output_file = os.path.join(tempfile.gettempdir(), f"{file_name_without_extension}.asm")
        try:
            result = subprocess.run([objdump_path, *arguments.split()], capture_output=True, text=True, check=True)
            if result.returncode == 0:
                logging.info(f"Objdump output saved to temp file: {temp_output_file}")
                with open(temp_output_file, "w") as output_file:
                    output_file.write(result.stdout)
                self.extract_features(temp_output_file)
            else:
                logging.error("Objdump error:\n", result.stderr)
        except Exception as e:
            logging.error("An error occurred:", str(e))

    def extract_features(self,asm_file_path):
        section_size = self.extract_section_size(asm_file_path)

        fields = ["jmp", "mov", "retf", "push", "pop", "xor", "retn", "nop", "sub", "inc", "dec", "add", "imul", "xchg", "or", "shr", "cmp", "call", "shl", "ror", "rol", "jnb", "jz", "rtn", "lea", "movzx", "edx", "esi", "eax", "ebx", "ecx", "edi", "ebp", "esp", "eip"]

        # Initialize a dictionary to store field counts
        data = {field: [] for field in fields}

        # Process the specified file
        file_name = os.path.basename(asm_file_path)
        with open(asm_file_path, "r") as asm_file:
            content = asm_file.read()
            for field in fields:
                count = content.count(field)
                data[field].append(count)
        data.update(section_size)
        # Create a DataFrame
        df = pd.DataFrame(data)
        df.to_csv("test.csv",index=False)

    def extract_section_size(self,file_path):
        # Initialize variables to keep track of section names and line counts
        section_name = None
        line_count = 0
        section_counts = {}

        # Open the file for reading
        with open(file_path, 'r') as file:
            # Loop through each line in the file
            for line in file:
                if line.startswith("Disassembly of section"):
                    # If a new section is encountered, update the section name
                    section_name = line.split()[-1].strip(':')
                    line_count = 0
                elif section_name is not None:
                    # If a section name has been identified, increment the line count
                    line_count += 1
                    if section_name in section_counts:
                        section_counts[section_name] += 1
                    else:
                        section_counts[section_name] = 1

        return section_counts