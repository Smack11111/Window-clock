import argparse
import tkinter as tk
from tkinter import colorchooser, simpledialog
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description="Simple window clock")
    parser.add_argument('--bg-color', default='black', help='Background color')
    parser.add_argument('--font-size', type=int, default=48, help='Font size of the clock')
    parser.add_argument('--format', choices=['12', '24'], default='24', help='Time format (12 or 24 hour)')
    return parser.parse_args()


class WindowClock:
    def __init__(self, bg_color='black', font_size=48, time_format='24'):
        self.bg_color = bg_color
        self.font_size = font_size
        self.time_format = time_format
        self.root = tk.Tk()
        self.root.title("Window Clock")
        self.root.configure(bg=self.bg_color)

        self.label = tk.Label(self.root, fg='white', bg=self.bg_color,
                              font=('Helvetica', self.font_size))
        self.label.pack(padx=20, pady=20)

        self.create_menu()
        self.update_clock()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Background Color", command=self.change_bg_color)
        settings_menu.add_command(label="Font Size", command=self.change_font_size)
        settings_menu.add_command(label="Toggle 12/24 Hour", command=self.toggle_format)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        self.root.config(menu=menubar)

    def change_bg_color(self):
        color = colorchooser.askcolor(title="Choose background color", color=self.bg_color)[1]
        if color:
            self.bg_color = color
            self.root.configure(bg=self.bg_color)
            self.label.configure(bg=self.bg_color)

    def change_font_size(self):
        size = simpledialog.askinteger("Font Size", "Enter font size", initialvalue=self.font_size)
        if size:
            self.font_size = size
            self.label.configure(font=('Helvetica', self.font_size))

    def toggle_format(self):
        self.time_format = '12' if self.time_format == '24' else '24'

    def get_time_str(self):
        now = datetime.now()
        if self.time_format == '12':
            return now.strftime('%I:%M:%S %p')
        return now.strftime('%H:%M:%S')

    def update_clock(self):
        self.label.configure(text=self.get_time_str())
        self.root.after(1000, self.update_clock)

    def run(self):
        self.root.mainloop()


def main():
    args = parse_args()
    clock = WindowClock(bg_color=args.bg_color,
                        font_size=args.font_size,
                        time_format=args.format)
    clock.run()


if __name__ == '__main__':
    main()
