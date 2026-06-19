from PIL import Image, ImageDraw, ImageFont
import os

def load_fonts():
    try:
        return (
            ImageFont.truetype("arial.ttf", 18),
            ImageFont.truetype("arialbd.ttf", 20),
            ImageFont.truetype("arialbd.ttf", 24),
        )
    except Exception:
        try:
            return (
                ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18),
                ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20),
                ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24),
            )
        except Exception:
            font = ImageFont.load_default()
            return font, font, font

def draw_group_table(draw, y, group_name, teams, font, font_bold, width, padding, row_h):
    if group_name:
        draw.text((padding, y), group_name, font=font_bold, fill=(255, 215, 0))
        y += row_h

    draw.text((padding, y), "#", font=font_bold, fill=(180, 180, 180))
    draw.text((60, y), "Команда", font=font_bold, fill=(180, 180, 180))
    draw.text((420, y), "И", font=font_bold, fill=(180, 180, 180))
    draw.text((460, y), "В", font=font_bold, fill=(180, 180, 180))
    draw.text((500, y), "Н", font=font_bold, fill=(180, 180, 180))
    draw.text((540, y), "П", font=font_bold, fill=(180, 180, 180))
    draw.text((600, y), "О", font=font_bold, fill=(255, 215, 0))
    y += row_h

    rows = len(teams)
    for i, s in enumerate(teams):
        if i % 2 == 0:
            draw.rectangle([0, y - 4, width, y + row_h - 6], fill=(28, 28, 42))
        else:
            draw.rectangle([0, y - 4, width, y + row_h - 6], fill=(22, 22, 35))

        if i < 4:
            num_color = (100, 200, 100)
        elif i < 6:
            num_color = (100, 150, 255)
        elif i >= rows - 3:
            num_color = (255, 100, 100)
        else:
            num_color = (200, 200, 200)

        draw.text((padding, y), str(i + 1), font=font, fill=num_color)
        draw.text((60, y), s["team"][:22], font=font, fill=(240, 240, 240))
        draw.text((420, y), str(s["gp"]), font=font, fill=(200, 200, 200))
        draw.text((460, y), str(s["w"]), font=font, fill=(100, 220, 100))
        draw.text((500, y), str(s["d"]), font=font, fill=(200, 200, 200))
        draw.text((540, y), str(s["l"]), font=font, fill=(220, 100, 100))
        draw.text((600, y), str(s["pts"]), font=font, fill=(255, 215, 0))

        y += row_h

    return y

def generate_table_image(groups, league_name):
    width = 700
    row_h = 36
    header_h = 60
    padding = 20

    body_rows = 0
    for g in groups:
        body_rows += len(g["teams"]) + 1
        if g.get("name"):
            body_rows += 1

    height = header_h + row_h * body_rows + padding * 2

    img = Image.new("RGB", (width, height), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)
    font, font_bold, font_title = load_fonts()

    draw.rectangle([0, 0, width, header_h], fill=(30, 30, 50))
    draw.text((padding, 15), "Таблица " + league_name, font=font_title, fill=(255, 215, 0))

    y = header_h + 5
    for g in groups:
        y = draw_group_table(draw, y, g.get("name"), g["teams"], font, font_bold, width, padding, row_h)

    path = "/tmp/table.png"
    if os.name == "nt":
        path = "data/table.png"
    img.save(path)
    return path

def generate_scorers_image(scorers, league_name):
    width = 600
    row_h = 38
    header_h = 60
    padding = 20
    rows = len(scorers)
    height = header_h + row_h * (rows + 1) + padding * 2

    img = Image.new("RGB", (width, height), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)
    font, font_bold, font_title = load_fonts()

    draw.rectangle([0, 0, width, header_h], fill=(30, 30, 50))
    draw.text((padding, 15), "Бомбардиры " + league_name, font=font_title, fill=(255, 215, 0))

    y = header_h + 5
    draw.text((padding, y), "#", font=font_bold, fill=(180, 180, 180))
    draw.text((60, y), "Игрок", font=font_bold, fill=(180, 180, 180))
    draw.text((380, y), "Клуб", font=font_bold, fill=(180, 180, 180))
    draw.text((550, y), "Г", font=font_bold, fill=(255, 215, 0))
    y += row_h

    for i, s in enumerate(scorers):
        if i % 2 == 0:
            draw.rectangle([0, y - 4, width, y + row_h - 6], fill=(28, 28, 42))
        else:
            draw.rectangle([0, y - 4, width, y + row_h - 6], fill=(22, 22, 35))

        num_color = (100, 200, 100) if i < 3 else (200, 200, 200)
        draw.text((padding, y), str(i + 1), font=font, fill=num_color)
        draw.text((60, y), s["name"][:28], font=font, fill=(240, 240, 240))
        draw.text((380, y), s["team"][:18], font=font, fill=(200, 200, 200))
        draw.text((550, y), str(s["goals"]), font=font, fill=(255, 215, 0))

        y += row_h

    path = "/tmp/scorers.png"
    if os.name == "nt":
        path = "data/scorers.png"
    img.save(path)
    return path
