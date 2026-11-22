
import os
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v27.0")
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)

POSTS = [
    {
        "category": "MINDSET",
        "headline": "Small steps.\nBig changes.",
        "caption": "You don't need a perfect plan. Start with one small step today. 🌱\n\n#Motivation #Mindset #DailyInspiration",
        "colors": ((15, 32, 65), (48, 115, 125)),
    },
    {
        "category": "LIFE REMINDER",
        "headline": "Protect your\npeace.",
        "caption": "Not everything deserves your energy. Choose what helps you grow. ✨\n\n#LifeReminder #PositiveVibes #SelfGrowth",
        "colors": ((62, 37, 88), (157, 91, 119)),
    },
    {
        "category": "NATURE",
        "headline": "Take a breath.\nFind your calm.",
        "caption": "A little pause can make room for a clearer mind. Take a moment for yourself today. 🍃\n\n#Nature #Calm #Wellbeing",
        "colors": ((14, 77, 73), (89, 145, 105)),
    },
    {
        "category": "PRODUCTIVITY",
        "headline": "Focus on\nwhat matters.",
        "caption": "One meaningful task at a time. Progress is built through consistency. 🎯\n\n#Productivity #Focus #BetterHabits",
        "colors": ((93, 49, 25), (191, 120, 57)),
    },
    {
        "category": "GOOD VIBES",
        "headline": "Make today\ncount.",
        "caption": "A fresh day is another chance to do something good. Send this to someone who needs a little encouragement. ☀️\n\n#GoodVibes #Inspiration #DailyPost",
        "colors": ((38, 54, 105), (119, 94, 163)),
    },
]


def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)

    return ImageFont.load_default()


def make_gradient(size, c1, c2):
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()

    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(
            int(c1[i] * (1 - t) + c2[i] * t)
            for i in range(3)
        )

        for x in range(width):
            pixels[x, y] = color

    return image


def render_post(post, slot, date_key):
    width, height = 1080, 1350
    image = make_gradient((width, height), *post["colors"])
    draw = ImageDraw.Draw(image, "RGBA")

    draw.ellipse((720, -170, 1240, 350),
                 fill=(255, 255, 255, 24))
    draw.ellipse((-210, 930, 390, 1530),
                 fill=(255, 255, 255, 18))

    draw.rounded_rectangle(
        (72, 78, 1008, 1272),
        radius=42,
        outline=(255, 255, 255, 90),
        width=3,
    )

    label_font = get_font(30, bold=True)
    headline_font = get_font(82, bold=True)
    footer_font = get_font(25)

    draw.rounded_rectangle(
        (112, 145, 420, 212),
        radius=28,
        fill=(255, 255, 255, 38),
    )

    draw.text(
        (142, 160),
        post["category"],
        font=label_font,
        fill=(255, 255, 255, 255),
    )

    lines = post["headline"].split("\n")
    y = 470 if len(lines) == 2 else 520

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        x = (width - (bbox[2] - bbox[0])) // 2

        draw.text(
            (x + 3, y + 5),
            line,
            font=headline_font,
            fill=(0, 0, 0, 70),
        )

        draw.text(
            (x, y),
            line,
            font=headline_font,
            fill=(255, 255, 255, 255),
        )

        y += 112

    draw.line(
        (350, 850, 730, 850),
        fill=(255, 255, 255, 170),
        width=4,
    )

    footer = "A LITTLE INSPIRATION FOR YOUR DAY"
    bbox = draw.textbbox((0, 0), footer, font=footer_font)

    draw.text(
        ((width - (bbox[2] - bbox[0])) // 2, 900),
        footer,
        font=footer_font,
        fill=(255, 255, 255, 235),
    )

    brand = os.getenv("BRAND_NAME", "DAILY INSPIRATION")
    brand_font = get_font(24, bold=True)
    bbox = draw.textbbox((0, 0), brand, font=brand_font)

    draw.text(
        ((width - (bbox[2] - bbox[0])) // 2, 1160),
        brand,
        font=brand_font,
        fill=(255, 255, 255, 220),
    )

    path = OUT_DIR / f"{date_key}-post-{slot}.jpg"
    image.save(path, "JPEG", quality=92, optimize=True)

    return path


def publish_facebook(image_path, caption):
    page_id = os.environ["FB_PAGE_ID"]
    token = os.environ["FB_PAGE_ACCESS_TOKEN"]

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_VERSION}/{page_id}/photos"
    )

    with image_path.open("rb") as image_file:
        response = requests.post(
            url,
            data={
                "caption": caption,
                "access_token": token,
            },
            files={
                "source": (
                    image_path.name,
                    image_file,
                    "image/jpeg",
                )
            },
            timeout=90,
        )

    if not response.ok:
        raise RuntimeError(
            f"Facebook publish failed "
            f"({response.status_code}): {response.text[:1000]}"
        )

    return response.json()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--slot",
        type=int,
        choices=range(1, 6),
        default=None,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    date_key = now.strftime("%Y%m%d")

    slot = args.slot or int(os.getenv("POST_SLOT", "1"))

    if slot < 1 or slot > 5:
        raise SystemExit("POST_SLOT must be between 1 and 5.")

    post = POSTS[slot - 1]

    image_path = render_post(post, slot, date_key)

    print(f"Generated image: {image_path}")
    print(f"Selected slot: {slot}")
    print(f"Caption: {post['caption']}")

    if args.dry_run:
        print("DRY RUN: no Facebook post was published.")
        return

    required = [
        "FB_PAGE_ID",
        "FB_PAGE_ACCESS_TOKEN",
    ]

    missing = [
        name for name in required
        if not os.getenv(name)
    ]

    if missing:
        raise SystemExit(
            "Missing GitHub Actions secrets: "
            + ", ".join(missing)
        )

    result = publish_facebook(
        image_path,
        post["caption"],
    )

    print("FACEBOOK PUBLISHED SUCCESSFULLY")
    print(json.dumps(result)[:800])


if __name__ == "__main__":
    main()
