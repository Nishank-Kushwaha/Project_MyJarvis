import tkinter as tk
from PIL import ImageGrab

selected_region = None

def take_snip():
    global selected_region

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)        # semi-transparent overlay
    root.configure(bg="black")
    root.attributes("-topmost", True)

    canvas = tk.Canvas(root, cursor="cross", bg="black")
    canvas.pack(fill="both", expand=True)

    start_x = start_y = 0
    rect = None

    def on_press(event):
        nonlocal start_x, start_y, rect
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(
            start_x, start_y, start_x, start_y,
            outline="#00d4ff", width=2, fill="#00d4ff"
        )

    def on_drag(event):
        canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_release(event):
        global selected_region
        end_x, end_y = event.x, event.y

        # Normalize coordinates (in case user dragged backwards)
        x1, y1 = min(start_x, end_x), min(start_y, end_y)
        x2, y2 = max(start_x, end_x), max(start_y, end_y)

        root.destroy()

        if x2 - x1 > 5 and y2 - y1 > 5:   # ignore tiny accidental clicks
            selected_region = (x1, y1, x2, y2)
        else:
            selected_region = None

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", lambda e: root.destroy())  # cancel with Escape

    root.mainloop()
    return selected_region