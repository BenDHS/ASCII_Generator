import os
from PIL import Image, ImageDraw, ImageFont

input_folder = "input"

output_txt_folder = "output-txt"
output_png_folder = "output-png"

# "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,^`'. "
ASCII_CHARS = "@%#*+=-:. "

OUTPUT_WIDTH = 500

BLACK_THRESHOLD = 15

#For windwows, use any monospace font like Consolas ""C:/Windows/Fonts/consola.ttf" "
FONT_PATH = "/System/Library/Fonts/Monaco.ttf"

FONT_SIZE = 12


def image_to_ascii(image_path, output_width=OUTPUT_WIDTH):
    """Convert an image to ASCII art string, ignoring near-black areas."""
    img = Image.open(image_path).convert("L")  

    # maintain aspect ratio (font is taller than wide → adjust by ~0.55)
    aspect_ratio = img.height / img.width
    new_height = int(output_width * aspect_ratio * 0.55)
    img = img.resize((output_width, new_height))

    pixels = img.getdata()
    ascii_str = ""

    for pixel in pixels:
        if pixel < BLACK_THRESHOLD:
            ascii_str += " "
        else:
            ascii_str += ASCII_CHARS[pixel * len(ASCII_CHARS) // 256]

    # Break into lines
    ascii_lines = [ascii_str[i:i + output_width] for i in range(0, len(ascii_str), output_width)]
    return "\n".join(ascii_lines)


def ascii_to_png(ascii_art, output_path, font_path=FONT_PATH, font_size=FONT_SIZE):
    """Render ASCII text to a PNG image using Pillow."""
    lines = ascii_art.split("\n")
    font = ImageFont.truetype(font_path, font_size)

    bbox = font.getbbox("A")
    char_width, char_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    img_width = char_width * len(lines[0])
    img_height = char_height * len(lines)
    
    #Background color for png output
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines):
        draw.text((0, i * char_height), line, font=font, fill="black")

    img.save(output_path)



def process_frames(input_folder, txt_folder, png_folder):
    os.makedirs(txt_folder, exist_ok=True)
    os.makedirs(png_folder, exist_ok=True)

    for filename in sorted(os.listdir(input_folder)):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            frame_num = os.path.splitext(filename)[0]
            input_path = os.path.join(input_folder, filename)
            txt_path = os.path.join(txt_folder, f"{frame_num}.txt")
            png_path = os.path.join(png_folder, f"{frame_num}.png")

            ascii_art = image_to_ascii(input_path)

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(ascii_art)

            ascii_to_png(ascii_art, png_path)

            print(f"Processed {filename} -> {txt_path}, {png_path}")


if __name__ == "__main__":
    process_frames(input_folder, output_txt_folder, output_png_folder)
