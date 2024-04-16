from tkinter import *
import customtkinter as ctk
import os
from dotenv import load_dotenv
import ConnectionManager
import threading

load_dotenv()

masterRP = os.getenv("MASTERRP")
slave1 = os.getenv("SLAVE1")
slave2 = os.getenv("SLAVE2")
private_key_path = os.getenv("PRIVATE_KEY_PATH")

class CheckBoxesFrame(ctk.CTkFrame):
    def __init__(self,master,title,values):
        super().__init__(master)
        self.values = values
        self.title = title
        self.checkboxes = []

        for i,value in enumerate(self.values):
            checkbox = ctk.CTkCheckBox(self,text = value)
            checkbox.grid(row=i+1, column=0, padx=10, pady=(10,0), sticky="w")
            self.checkboxes.append(checkbox)
        
        self.title = ctk.CTkLabel(self,text = self.title,fg_color = "gray30",corner_radius = 5)
        self.title.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")


    def get(self):
        selected_ips = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                selected_ips.append(checkbox.cget("text"))
        return selected_ips
        

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.connections =[]

        self.password ="root"
        self.selected_ips = []


        self.title("RedPitaya Signal Acquisition")
        self.geometry("720x480")
        self.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self, text="Not connected", fg_color="red", font=("",20))
        self.status_label.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.checkboxes_frame = CheckBoxesFrame(self,"Devices",values =[masterRP,slave1,slave2])
        self.checkboxes_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsw")

        self.button = ctk.CTkButton(self,text = "Connect to Pitayas", command = self.connect_to_devices)
        self.button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.button = ctk.CTkButton(self,text = "Send Acquire Command", command = lambda: self.execute_commands("cd RedPitaya/G && ./send_acquire"))
        self.button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
#use ConnectionManager to connect to ip checked in checkboxes
    def connect_to_devices(self):
        self.selected_ips = self.checkboxes_frame.get()
        rp1, rp2, rp3 = None, None, None
        for ip in self.selected_ips:
            if ip == masterRP:
                rp1 = ConnectionManager.ConnectionManager(ip, "root", self.password, private_key_path)
                if rp1.connect():
                    self.connections.append(rp1)
                    if rp1.client is not None:
                        output = rp1.execute_command("echo 'Connected to MasterRP'")
                        print(output)  # print output to console
                        for line in output:
                            self.status_label.configure(text=f"MasterRP: {line}", fg_color="blue")
                    else:
                        self.status_label.configure(text="Failed to connect to MasterRP", fg_color="red")
                        return


    def execute_commands(self, command):
        def execute_command_in_thread(connection, command):
            if connection.client is not None:
                output_generator = connection.execute_command(command)
                for line in output_generator:  # iterate over the generator
                    print(f"Output: {line}")  # print output to console
                    self.status_label.configure(text=f"{connection.ip}: {line}", fg_color="blue")
                    
        for connection in self.connections:
            threading.Thread(target=execute_command_in_thread, args=(connection, command)).start()

    def destroy(self):
        for connection in self.connections:
            connection.disconnect()  # replace with your method for ending a connection
        super().destroy()
            

if __name__ == "__main__":
    app = App()
    app.mainloop()