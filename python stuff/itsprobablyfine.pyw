from tkinter import Tk, Label, Toplevel
from tkinter.ttk import Button
from time import sleep
import sys, random


dev = not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))

def process(m=0):
    x = True
    def end():
        nonlocal x
        x = False
        tk.destroy()

    def callback():
        tk.lift()
        tk.wm_deiconify()
        tk.after(500, callback)

    while x:
        tk = Tk()
        for i in range(m):
            tp = Toplevel(tk)
            tp.wm_attributes("-topmost", True)
            tp.title("It's probably fine")
            pos = f"{random.randint(0,tk.winfo_screenwidth()-300)}+{random.randint(0,tk.winfo_screenheight()-200)}"
            tp.geometry("300x200+" + pos)
            label = Label(tp, text="It's probably fine.", font=("Aptos", 15))
            label.pack()
            if dev:
                btn = Button(tp, text="OK", command=end)
                btn.pack()
        tk.wm_attributes("-topmost", True)
        tk.after(500, callback)
        tk.title("It's probably fine")
        pos = f"{random.randint(0,tk.winfo_screenwidth()-300)}+{random.randint(0,tk.winfo_screenheight()-200)}"
        tk.geometry("300x200+" + pos)
        label = Label(tk, text="It's probably fine.", font=("Aptos", 15))
        label.pack()
        if dev:
            btn = Button(tk, text="OK", command=end)
            btn.pack()
        tk.mainloop()
        sleep(0.1)
        process(m*2+1)

process()