"""
download_nontomato_images.py
----------------------------
Downloads diverse real-world images (animals, food, buildings, people, vehicles, etc.)
to add to the "Non-Tomato" training class.

WHY THIS IS NEEDED:
  The current Non-Tomato class only has other PLANT LEAVES (mango, banana, etc.).
  This causes the model to confuse real-world Google tomato images with "other plants"
  because real photos look different from lab photos.

  Adding diverse everyday images helps the model learn:
  ✅ "This is clearly NOT a tomato plant" = cars, buildings, animals, food
  ✅ Makes the Non-Tomato boundary much sharper

HOW TO USE:
  cd /Users/mackbook/Desktop/tomato_backend/train_model
  python download_nontomato_images.py

  Then retrain:
  python trainer.py
"""

import os
import urllib.request
import time
import random

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
NOT_TOMATO_DIR = os.path.join(BASE_DIR, 'training_data',
                              'This picture does not have relationship with Tomato')

os.makedirs(NOT_TOMATO_DIR, exist_ok=True)

# ── HOW MANY TO DOWNLOAD ───────────────────────────────────────────────────────
# We download enough to bring the Non-Tomato class to ~1500
# (slightly more than other classes = model is slightly stricter)
TOTAL_TO_DOWNLOAD = 600   # Adjust if you want more

# ── IMAGE CATEGORIES FROM PICSUM (random real-world images) ───────────────────
# Picsum gives random photography — landscapes, people, objects, food, animals
# We use multiple random seeds to get diverse images

print("=" * 60)
print("  📥 Non-Tomato Image Downloader")
print("=" * 60)
print(f"\nSaving to: {NOT_TOMATO_DIR}")

# Count existing images
existing = [f for f in os.listdir(NOT_TOMATO_DIR)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
print(f"Existing images: {len(existing)}")
print(f"Planning to download: {TOTAL_TO_DOWNLOAD} new images\n")

downloaded = 0
failed     = 0

# Strategy: use different seeds and sizes to get truly random diverse images
# We mix different image IDs from Picsum (0–1084 are valid IDs)
random.seed(99)

# Gather a set of IDs we haven't already downloaded
used_suffix = set()

for i in range(1, TOTAL_TO_DOWNLOAD + 200):  # extra attempts in case of failures
    if downloaded >= TOTAL_TO_DOWNLOAD:
        break

    # Use specific Picsum IDs for controlled diversity
    # IDs 1-1084 cover: nature, people, animals, buildings, food, vehicles, etc.
    img_id = random.randint(1, 1084)
    
    # Use 224x224 to match model input size
    url      = f"https://picsum.photos/id/{img_id}/224/224"
    filename = f"realworld_{img_id}_{i}.jpg"
    filepath = os.path.join(NOT_TOMATO_DIR, filename)

    # Skip if already exists
    if os.path.exists(filepath):
        continue

    try:
        urllib.request.urlretrieve(url, filepath)
        downloaded += 1

        if downloaded % 50 == 0:
            print(f"  ✅ Downloaded {downloaded}/{TOTAL_TO_DOWNLOAD}...")
        
        time.sleep(0.05)  # Be polite to the server

    except Exception as e:
        failed += 1
        if failed <= 5:
            print(f"  ⚠️  Failed to download id={img_id}: {e}")

# Final report
final_count = len([f for f in os.listdir(NOT_TOMATO_DIR)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))])

print("\n" + "=" * 60)
print("  ✅ DONE!")
print("=" * 60)
print(f"  New images downloaded  : {downloaded}")
print(f"  Download failures      : {failed}")
print(f"  Total in Non-Tomato    : {final_count}")
print(f"  Other classes have     : ~1000 each")

if final_count > 1400:
    print(f"\n  ✅ Great! Non-Tomato class has MORE data → stricter detection")
elif final_count >= 900:
    print(f"\n  ✅ Non-Tomato class is balanced (within range)")
else:
    print(f"\n  ⚠️  Non-Tomato class is low. Consider re-running this script.")

print("\n" + "=" * 60)
print("  🚀 NEXT STEP: Retrain the model")
print("     cd /Users/mackbook/Desktop/tomato_backend/train_model")
print("     python trainer.py")
print("=" * 60)
