import argparse
import tkinter as tk
from tkinter import colorchooser, ttk, font, messagebox
from datetime import datetime

from monitor_utils import enumerate_monitors



def parse_args():
    parser = argparse.ArgumentParser(description="Simple window clock")
    parser.add_argument('--bg-color', default='black', help='Background color of the clock window')
    parser.add_argument('--font-color', default='white', help='Color of the clock text')
    parser.add_argument('--font-size', type=int, default=48, help='Font size of the clock')
    parser.add_argument('--format', choices=['12', '24'], default='24', help='Time format (12 or 24 hour)')
    return parser.parse_args()


class WindowClock:
    def __init__(self, bg_color='black', font_color='white', font_size=48, time_format='24'):
        self.bg_color = bg_color
        self.font_color = font_color
        self.font_size = font_size
        self.time_format = time_format

        self.font_family = 'Helvetica'
        self.selected_monitor_index = 0
        self.dragging = False
        self.scaling = False
        self.scale_handle = None
        self.center_line_h = None
        self.center_line_v = None

        # Main window will hold settings
        self.settings_root = tk.Tk()
        self.settings_root.title("Clock Settings")

        # Populate settings UI
        self.monitors = enumerate_monitors(self.settings_root)
        if len(self.monitors) == 1:
            messagebox.showwarning("Monitor Detection", "Multiple displays were not detected.\nInstall the 'screeninfo' package for improved detection.")
        self.create_settings_ui()

        # Separate borderless window for the clock display
        self.clock_window = tk.Toplevel(self.settings_root)
        self.clock_window.overrideredirect(True)
        self.clock_window.configure(bg=self.bg_color)

        # Use a canvas so the text can be moved around
        self.canvas = tk.Canvas(self.clock_window, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")
        self.text_item = self.canvas.create_text(100, 100, text='', fill=self.font_color,
                                                 font=(self.font_family, self.font_size))
        self.selection_rect = None

        # Bind events for dragging and scaling
        self.canvas.bind('<Button-1>', self.on_text_press)
        self.canvas.bind('<B1-Motion>', self.on_text_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_text_release)
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.canvas.bind('<Button-4>', self.on_mousewheel)  # Linux scroll up
        self.canvas.bind('<Button-5>', self.on_mousewheel)  # Linux scroll down

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

        # Font color button
        tk.Button(self.settings_root, text="Font Color", command=self.change_font_color).grid(row=3, column=0, columnspan=2, pady=2)

        # Format toggle button
        tk.Button(self.settings_root, text="Toggle 12/24 Hour", command=self.toggle_format).grid(row=4, column=0, columnspan=2, pady=2)

        # Apply settings
        tk.Button(self.settings_root, text="Apply", command=self.apply_settings).grid(row=5, column=0, pady=5)
        tk.Button(self.settings_root, text="Quit", command=self.settings_root.quit).grid(row=5, column=1, pady=5)

    def change_font_color(self):
        color = colorchooser.askcolor(title="Choose font color", color=self.font_color)[1]
        if color:
            self.font_color = color
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
        x_sign = '+' if monitor.x >= 0 else ''
        y_sign = '+' if monitor.y >= 0 else ''
        geometry = f"{monitor.width}x{monitor.height}{x_sign}{monitor.x}{y_sign}{monitor.y}"
        self.clock_window.geometry(geometry)
        self.canvas.configure(bg=self.bg_color)
        self.canvas.itemconfigure(self.text_item, font=(self.font_family, self.font_size), fill=self.font_color)
        if self.selection_rect:
            bbox = self.canvas.bbox(self.text_item)
            self.canvas.coords(self.selection_rect, bbox)
            if self.scale_handle:
                self.canvas.coords(self.scale_handle, bbox[2], bbox[3], bbox[2] + 8, bbox[3] + 8)

    def on_text_press(self, event):
        if self.scale_handle:
            hx1, hy1, hx2, hy2 = self.canvas.coords(self.scale_handle)
            if hx1 <= event.x <= hx2 and hy1 <= event.y <= hy2:
                self.scaling = True
                self.scale_start_y = event.y
                self.initial_font_size = self.font_size
                return

        bbox = self.canvas.bbox(self.text_item)
        if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
            self.dragging = True
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            self.drag_offset_x = event.x - cx
            self.drag_offset_y = event.y - cy
            if self.selection_rect:
                self.canvas.coords(self.selection_rect, bbox)
            else:
                self.selection_rect = self.canvas.create_rectangle(bbox, outline='red', dash=(2, 2))
            if self.scale_handle:
                self.canvas.coords(self.scale_handle, bbox[2], bbox[3], bbox[2] + 8, bbox[3] + 8)
            else:
                self.scale_handle = self.canvas.create_oval(bbox[2], bbox[3], bbox[2] + 8, bbox[3] + 8, fill='red', outline='')
        else:
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None
            if self.scale_handle:
                self.canvas.delete(self.scale_handle)
                self.scale_handle = None

    def on_text_drag(self, event):
        if self.scaling:
            delta = event.y - self.scale_start_y
            new_size = max(1, self.initial_font_size + delta)
            if new_size != self.font_size:
                self.font_size = new_size
                self.font_size_var.set(self.font_size)
                self.canvas.itemconfigure(self.text_item, font=(self.font_family, self.font_size))
                bbox = self.canvas.bbox(self.text_item)
                if self.selection_rect:
                    self.canvas.coords(self.selection_rect, bbox)
                if self.scale_handle:
                    self.canvas.coords(self.scale_handle, bbox[2], bbox[3], bbox[2] + 8, bbox[3] + 8)
            return

        if self.dragging:
            x = event.x - self.drag_offset_x
            y = event.y - self.drag_offset_y
            cx = self.canvas.winfo_width() / 2
            cy = self.canvas.winfo_height() / 2
            snapped = False
            if abs(x - cx) <= 10:
                x = cx
                snapped = True
            if abs(y - cy) <= 10:
                y = cy
                snapped = True

            self.canvas.coords(self.text_item, x, y)
            bbox = self.canvas.bbox(self.text_item)
            if self.selection_rect:
                self.canvas.coords(self.selection_rect, bbox)
            if self.scale_handle:
                self.canvas.coords(self.scale_handle, bbox[2], bbox[3], bbox[2] + 8, bbox[3] + 8)

            if snapped:
                if not self.center_line_v:
                    self.center_line_v = self.canvas.create_line(cx, 0, cx, self.canvas.winfo_height(), fill='red', dash=(2, 2))
                if not self.center_line_h:
                    self.center_line_h = self.canvas.create_line(0, cy, self.canvas.winfo_width(), cy, fill='red', dash=(2, 2))
            else:
                if self.center_line_v:
                    self.canvas.delete(self.center_line_v)
                    self.center_line_v = None
                if self.center_line_h:
                    self.canvas.delete(self.center_line_h)
                    self.center_line_h = None

    def on_text_release(self, _event):
        self.dragging = False
        self.scaling = False
        if self.center_line_v:
            self.canvas.delete(self.center_line_v)
            self.center_line_v = None
        if self.center_line_h:
            self.canvas.delete(self.center_line_h)
            self.center_line_h = None

    def on_mousewheel(self, event):
        if self.selection_rect:
            delta = 1 if getattr(event, 'delta', 0) > 0 or getattr(event, 'num', None) == 4 else -1
            self.font_size = max(1, self.font_size + delta)
            self.font_size_var.set(self.font_size)
            self.canvas.itemconfigure(self.text_item, font=(self.font_family, self.font_size))
            bbox = self.canvas.bbox(self.text_item)
            self.canvas.coords(self.selection_rect, bbox)
            if self.scale_handle:
                self.canvas.coords(self.scale_handle, bbox[2], bbox[3], bbox[2] + 8, bbox[3] + 8)

    def get_time_str(self):
        now = datetime.now()
        if self.time_format == '12':
            return now.strftime('%I:%M:%S %p')
        return now.strftime('%H:%M:%S')

    def update_clock(self):
        self.canvas.itemconfigure(self.text_item, text=self.get_time_str())
        self.clock_window.after(1000, self.update_clock)

    def run(self):
        self.settings_root.mainloop()


def main():
    args = parse_args()
    clock = WindowClock(bg_color=args.bg_color,
                        font_color=args.font_color,
                        font_size=args.font_size,
                        time_format=args.format)
    clock.run()


if __name__ == '__main__':
    main()
