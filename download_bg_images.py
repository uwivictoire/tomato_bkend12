import os
import urllib.request
import time

TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'train_model', 'training_data', 'Not Included In Dataset')

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

print(f"Downloading 100 random images to {TARGET_DIR}...")

# Use Picsum to get random 224x224 images
base_url = "https://picsum.photos/224/224?random="

for i in range(1, 101):
    url = f"{base_url}{i}"
    filename = os.path.join(TARGET_DIR, f"random_{i}.jpg")
    try:
        urllib.request.urlretrieve(url, filename)
        if i % 10 == 0:
            print(f"Downloaded {i}/100...")
        time.sleep(0.1) # Be polite to the server
    except Exception as e:
        print(f"Failed to download image {i}: {e}")

print("Download complete.")
