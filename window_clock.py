import argparse
import tkinter as tk
from tkinter import colorchooser, ttk, font
from datetime import datetime


def enumerate_monitors(root):
    """Best effort attempt to list monitors."""
    monitors = []
    try:
        from screeninfo import get_monitors
        monitors = get_monitors()
    except Exception:
        pass

    if not monitors:
        # Fallback to single monitor using Tk info
        class _Monitor:
            def __init__(self, width, height, x=0, y=0, name="Default"):
                self.width = width
                self.height = height
                self.x = x
                self.y = y
                self.name = name

        monitors = [_Monitor(root.winfo_screenwidth(), root.winfo_screenheight())]

    return monitors


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

        self.font_family = 'Helvetica'
        self.selected_monitor_index = 0

        # Main window will hold settings
        self.settings_root = tk.Tk()
        self.settings_root.title("Clock Settings")

        # Populate settings UI
        self.monitors = enumerate_monitors(self.settings_root)
        self.create_settings_ui()

        # Separate borderless window for the clock display
        self.clock_window = tk.Toplevel(self.settings_root)
        self.clock_window.overrideredirect(True)
        self.clock_window.configure(bg=self.bg_color)

        self.label = tk.Label(self.clock_window, fg='white', bg=self.bg_color,
                              font=(self.font_family, self.font_size))
        self.label.pack(expand=True, fill="both")

        self.apply_settings()
        self.update_clock()

    def create_settings_ui(self):
        fonts = list(font.families())
        self.font_var = tk.StringVar(value=self.font_family)
        self.font_size_var = tk.IntVar(value=self.font_size)
        self.monitor_names = [getattr(m, 'name', f"{i}") for i, m in enumerate(self.monitors)]
        self.monitor_var = tk.StringVar(value=self.monitor_names[self.selected_monitor_index])

        # Monitor selection
        tk.Label(self.settings_root, text="Monitor:").grid(row=0, column=0, sticky="e")
        ttk.Combobox(self.settings_root, textvariable=self.monitor_var, values=self.monitor_names, state="readonly").grid(row=0, column=1, pady=2)

        # Font family selection
        tk.Label(self.settings_root, text="Font:").grid(row=1, column=0, sticky="e")
        ttk.Combobox(self.settings_root, textvariable=self.font_var, values=fonts, state="readonly").grid(row=1, column=1, pady=2)

        # Font size spinbox
        tk.Label(self.settings_root, text="Font Size:").grid(row=2, column=0, sticky="e")
        tk.Spinbox(self.settings_root, from_=10, to=400, textvariable=self.font_size_var).grid(row=2, column=1, pady=2)

        # Background color button
        tk.Button(self.settings_root, text="Background Color", command=self.change_bg_color).grid(row=3, column=0, columnspan=2, pady=2)

        # Format toggle button
        tk.Button(self.settings_root, text="Toggle 12/24 Hour", command=self.toggle_format).grid(row=4, column=0, columnspan=2, pady=2)

        # Apply settings
        tk.Button(self.settings_root, text="Apply", command=self.apply_settings).grid(row=5, column=0, pady=5)
        tk.Button(self.settings_root, text="Quit", command=self.settings_root.quit).grid(row=5, column=1, pady=5)

    def change_bg_color(self):
        color = colorchooser.askcolor(title="Choose background color", color=self.bg_color)[1]
        if color:
            self.bg_color = color
            self.apply_settings()

    def toggle_format(self):
        self.time_format = '12' if self.time_format == '24' else '24'
        self.update_clock()

    def apply_settings(self):
        self.font_family = self.font_var.get()
        self.font_size = self.font_size_var.get()
        if self.monitor_var.get() in self.monitor_names:
            self.selected_monitor_index = self.monitor_names.index(self.monitor_var.get())

        monitor = self.monitors[self.selected_monitor_index]
        geometry = f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}"
        self.clock_window.geometry(geometry)
        self.label.configure(font=(self.font_family, self.font_size), bg=self.bg_color)
        self.clock_window.configure(bg=self.bg_color)

    def get_time_str(self):
        now = datetime.now()
        if self.time_format == '12':
            return now.strftime('%I:%M:%S %p')
        return now.strftime('%H:%M:%S')

    def update_clock(self):
        self.label.configure(text=self.get_time_str())
        self.clock_window.after(1000, self.update_clock)

    def run(self):
        self.settings_root.mainloop()


def main():
    args = parse_args()
    clock = WindowClock(bg_color=args.bg_color,
                        font_size=args.font_size,
                        time_format=args.format)
    clock.run()


if __name__ == '__main__':
    main()
