from PIL import Image, ImageDraw

def create_icon(size, filename):
    img = Image.new('RGB', (size, size), color = '#005696')
    d = ImageDraw.Draw(img)
    d.text((size//4, size//4), "OLI", fill=(255, 255, 255))
    img.save(filename)

create_icon(16, "extension/public/icon16.png")
create_icon(48, "extension/public/icon48.png")
create_icon(128, "extension/public/icon128.png")
print("Icons created.")
