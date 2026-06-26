import asyncio
import os

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from auro import config
from auro.helpers import Track


class Thumbnail:
    WIDTH = 1280
    HEIGHT = 720

    def __init__(self):
        try:
            self.title_font = ImageFont.truetype("auro/helpers/Raleway-Bold.ttf", 48)
            self.small_font = ImageFont.truetype("auro/helpers/Inter-Light.ttf", 28)
            self.time_font = ImageFont.truetype("auro/helpers/Raleway-Bold.ttf", 24)
        except Exception:
            self.title_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
            self.time_font = ImageFont.load_default()

        self.session = None

    async def start(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    async def download_thumb(self, url: str, path: str):
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            with open(path, "wb") as f:
                f.write(await resp.read())

    def create_image(self, thumb_path, output, song):
        # Background
        bg = Image.open(thumb_path).convert("RGB").resize((self.WIDTH, self.HEIGHT))

        bg = bg.filter(ImageFilter.GaussianBlur(40))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)

        draw = ImageDraw.Draw(bg)

        # Album Art
        cover = Image.open(thumb_path).convert("RGB").resize((380, 380))

        x = 90
        y = 170

        # Shadow
        shadow = Image.new("RGBA", (390, 390), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle(
            (8, 8, 388, 388),
            radius=25,
            fill=(0, 0, 0, 120),
        )

        bg.paste(shadow, (x, y), shadow)

        # Rounded Cover
        mask = Image.new("L", (380, 380), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, 380, 380),
            radius=25,
            fill=255,
        )

        cover.putalpha(mask)
        bg.paste(cover, (x, y), cover)

        # Text
        title = (song.title or "Unknown")[:35]
        channel = (song.channel_name or "Unknown")[:30]
        views = song.view_count or "0"

        tx = 550
        ty = 230

        draw.text(
            (tx, ty),
            title,
            fill="white",
            font=self.title_font,
        )

        draw.text(
            (tx, ty + 75),
            channel,
            fill=(220, 220, 220),
            font=self.small_font,
        )

        draw.text(
            (tx, ty + 130),
            f"{views} views",
            fill=(180, 180, 180),
            font=self.small_font,
        )

        # Progress Bar
        line_y = 620

        draw.text(
            (40, line_y - 30),
            "0:01",
            fill="white",
            font=self.time_font,
        )

        draw.text(
            (1180, line_y - 30),
            f"-{song.duration or '0:00'}",
            fill="white",
            font=self.time_font,
        )

        draw.line(
            [(50, line_y + 20), (1230, line_y + 20)],
            fill=(220, 220, 220),
            width=5,
        )

        draw.ellipse(
            (40, line_y + 10, 60, line_y + 30),
            fill="white",
        )

        bg.save(output, quality=95)
        return output

    async def generate(self, song: Track):
        try:
            if not self.session:
                await self.start()

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"

            if os.path.exists(output):
                return output

            await self.download_thumb(song.thumbnail, temp)

            await asyncio.to_thread(
                self.create_image,
                temp,
                output,
                song,
            )

            if os.path.exists(temp):
                os.remove(temp)

            return output

        except Exception:
            return config.DEFAULT_THUMB
