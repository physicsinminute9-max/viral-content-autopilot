
import os
import json
import argparse
import random
import math
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v27.0")

OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)

FACTS = [
    {
        "category": "SPACE",
        "headline": "A day on Venus is longer than its year.",
        "detail": "Venus takes about 243 Earth days to rotate once, but only about 225 Earth days to orbit the Sun.",
        "source": "NASA",
        "url": "https://science.nasa.gov/venus/venus-facts/",
        "tags": "#Space #Venus #ScienceFacts",
        "colors": ((38, 35, 91), (130, 65, 117)),
    },
    {
        "category": "SPACE",
        "headline": "Jupiter has an incredibly short day.",
        "detail": "Jupiter completes one rotation in roughly 10 hours, making its day the shortest of all the planets in our solar system.",
        "source": "NASA",
        "url": "https://science.nasa.gov/jupiter/jupiter-facts/",
        "tags": "#Jupiter #SpaceFacts #Astronomy",
        "colors": ((32, 53, 105), (91, 128, 164)),
    },
    {
        "category": "SPACE",
        "headline": "Saturn could float in water.",
        "detail": "Saturn's average density is lower than the density of water. This is a comparison of average density, not a real floating experiment.",
        "source": "NASA",
        "url": "https://science.nasa.gov/saturn/saturn-facts/",
        "tags": "#Saturn #PlanetFacts #Space",
        "colors": ((91, 57, 31), (184, 128, 68)),
    },
    {
        "category": "SPACE",
        "headline": "The Moon is slowly moving away.",
        "detail": "The Moon moves away from Earth by about 3.8 centimetres each year.",
        "source": "NASA",
        "url": "https://science.nasa.gov/moon/",
        "tags": "#Moon #Earth #SpaceFacts",
        "colors": ((22, 55, 91), (75, 117, 145)),
    },
    {
        "category": "SPACE",
        "headline": "Uranus rotates on its side.",
        "detail": "Uranus has an extreme axial tilt of about 98 degrees, so it rotates almost on its side.",
        "source": "NASA",
        "url": "https://science.nasa.gov/uranus/uranus-facts/",
        "tags": "#Uranus #Astronomy #Science",
        "colors": ((16, 89, 102), (75, 157, 159)),
    },
    {
        "category": "SPACE",
        "headline": "Venus is hotter than Mercury.",
        "detail": "Even though Mercury is closer to the Sun, Venus is hotter because its thick atmosphere traps heat.",
        "source": "NASA",
        "url": "https://science.nasa.gov/venus/venus-facts/",
        "tags": "#Venus #Mercury #SpaceFacts",
        "colors": ((111, 48, 34), (195, 104, 57)),
    },
    {
        "category": "OCEAN",
        "headline": "Octopuses have three hearts.",
        "detail": "Two hearts pump blood to the gills, while a third pumps it to the rest of the body.",
        "source": "Smithsonian Ocean",
        "url": "https://ocean.si.edu/",
        "tags": "#Octopus #OceanFacts #Nature",
        "colors": ((14, 75, 81), (35, 137, 133)),
    },
    {
        "category": "ANIMALS",
        "headline": "Sharks are older than trees.",
        "detail": "Shark ancestors appeared in the fossil record hundreds of millions of years ago, before the first true trees.",
        "source": "Smithsonian Ocean",
        "url": "https://ocean.si.edu/",
        "tags": "#Sharks #AnimalFacts #Nature",
        "colors": ((22, 54, 83), (71, 117, 143)),
    },
    {
        "category": "NATURE",
        "headline": "A lightning bolt is extremely hot.",
        "detail": "The air in a lightning channel can reach temperatures around 30,000 kelvin, hotter than the surface of the Sun.",
        "source": "NOAA",
        "url": "https://www.noaa.gov/",
        "tags": "#Lightning #WeatherFacts #Science",
        "colors": ((47, 42, 89), (111, 91, 158)),
    },
    {
        "category": "HUMAN BODY",
        "headline": "Your skin is your largest organ.",
        "detail": "Human skin covers the body and helps protect it from the outside environment.",
        "source": "Cleveland Clinic",
        "url": "https://my.clevelandclinic.org/health/body/10978-skin",
        "tags": "#HumanBody #HealthFacts #Science",
        "colors": ((83, 48, 77), (164, 93, 111)),
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


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()

        bbox = draw.textbbox(
            (0, 0),
            test,
            font=font
        )

        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def make_caption(fact):
    return (
        f"Did you know? 🤯\n\n"
        f"{fact['headline']}\n\n"
        f"{fact['detail']}\n\n"
        f"Source: {fact['source']} — {fact['url']}\n\n"
        f"{fact['tags']} #DidYouKnow #InterestingFacts"
    )


def draw_stars(draw, cx, cy, radius, rng):
    for _ in range(30):
        x = rng.randint(cx-radius, cx+radius)
        y = rng.randint(cy-radius, cy+radius)
        size = rng.randint(3, 8)

        draw.ellipse(
            (x, y, x+size, y+size),
            fill=(255, 255, 255, 210)
        )


def draw_visual(draw, category, cx, cy, seed):
    rng = random.Random(seed)

    category = category.upper()

    if category == "SPACE":
        # Colorful 3D-inspired planet
        colors = [
            (255, 174, 76, 255),
            (112, 205, 255, 255),
            (202, 135, 255, 255),
            (255, 115, 125, 255),
        ]

        planet_color = rng.choice(colors)

        draw.ellipse(
            (cx-135, cy-135, cx+135, cy+135),
            fill=planet_color,
            outline=(255, 255, 255, 230),
            width=5
        )

        draw.ellipse(
            (cx-95, cy-100, cx+55, cy-5),
            fill=(255, 255, 255, 45)
        )

        # Planet rings
        draw.ellipse(
            (cx-205, cy-65, cx+205, cy+85),
            outline=(255, 255, 255, 210),
            width=13
        )

        draw.ellipse(
            (cx-190, cy-52, cx+190, cy+70),
            outline=(255, 255, 255, 80),
            width=4
        )

        draw_stars(draw, cx, cy, 220, rng)

    elif category == "OCEAN":
        # Cartoon octopus
        body_color = (255, 125, 120, 255)

        for i in range(8):
            start_x = cx - 80 + i * 23
            end_x = start_x + rng.randint(-35, 35)

            draw.line(
                (start_x, cy+30, end_x, cy+145),
                fill=body_color,
                width=21
            )

            draw.ellipse(
                (end_x-12, cy+132, end_x+12, cy+156),
                fill=body_color
            )

        draw.ellipse(
            (cx-95, cy-120, cx+95, cy+85),
            fill=body_color
        )

        # Eyes
        draw.ellipse(
            (cx-53, cy-45, cx-15, cy-5),
            fill="white"
        )

        draw.ellipse(
            (cx+15, cy-45, cx+53, cy-5),
            fill="white"
        )

        draw.ellipse(
            (cx-42, cy-35, cx-25, cy-15),
            fill=(20, 40, 65)
        )

        draw.ellipse(
            (cx+26, cy-35, cx+43, cy-15),
            fill=(20, 40, 65)
        )

        # Bubbles
        for _ in range(12):
            x = rng.randint(cx-190, cx+190)
            y = rng.randint(cy-180, cy+180)
            r = rng.randint(7, 17)

            draw.ellipse(
                (x-r, y-r, x+r, y+r),
                outline=(255, 255, 255, 180),
                width=4
            )

    elif category == "ANIMALS":
        # Cartoon shark
        shark_color = (170, 220, 240, 255)

        draw.ellipse(
            (cx-160, cy-75, cx+155, cy+85),
            fill=shark_color
        )

        draw.polygon(
            [
                (cx-20, cy-65),
                (cx+35, cy-155),
                (cx+80, cy-55)
            ],
            fill=shark_color
        )

        draw.polygon(
            [
                (cx+120, cy-5),
                (cx+205, cy-90),
                (cx+175, cy+35)
            ],
            fill=shark_color
        )

        draw.ellipse(
            (cx+70, cy-40, cx+91, cy-19),
            fill=(15, 35, 55)
        )

        draw.arc(
            (cx-10, cy+5, cx+110, cy+85),
            start=0,
            end=180,
            fill=(30, 60, 80),
            width=6
        )

        draw.polygon(
            [
                (cx-25, cy+72),
                (cx+10, cy+72),
                (cx+2, cy+110)
            ],
            fill=(255, 255, 255, 220)
        )

    elif category == "NATURE":
        # Lightning bolt
        draw.polygon(
            [
                (cx+30, cy-180),
                (cx-105, cy+5),
                (cx-25, cy+5),
                (cx-85, cy+175),
                (cx+120, cy-55),
                (cx+35, cy-55)
            ],
            fill=(255, 222, 65, 255),
            outline=(255, 255, 255, 255)
        )

        for angle in range(0, 360, 45):
            x1 = cx + int(math.cos(math.radians(angle)) * 150)
            y1 = cy + int(math.sin(math.radians(angle)) * 150)

            x2 = cx + int(math.cos(math.radians(angle)) * 190)
            y2 = cy + int(math.sin(math.radians(angle)) * 190)

            draw.line(
                (x1, y1, x2, y2),
                fill=(255, 255, 255, 190),
                width=7
            )

    elif category == "HUMAN BODY":
        # Colorful protective shield
        draw.polygon(
            [
                (cx, cy-175),
                (cx+145, cy-110),
                (cx+115, cy+65),
                (cx, cy+180),
                (cx-115, cy+65),
                (cx-145, cy-110)
            ],
            fill=(255, 185, 170, 255),
            outline=(255, 255, 255, 255)
        )

        draw.arc(
            (cx-65, cy-75, cx+65, cy+75),
            start=190,
            end=350,
            fill=(255, 255, 255, 255),
            width=13
        )

        draw.ellipse(
            (cx-28, cy-35, cx+28, cy+25),
            fill=(255, 255, 255, 230)
        )

    else:
        # General geometric artwork
        for _ in range(10):
            x = rng.randint(cx-170, cx+170)
            y = rng.randint(cy-170, cy+170)
            r = rng.randint(25, 75)

            color = (
                rng.randint(100, 255),
                rng.randint(100, 255),
                rng.randint(100, 255),
                220
            )

            draw.ellipse(
                (x-r, y-r, x+r, y+r),
                fill=color
            )


def render_post(fact, slot, date_key):
    width, height = 1080, 1350

    day_number = datetime.strptime(
        date_key, "%Y%m%d"
    ).date().toordinal()

    seed = day_number * 10 + slot
    rng = random.Random(seed)

    # Four different poster layouts
    layout = seed % 4

    image = make_gradient(
        (width, height),
        *fact["colors"]
    )

    draw = ImageDraw.Draw(image, "RGBA")

    # Decorative colorful circles
    for _ in range(20):
        x = rng.randint(-100, width+100)
        y = rng.randint(-100, height+100)
        radius = rng.randint(20, 100)

        color = (
            rng.randint(170, 255),
            rng.randint(170, 255),
            rng.randint(170, 255),
            23
        )

        draw.ellipse(
            (x-radius, y-radius, x+radius, y+radius),
            fill=color
        )

    # Main card frame
    draw.rounded_rectangle(
        (42, 42, 1038, 1308),
        radius=48,
        outline=(255, 255, 255, 130),
        width=4
    )

    # Category badge
    label_font = get_font(27, bold=True)

    draw.rounded_rectangle(
        (85, 85, 455, 158),
        radius=32,
        fill=(255, 255, 255, 45)
    )

    draw.text(
        (115, 105),
        fact["category"],
        font=label_font,
        fill="white"
    )

    # Illustration
    positions = [
        (540, 365),
        (720, 365),
        (360, 365),
        (540, 420)
    ]

    cx, cy = positions[layout]

    draw_visual(
        draw,
        fact["category"],
        cx,
        cy,
        seed
    )

    # Different card styles
    if layout == 0:
        draw.rounded_rectangle(
            (85, 590, 995, 1125),
            radius=42,
            fill=(255, 255, 255, 25)
        )

    elif layout == 1:
        draw.rounded_rectangle(
            (85, 590, 995, 1125),
            radius=42,
            outline=(255, 255, 255, 140),
            width=4
        )

    elif layout == 2:
        draw.rounded_rectangle(
            (85, 590, 995, 1125),
            radius=42,
            fill=(0, 0, 0, 28)
        )

    else:
        draw.line(
            (120, 610, 960, 610),
            fill=(255, 255, 255, 190),
            width=5
        )

    # Headline
    headline_font = get_font(53, bold=True)
    detail_font = get_font(30)
    footer_font = get_font(23)

    headline_lines = wrap_text(
        draw,
        fact["headline"],
        headline_font,
        840
    )

    y = 645 if layout != 3 else 670

    for line in headline_lines[:3]:
        bbox = draw.textbbox(
            (0, 0),
            line,
            font=headline_font
        )

        x = (width - (bbox[2] - bbox[0])) // 2

        draw.text(
            (x+3, y+4),
            line,
            font=headline_font,
            fill=(0, 0, 0, 75)
        )

        draw.text(
            (x, y),
            line,
            font=headline_font,
            fill="white"
        )

        y += 68

    y += 18

    # Detail
    detail_lines = wrap_text(
        draw,
        fact["detail"],
        detail_font,
        840
    )

    for line in detail_lines[:4]:
        bbox = draw.textbbox(
            (0, 0),
            line,
            font=detail_font
        )

        x = (width - (bbox[2] - bbox[0])) // 2

        draw.text(
            (x, y),
            line,
            font=detail_font,
            fill=(255, 255, 255, 245)
        )

        y += 46

    # Source footer
    source_text = f"Source: {fact['source']}"

    bbox = draw.textbbox(
        (0, 0),
        source_text,
        font=footer_font
    )

    draw.text(
        ((width - (bbox[2] - bbox[0])) // 2, 1160),
        source_text,
        font=footer_font,
        fill=(255, 255, 255, 230)
    )

    # Brand name
    brand = os.getenv("BRAND_NAME", "DAILY FACTS")
    brand_font = get_font(25, bold=True)

    bbox = draw.textbbox(
        (0, 0),
        brand,
        font=brand_font
    )

    draw.text(
        ((width - (bbox[2] - bbox[0])) // 2, 1220),
        brand,
        font=brand_font,
        fill=(255, 255, 255, 235)
    )

    path = OUT_DIR / f"{date_key}-post-{slot}.jpg"

    image.save(
        path,
        "JPEG",
        quality=94,
        optimize=True
    )

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


def choose_fact(slot, date_key):
    day_number = datetime.strptime(
        date_key, "%Y%m%d"
    ).date().toordinal()

    index = (day_number * 5 + slot - 1) % len(FACTS)

    return FACTS[index]


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--slot",
        type=int,
        choices=range(1, 6),
        default=None
    )

    parser.add_argument(
        "--dry-run",
        action="store_true"
    )

    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    date_key = now.strftime("%Y%m%d")

    slot = args.slot or int(os.getenv("POST_SLOT", "1"))

    if slot < 1 or slot > 5:
        raise SystemExit("POST_SLOT must be between 1 and 5.")

    fact = choose_fact(slot, date_key)

    image_path = render_post(
        fact,
        slot,
        date_key
    )

    caption = make_caption(fact)

    print(f"Generated image: {image_path}")
    print(f"Selected slot: {slot}")
    print(f"Fact category: {fact['category']}")
    print(f"Fact: {fact['headline']}")
    print(f"Source: {fact['source']}")
    print(f"Caption: {caption}")

    if args.dry_run:
        print("DRY RUN: no Facebook post was published.")
        return

    required = [
        "FB_PAGE_ID",
        "FB_PAGE_ACCESS_TOKEN"
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
        caption
    )

    print("FACEBOOK PUBLISHED SUCCESSFULLY")
    print(json.dumps(result)[:800])


if __name__ == "__main__":
    main()
