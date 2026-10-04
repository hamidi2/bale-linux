#!/usr/bin/env python3
# تولید آیکون‌های شمارنده (badge-0..99.png) از روی لوگوی بله
from PIL import Image, ImageDraw, ImageFont
import os, sys

base_path = sys.argv[1] if len(sys.argv) > 1 else 'bale.png'
out = sys.argv[2] if len(sys.argv) > 2 else 'badges'
os.makedirs(out, exist_ok=True)
base = Image.open(base_path).convert('RGBA').resize((32, 32), Image.LANCZOS)
base.save(f'{out}/badge-0.png')
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
except Exception:
    font = ImageFont.load_default()
for n in range(1, 100):
    img = base.copy()
    d = ImageDraw.Draw(img)
    d.ellipse([14, 14, 32, 32], fill=(228, 30, 30, 255), outline=(255, 255, 255, 255), width=1)
    txt = str(n)
    bbox = d.textbbox((0, 0), txt, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((23 - w / 2 - bbox[0], 23 - h / 2 - bbox[1]), txt, font=font, fill=(255, 255, 255, 255))
    img.save(f'{out}/badge-{n}.png')
print(f'badges → {out}/badge-0..99.png')
