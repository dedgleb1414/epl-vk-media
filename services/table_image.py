from PIL import Image, ImageDraw, ImageFont
import os

def generate_table_image(standings, league_name):
    rows = len(standings)
    width = 700
    row_h = 36
    header_h = 60
    padding = 20
    height = header_h + row_h * rows + padding * 2

    img = Image.new("RGB", (width, height), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 18)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
        font_title = ImageFont.truetype("arialbd.ttf", 24)
    except:
        font = ImageFont.load_default()
        font_bold = font
        font_title = font

    # Заголовок
    draw.rectangle([0, 0, width, header_h], fill=(30, 30, 50))
    draw.text((padding, 15), "📊 " + league_name, font=font_title, fill=(255, 215, 0))

    # Шапка таблицы
    y = header_h + 5
    draw.text((padding, y), "#", font=font_bold, fill=(180, 180, 180))
    draw.text((60, y), "Команда", font=font_bold, fill=(180, 180, 180))
    draw.text((420, y), "И", font=font_bold, fill=(180, 180, 180))
    draw.text((460, y), "В", font=font_bold, fill=(180, 180, 180))
    draw.text((500, y), "Н", font=font_bold, fill=(180, 180, 180))
    draw.text((540, y), "П", font=font_bold, fill=(180, 180, 180))
    draw.text((600, y), "О", font=font_bold, fill=(255, 215, 0))

    y += row_h

    for i, s in enumerate(standings):
        # Чередование строк
        if i % 2 == 0:
            draw.rectangle([0, y - 4, width, y + row_h - 6], fill=(28, 28, 42))
        else:
            draw.rectangle([0, y - 4, width, y + row_h - 6], fill=(22, 22, 35))

        # Цвет позиции
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

    path = "data/table.png"
    img.save(path)
    return path