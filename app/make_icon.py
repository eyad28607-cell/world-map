"""Draws the app icon (a globe with an orange marker) and saves icon.ico and icon.png."""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024  # draw large, then downscale for smooth edges
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# rounded-square background
d.rounded_rectangle((32, 32, S - 32, S - 32), radius=220, fill=(11, 46, 107, 255))

# globe
cx, cy, r = S // 2, S // 2 + 20, 340
d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(42, 111, 219, 255))
line = (232, 240, 251, 255)
w = 22
d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=line, width=w)
for k in (0.45, 0.85):  # meridians
    d.ellipse((cx - r * k, cy - r, cx + r * k, cy + r), outline=line, width=w)
d.line((cx, cy - r, cx, cy + r), fill=line, width=w)
for f in (-0.5, 0, 0.5):  # parallels
    y = cy + r * f
    half = (r * r - (r * f) ** 2) ** 0.5
    d.line((cx - half, y, cx + half, y), fill=line, width=w)

# map pin
px, py, pr = cx + 190, cy - 230, 120
d.polygon([(px - pr * 0.82, py + pr * 0.55), (px + pr * 0.82, py + pr * 0.55), (px, py + pr * 1.9)], fill=(240, 138, 75, 255))
d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(240, 138, 75, 255))
d.ellipse((px - pr * 0.42, py - pr * 0.42, px + pr * 0.42, py + pr * 0.42), fill=(11, 46, 107, 255))

img.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, "icon.png"))
img.save(os.path.join(HERE, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("ok")
