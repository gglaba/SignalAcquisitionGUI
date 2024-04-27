from tkinter import *
import customtkinter as ctk

class CheckBoxesFrame(ctk.CTkFrame):
    def __init__(self, master, title, values):
        super().__init__(master)
        self.values = values
        self.title = title
        self.checkboxes = []
        self.labels = []
        self.vars = []
        self.disconnect_buttons = {}

        for i, value in enumerate(self.values):
            checkbox = ctk.CTkCheckBox(self, text=value)
            checkbox.grid(row=i + 1, column=0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)

            disconnect_button = ctk.CTkButton(self, text="Disconnect", command=lambda ip=value: self.master.disconnect_from_device(ip))
            disconnect_button.grid(row=i + 1, column=2, padx=10, pady=(10, 0), sticky="w")
            disconnect_button.grid_remove()
            self.disconnect_buttons[value] = disconnect_button

            label = ctk.CTkLabel(self, text="Not connected", fg_color="red")
            label.grid(row=i + 1, column=1, padx=10, pady=(10, 0), sticky="w")
            self.labels.append(label)

        self.title = ctk.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=5)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

    def show_disconnect_button(self, ip):
        self.disconnect_buttons[ip].grid()
    
    def hide_disconnect_button(self, ip):
        self.disconnect_buttons[ip].grid_remove()

    def get(self):
        selected_ips = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                selected_ips.append(checkbox.cget("text"))
        return selected_ips

    def update_label(self, ip, status):
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.cget("text") == ip:
                self.labels[i].configure(text=status)
                if status == "Connected":
                    self.labels[i].configure(fg_color="green")
                else:
                    self.labels[i].configure(fg_color="red")
                break