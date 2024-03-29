import customtkinter as ctk
from tkinter import filedialog

def select_path():
    file_path = filedialog.askdirectory()
    print(f"Selected path: {file_path}")

root = ctk.CTk()

root.geometry("720x480")
root.title("Signal Acquisition")

# Create a frame for the left side
left_frame = ctk.CTkFrame(root,width = 300, height = 500)
left_frame.pack(side=ctk.LEFT,fill='both',expand=True)

# Create a frame for the right side
right_frame = ctk.CTkFrame(root,width = 300, height = 500)
right_frame.pack(side=ctk.RIGHT,fill='both',expand=True)

def checkbox_ev():
    print(f"RP1: {rp1.get()}")
    print(f"RP2: {rp2.get()}")
    print(f"RP3: {rp3.get()}")

# Create the checkboxes
rp1 = ctk.CTkCheckBox(right_frame, text="RP1", command=checkbox_ev)
rp2 = ctk.CTkCheckBox(right_frame, text="RP2", command=checkbox_ev)
rp3 = ctk.CTkCheckBox(right_frame, text="RP3", command=checkbox_ev)
rp1.pack(anchor='center')
rp2.pack(anchor='center')
rp3.pack(anchor='center')





def startAcq():
    if rp1.get():
        print("Checkbox RP1 is selected")
    if rp2.get():
        print("Checkbox RP2 is selected")
    if rp3.get():
        print("Checkbox RP3 is selected")


# Create the Start Acquisition button
start_button = ctk.CTkButton(left_frame, text="Start Acquisition",command = startAcq)
start_button.pack(anchor='center')







# Create the path selection button
path_button = ctk.CTkButton(right_frame, text="Select Path", command=select_path)
path_button.pack()



root.mainloop()
