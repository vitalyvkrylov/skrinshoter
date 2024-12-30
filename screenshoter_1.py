from tkinter import *
from PIL import ImageGrab
import datetime, os


class SnippingTool:
    def __init__(self, master):
        self.master = master
        master.attributes('-topmost', True)
        master.attributes('-alpha', 0.8)
        master.geometry(f"{master.winfo_screenwidth()}x{master.winfo_screenheight()}")
        master.overrideredirect(True)

        self.start_x, self.start_y, self.end_x, self.end_y = None, None, None, None
        self.snipping = False
        self.canvas = Canvas(master, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=YES)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.imageDir = "./images"
        self.imageType = '.png'

        if not os.path.exists(self.imageDir):
            os.makedirs(self.imageDir)

        master.bind("<Escape>", self.on_key_press)

        # Resize handles
        self.handles = {}
        self.selected_handle = None
        self.handle_size = 8

        # Control panel
        self.panel = None

    def on_mouse_down(self, event):
        handle = self.get_handle_at(event.x, event.y)
        if handle:
            self.selected_handle = handle
        else:
            self.snipping = True
            self.start_x, self.start_y = event.x, event.y
            self.end_x, self.end_y = event.x, event.y

    def on_mouse_move(self, event):
        if self.snipping:
            self.end_x, self.end_y = event.x, event.y
            self.draw_border()
        elif self.selected_handle:
            self.resize_selection(event.x, event.y)
            self.draw_border()

    def on_mouse_up(self, event):
        if self.snipping:
            self.snipping = False
            self.add_handles()
            self.add_control_panel()
        self.selected_handle = None

    def draw_border(self):
        self.canvas.delete("border")
        if self.start_x is not None and self.end_x is not None:
            self.canvas.create_rectangle(
                self.start_x, self.start_y, self.end_x, self.end_y,
                outline="white", width=2, tags="border", fill=""
            )
        self.add_handles()
        self.update_control_panel()

    def add_handles(self):
        self.canvas.delete("handle")
        self.handles.clear()

        x1, y1, x2, y2 = self.start_x, self.start_y, self.end_x, self.end_y
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        positions = {
            "tl": (x1, y1),  # Top-left
            "tr": (x2, y1),  # Top-right
            "bl": (x1, y2),  # Bottom-left
            "br": (x2, y2),  # Bottom-right
            "ml": ((x1 + x2) // 2, y1),  # Middle-top
            "mr": ((x1 + x2) // 2, y2),  # Middle-bottom
            "tm": (x1, (y1 + y2) // 2),  # Middle-left
            "bm": (x2, (y1 + y2) // 2),  # Middle-right
        }

        for handle, (x, y) in positions.items():
            rect = self.canvas.create_rectangle(
                x - self.handle_size, y - self.handle_size,
                x + self.handle_size, y + self.handle_size,
                fill="white", tags="handle"
            )
            self.handles[handle] = (rect, x, y)

    def resize_selection(self, x, y):
        handle, _, _ = self.handles[self.selected_handle]

        if self.selected_handle == "tl":
            self.start_x, self.start_y = x, y
        elif self.selected_handle == "tr":
            self.end_x, self.start_y = x, y
        elif self.selected_handle == "bl":
            self.start_x, self.end_y = x, y
        elif self.selected_handle == "br":
            self.end_x, self.end_y = x, y
        elif self.selected_handle == "ml":
            self.start_y = y
        elif self.selected_handle == "mr":
            self.end_y = y
        elif self.selected_handle == "tm":
            self.start_x = x
        elif self.selected_handle == "bm":
            self.end_x = x

    def get_handle_at(self, x, y):
        for handle, (_, hx, hy) in self.handles.items():
            if abs(x - hx) <= self.handle_size and abs(y - hy) <= self.handle_size:
                return handle
        return None

    def add_control_panel(self):
        if self.panel:
            self.canvas.delete("panel")
            self.panel = None

        self.panel = Frame(self.canvas, bg="gray")
        save_btn = Button(self.panel, text="Сохранить", command=self.capture_snip)
        copy_btn = Button(self.panel, text="Копировать", command=self.copy_to_clipboard)
        cancel_btn = Button(self.panel, text="Отменить", command=self.cancel_snip)

        save_btn.pack(side=LEFT, padx=5, pady=5)
        copy_btn.pack(side=LEFT, padx=5, pady=5)
        cancel_btn.pack(side=LEFT, padx=5, pady=5)

        self.panel_window = self.canvas.create_window(
            0, 0, window=self.panel, anchor="se", tags="panel"
        )
        self.update_control_panel()

    def update_control_panel(self):
        if self.panel:
            x1, y1, x2, y2 = self.start_x, self.start_y, self.end_x, self.end_y
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            # Расположить панель справа снизу выделенной области
            self.canvas.coords(self.panel_window, x2, y2)

    def capture_snip(self):
        self.master.withdraw()
        x1, x2 = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
        y1, y2 = min(self.start_y, self.end_y), max(self.start_y, self.end_y)
        root_x, root_y = self.master.winfo_rootx(), self.master.winfo_rooty()
        x1 += root_x
        x2 += root_x
        y1 += root_y
        y2 += root_y

        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + self.imageType
        screenshot.save(os.path.join(self.imageDir, filename))
        print(f"Screenshot saved as {os.path.join(self.imageDir, filename)}")
        self.master.destroy()

    def copy_to_clipboard(self):
        x1, x2 = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
        y1, y2 = min(self.start_y, self.end_y), max(self.start_y, self.end_y)
        root_x, root_y = self.master.winfo_rootx(), self.master.winfo_rooty()
        x1 += root_x
        x2 += root_x
        y1 += root_y
        y2 += root_y

        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        self.master.clipboard_clear()
        self.master.clipboard_append(screenshot.tobytes())
        print("Screenshot copied to clipboard")

    def cancel_snip(self):
        print("Snipping cancelled")
        self.master.destroy()

    def on_key_press(self, event):
        if event.keysym == 'Escape':
            self.master.destroy()


def main():
    root = Tk()
    app = SnippingTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
