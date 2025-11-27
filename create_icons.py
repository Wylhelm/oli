import shutil
from PIL import Image
import os

def update_assets():
    source_logo = "logo.png"
    
    if not os.path.exists(source_logo):
        print(f"Error: {source_logo} not found in root.")
        return

    # Target paths for the main logo
    targets = [
        "extension/src/assets/logo.png",
        "extension/public/logo.png"
    ]
    
    # Copy the main logo
    for target in targets:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source_logo, target)
        print(f"Copied {source_logo} to {target}")

    # Generate icons from the logo
    try:
        img = Image.open(source_logo)
        
        # Icon sizes needed for Chrome extension
        icon_sizes = [16, 48, 128]
        
        for size in icon_sizes:
            # Resize using LANCZOS for high quality downsampling
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            target_icon = f"extension/public/icon{size}.png"
            resized_img.save(target_icon)
            print(f"Generated {target_icon}")
            
    except Exception as e:
        print(f"Error processing icons: {e}")

if __name__ == "__main__":
    update_assets()
