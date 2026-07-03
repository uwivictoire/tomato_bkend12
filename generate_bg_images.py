import os
import random
from PIL import Image, ImageDraw

TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'train_model', 'training_data', 'Not Included In Dataset')

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

print(f"Generating 100 random images to {TARGET_DIR}...")

for i in range(1, 101):
    # Create image with random background color
    bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', (224, 224), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw some random shapes
    for _ in range(random.randint(3, 10)):
        shape_type = random.choice(['rectangle', 'ellipse', 'line'])
        x0 = random.randint(0, 200)
        y0 = random.randint(0, 200)
        x1 = random.randint(x0, 224)
        y1 = random.randint(y0, 224)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        if shape_type == 'rectangle':
            draw.rectangle([x0, y0, x1, y1], fill=color)
        elif shape_type == 'ellipse':
            draw.ellipse([x0, y0, x1, y1], fill=color)
        else:
            draw.line([x0, y0, x1, y1], fill=color, width=random.randint(1, 10))
            
    filename = os.path.join(TARGET_DIR, f"synthetic_{i}.jpg")
    img.save(filename)

print("Generation complete.")
