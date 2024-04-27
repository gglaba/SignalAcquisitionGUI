import tkinter
import customtkinter as ctk
import os
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import ConnectionManager
from CTkMessagebox import CTkMessagebox
from ProgressWindow import ProgressWindow
from CheckBoxesFrame import CheckBoxesFrame


load_dotenv()

masterRP = os.getenv("MASTERRP")
slave1 = os.getenv("SLAVE1")
slave2 = os.getenv("SLAVE2")
private_key_path = os.getenv("PRIVATE_KEY_PATH")
testpath = os.getenv("PRIVATE_KEY_PATHTEST")
testip = os.getenv("TESTIP")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
testusername = os.getenv("TESTUSERNAME")
testpassword = os.getenv("TESTPASSWORD")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.command = "cd /home/grzesiula/Desktop/dev && ./a.out"
        self.connections = []
        self.error_queue = queue.Queue()
        self.selected_ips = []
        self.title("RedPitaya Signal Acquisition")
        self.geometry("400x400")
        self.grid_columnconfigure(0, weight=1)
        self.checkboxes_frame = CheckBoxesFrame(self, "Devices", values=[masterRP, slave1, slave2, testip])
        self.checkboxes_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsw")

        self.connect_button = ctk.CTkButton(self, text="Connect to Pitayas", command=self.start_connect_to_devices_thread)
        self.connect_button.grid(row=3, column=0, padx=10, pady=10)

        self.acquire_button = ctk.CTkButton(self, text="Acquire Signals", command=self.open_progress_window)
        self.acquire_button.grid(row=4, column=0, padx=10, pady=10)
        self.acquire_button.configure(state="disabled")

        self.check_errors()
        self.check_new_checked_boxes()

    def check_new_checked_boxes(self):
        selected_ips = self.checkboxes_frame.get()
        if selected_ips != self.selected_ips:
            self.selected_ips = selected_ips
            self.connect_button.configure(state="normal")
        elif len(self.selected_ips) == len(self.connections):
            self.connect_button.configure(state="disabled")
        self.after(100, self.check_new_checked_boxes)

    def check_errors(self):
        try:
            error_message = self.error_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self.show_error(error_message)
        self.after(100, self.check_errors)

    def show_error(self,error_text):
        tkinter.messagebox.showerror("Error",error_text)

    def open_progress_window(self):
        self.progress_window = ProgressWindow(self)
        self.progress_window.focus_set()
        self.progress_window.attributes('-topmost', True)
        self.acquire_button.configure(state="disabled")
        self.start_acquisition_thread()

    def start_connect_to_devices_thread(self):
        self.connect_button.configure(state="disabled")
        threading.Thread(target=self.connect_to_devices).start()
        
    def connect_to_devices(self):
        self.selected_ips = self.checkboxes_frame.get()
        with ThreadPoolExecutor(max_workers=len(self.selected_ips)) as executor:
            for ip in self.selected_ips:
                if ip not in [connection.ip for connection in self.connections]:
                    executor.submit(self.connect_to_device, ip)

    def connect_to_device(self, ip):
            try:
                rp = ConnectionManager.ConnectionManager(self, ip, testusername, testpassword, testpath)
                if rp.connect() and rp.client is not None:
                    self.connections.append(rp)
                    output = rp.execute_command(f"echo 'Connected to {ip}'")
                    self.checkboxes_frame.update_label(ip, "Connected")
                    self.checkboxes_frame.show_disconnect_button(ip)
                    self.acquire_button.configure(state="normal")
                else:
                    raise Exception(f"Failed to connect to {ip}")
            except Exception as e:
                self.error_queue.put(str(e) + f" {ip}")
                self.checkboxes_frame.update_label(ip, "Failed to connect")
                self.connect_button.configure(state="normal")

    def start_acquisition_thread(self):
        threading.Thread(target=self.start_acquisition, args=(self.command,), daemon=True).start()

    def start_acquisition(self, command):
        for connection in self.connections:
            threading.Thread(target=self.run_acquisition, args=(connection, command), daemon=True).start()

    def run_acquisition(self, connection, command):
        self.acquire_button.configure(state="normal")
        try:
            stdout, stderr = connection.execute_command(command)
            connection.start_listener()
        except Exception as e:
            e_msg = f"{connection}: {str(e)}"
            print(e_msg)
        finally:
            self.progress_window.close()

    def disconnect_from_device(self, ip):
        for connection in self.connections:
            if connection.ip == ip:
                connection.disconnect()
                self.connections.remove(connection)
                self.checkboxes_frame.update_label(ip, "Disconnected")
                self.checkboxes_frame.hide_disconnect_button(ip)
                self.connect_button.configure(state="normal")
                break

    def destroy(self):
        for connection in self.connections:
            connection.disconnect()
        super().destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()