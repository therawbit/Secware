import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tempfile
from plyer import notification
import pandas as pd
from pathlib import Path

class Worker:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def run(self):
        event_handler = FileCreatedHandler()
        observer = Observer()
        observer.schedule(event_handler, path=self.folder_path, recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

class FileCreatedHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        if file_path.endswith(".exe"):
            print(f"New .exe file detected: {file_path}")
            self.show_notification(file_path)
            self.invoke_external_system_call(file_path)

    def invoke_external_system_call(self, file_path):
        objdump_path = "objdump"
        arguments = f"-M intel -D {file_path}" 

        file_name_without_extension = os.path.splitext(os.path.basename(file_path))[0]
        temp_output_file = os.path.join(tempfile.gettempdir(), f"{file_name_without_extension}.asm")

        try:
            result = subprocess.run([objdump_path, *arguments.split()], capture_output=True, text=True)
            if result.returncode == 0:
                print("objdump output saved to temp file:", temp_output_file)
                with open(temp_output_file, "w") as output_file:
                    output_file.write(result.stdout)
                extract_features(file_path,temp_output_file)
            else:
                print("objdump error:\n", result.stderr)
        except Exception as e:
            print("An error occurred:", str(e))

    def show_notification(self,file_path):
        notification_title = "New .exe File Detected"
        notification_message = f"New .exe file detected: {os.path.basename(file_path)}. Please do not run it until we verify its safety"
        notification.notify(
            title=notification_title,
            message=notification_message,
            app_name="Secware",
            timeout=10
        )


def extract_features(original_file_path,asm_file_path):
    section_size = extract_section_size(asm_file_path)

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

def extract_section_size(file_path):
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


if __name__ == "__main__":
    folder_path = Path.home()
    worker = Worker(folder_path)
    worker.run()
