from tkinter import Tk, Label
from tkinter.ttk import Button
from time import sleep
import sys, random

x = True
dev = not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'))




def end():
    global x
    x = False
    tk.destroy()

def callback():
    tk.lift()
    tk.wm_deiconify()
    tk.after(500, callback)

while x:
    tk = Tk()
    tk.wm_attributes("-topmost", True)
    tk.after(500, callback)
    tk.title("It's probably fine")
    tk.geometry(f"300x200+{random.randint(0,tk.winfo_screenwidth()-600)}+{random.randint(0,tk.winfo_screenheight()-600)}")
    label = Label(tk, text="It's probably fine.", font=("Aptos", 15))
    label.pack()
    if dev:
        btn = Button(tk, text="OK", command=end)
        btn.pack()
    tk.mainloop()
    sleep(0.1)
