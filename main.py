
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

# Curated starter library. Add more verified facts to expand variety.
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
        bbox = draw.textbbox((0, 0), test, font=font)

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


def render_post(fact, slot, date_key):
    width, height = 1080, 1350

    image = make_gradient(
        (width, height),
        *fact["colors"],
    )

    draw = ImageDraw.Draw(image, "RGBA")

    draw.ellipse(
        (720, -170, 1240, 350),
        fill=(255, 255, 255, 24),
    )
    draw.ellipse(
        (-210, 930, 390, 1530),
        fill=(255, 255, 255, 18),
    )

    draw.rounded_rectangle(
        (72, 78, 1008, 1272),
        radius=42,
        outline=(255, 255, 255, 90),
        width=3,
    )

    label_font = get_font(28, bold=True)
    headline_font = get_font(59, bold=True)
    detail_font = get_font(34)
    footer_font = get_font(23)

    draw.rounded_rectangle(
        (112, 140, 430, 208),
        radius=28,
        fill=(255, 255, 255, 38),
    )

    draw.text(
        (140, 158),
        fact["category"],
        font=label_font,
        fill=(255, 255, 255, 255),
    )

    headline_lines = wrap_text(
        draw,
        fact["headline"],
        headline_font,
        820,
    )

    headline_height = len(headline_lines) * 76
    y = 330

    for line in headline_lines:
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        x = (width - (bbox[2] - bbox[0])) // 2

        draw.text(
            (x + 2, y + 3),
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

        y += 76

    y += 35

    draw.line(
        (350, y, 730, y),
        fill=(255, 255, 255, 170),
        width=4,
    )

    y += 55

    detail_lines = wrap_text(
        draw,
        fact["detail"],
        detail_font,
        820,
    )

    for line in detail_lines:
        bbox = draw.textbbox((0, 0), line, font=detail_font)
        x = (width - (bbox[2] - bbox[0])) // 2

        draw.text(
            (x, y),
            line,
            font=detail_font,
            fill=(255, 255, 255, 245),
        )

        y += 52

    source_text = f"Source: {fact['source']}"
    bbox = draw.textbbox((0, 0), source_text, font=footer_font)

    draw.text(
        ((width - (bbox[2] - bbox[0])) // 2, 1050),
        source_text,
        font=footer_font,
        fill=(255, 255, 255, 220),
    )

    brand = os.getenv("BRAND_NAME", "DAILY FACTS")
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


def choose_fact(slot, date_key):
    # Five consecutive facts are selected each day.
    # The library rotates after all available facts have been used.
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

    fact = choose_fact(slot, date_key)

    image_path = render_post(fact, slot, date_key)
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
        caption,
    )

    print("FACEBOOK PUBLISHED SUCCESSFULLY")
    print(json.dumps(result)[:800])


if __name__ == "__main__":
    main()
