import tkinter as tk
import math


class JarvisGUI:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.configure(bg="#000000")

        # Get screen dimensions
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        # 50% of screen, centered
        self.sw = screen_w // 2
        self.sh = screen_h // 2
        x = (screen_w - self.sw) // 2
        y = (screen_h - self.sh) // 2

        self.root.geometry(f"{self.sw}x{self.sh}+{x}+{y}")
        self.root.resizable(False, False)

        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.canvas = tk.Canvas(
            self.root,
            width=self.sw,
            height=self.sh,
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.cx = self.sw // 2
        self.cy = self.sh // 2 - 40
        self.base_radius = min(self.sw, self.sh) // 4

        self.angle = 0
        self.arc_offset = 0
        self.inner_angle = 0
        self.state_colors = {
            "idle":       "#00d4ff",
            "listening":  "#00ff99",
            "speaking":   "#ff6633",
            "processing": "#ffaa00",
            "active":     "#ff4488",
            "shutdown":   "#ff2222",
        }
        self.current_color = self.state_colors["idle"]

        self._draw_static()
        self._draw_dynamic()
        self._animate()
        
    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _draw_static(self):
        cx, cy = self.cx, self.cy
        r = self.base_radius

        # Corner brackets
        pad = 20
        length = 40
        corners = [
            (pad, pad, pad + length, pad, pad, pad + length),
            (self.sw - pad, pad, self.sw - pad - length, pad, self.sw - pad, pad + length),
            (pad, self.sh - pad, pad + length, self.sh - pad, pad, self.sh - pad - length),
            (self.sw - pad, self.sh - pad, self.sw - pad - length, self.sh - pad, self.sw - pad, self.sh - pad - length),
        ]
        for x1, y1, x2, y2, x3, y3 in corners:
            self.canvas.create_line(x1, y1, x2, y2, fill="#00d4ff", width=2)
            self.canvas.create_line(x1, y1, x3, y3, fill="#00d4ff", width=2)

        # Header
        self.canvas.create_text(
            cx, 22,
            text="J.A.R.V.I.S",
            fill="#00d4ff",
            font=("Courier", 13, "bold"),
            anchor="center"
        )

        # Outer faint ring
        self.canvas.create_oval(
            cx - r - 20, cy - r - 20,
            cx + r + 20, cy + r + 20,
            outline="#00d4ff", width=1,
            dash=(3, 8), fill=""
        )

        # Footer status bar
        self.canvas.create_text(
            cx - 180, self.sh - 20,
            text="SYS: ONLINE",
            fill="#00d4ff",
            font=("Courier", 10),
            anchor="center"
        )
        self.canvas.create_text(
            cx, self.sh - 20,
            text="AI: READY",
            fill="#00d4ff",
            font=("Courier", 10),
            anchor="center"
        )
        self.canvas.create_text(
            cx + 180, self.sh - 20,
            text="MIC: STANDBY",
            fill="#00d4ff",
            font=("Courier", 10),
            anchor="center"
        )

    def _draw_dynamic(self):
        cx, cy = self.cx, self.cy
        r = self.base_radius
        color = self.current_color

        self.canvas.delete("dynamic")

        # Crosshairs
        self.canvas.create_line(cx - r - 30, cy, cx + r + 30, cy,
                                 fill=color, width=1, dash=(4, 6), tags="dynamic")
        self.canvas.create_line(cx, cy - r - 30, cx, cy + r + 30,
                                 fill=color, width=1, dash=(4, 6), tags="dynamic")

        # Breathing main circle (radius pulses with sine)
        br = r + int(12 * math.sin(self.angle * 0.8))
        self._draw_glow_oval(cx, cy, br, color, width=3, tag="dynamic")

        # Inner ring
        self._draw_glow_oval(cx, cy, br - 25, color, width=1, opacity_factor=0.4, tag="dynamic")

        # Rotating dashed arc (outer)
        self._draw_rotating_arc(cx, cy, br + 20, self.arc_offset, color, dash=(30, 15), width=2, tag="dynamic")

        # Rotating dashed arc (inner, opposite direction)
        self._draw_rotating_arc(cx, cy, br - 45, -self.inner_angle, color, dash=(15, 20), width=1, tag="dynamic")

        # Center dot
        dot_r = 6
        self.canvas.create_oval(
            cx - dot_r, cy - dot_r,
            cx + dot_r, cy + dot_r,
            fill=color, outline="", tags="dynamic"
        )

    def _draw_glow_oval(self, cx, cy, r, color, width=2, opacity_factor=1.0, tag="dynamic"):
        # Simulate glow with multiple rings of decreasing width
        layers = [(r + 6, "#001a22", 8), (r + 3, "#002a33", 5), (r, color, width)]
        for radius, clr, w in layers:
            self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                outline=clr, width=w, fill="", tags=tag
            )

    def _draw_rotating_arc(self, cx, cy, r, offset_deg, color, dash=(20, 15), width=2, tag="dynamic"):
        start = offset_deg % 360
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start, extent=120,
            style="arc", outline=color, width=width, tags=tag
        )
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start + 150, extent=80,
            style="arc", outline=color, width=width, tags=tag
        )
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start + 260, extent=50,
            style="arc", outline=color, width=max(1, width - 1), tags=tag
        )

    def _animate(self):
        self.angle += 0.06
        self.arc_offset += 2.5
        self.inner_angle += 1.8
        self._draw_dynamic()
        self.root.after(33, self._animate)  # ~30 fps

    def update_status(self, text, state="idle"):
        def update():
            self.current_color = self.state_colors.get(state, "#00d4ff")
            self.canvas.delete("status")
            self.canvas.create_text(
                self.cx,
                self.cy + self.base_radius + 60,
                text=text.upper(),
                fill=self.current_color,
                font=("Courier", 24, "bold"),
                anchor="center",
                tags="status"
            )
        self.root.after(0, update)

    def run(self):
        # Draw initial status
        self.update_status("IDLE", "idle")
        self.root.mainloop()
