"""
merge_plants_images.py
-----------------------
BALANCED version: Takes a fixed number of images from EACH plant type
so the "not tomato" class stays balanced (~1000 images) like all other classes.

Strategy:
  - Original "not tomato" folder had 108 images
  - We want a total of ~1000 images in that class
  - So we pick  PER_PLANT = (1000 - original_count) / number_of_plant_types
    → roughly 20 images per plant type
  - This means: 108 original + (48 plants × ~18) ≈ 972 total  ✅ balanced!
"""

import os
import shutil
import random

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
# plant_leaves_source is kept OUTSIDE training_data so TF doesn't treat it as a class
PLANTS_FOLDER  = os.path.join(BASE_DIR, 'plant_leaves_source')
NOT_TOMATO_DIR = os.path.join(BASE_DIR, 'training_data',
                              'This picture does not have relationship with Tomato')

# ── SETTINGS ──────────────────────────────────────────────────────────────────
TARGET_TOTAL   = 1000   # we want the "not tomato" class to have ~this many images
IMAGE_EXTS     = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
RANDOM_SEED    = 42     # for reproducibility

# ── STEP 1: Remove previously merged plant images ─────────────────────────────
def clean_old_merged_images():
    """
    Removes images that were previously copied from plants_leaves.
    These are identified by having a plant-name prefix (e.g. 'Mango_image.jpg').
    Original images (random_*.jpg, synthetic_*.jpg) are kept safe.
    """
    if not os.path.exists(NOT_TOMATO_DIR):
        return 0

    # Collect all plant type names to identify previously merged files
    plant_names = []
    if os.path.exists(PLANTS_FOLDER):
        plant_names = [
            name for name in os.listdir(PLANTS_FOLDER)
            if os.path.isdir(os.path.join(PLANTS_FOLDER, name))
        ]

    removed = 0
    for filename in os.listdir(NOT_TOMATO_DIR):
        # Check if this file was copied from a plant folder (has plant name prefix)
        for plant_name in plant_names:
            if filename.startswith(plant_name + '_'):
                filepath = os.path.join(NOT_TOMATO_DIR, filename)
                os.remove(filepath)
                removed += 1
                break

    return removed


# ── STEP 2: Count original images already in "not tomato" folder ───────────────
def count_original_images():
    if not os.path.exists(NOT_TOMATO_DIR):
        return 0
    return sum(
        1 for f in os.listdir(NOT_TOMATO_DIR)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    )


# ── STEP 3: Copy balanced images from each plant type ─────────────────────────
def copy_balanced_images(per_plant: int):
    if not os.path.exists(PLANTS_FOLDER):
        print("❌ 'plants_leaves' folder not found!")
        return 0

    os.makedirs(NOT_TOMATO_DIR, exist_ok=True)
    random.seed(RANDOM_SEED)

    total_copied = 0

    plant_types = [
        name for name in os.listdir(PLANTS_FOLDER)
        if os.path.isdir(os.path.join(PLANTS_FOLDER, name))
    ]

    for plant_name in sorted(plant_types):
        plant_path = os.path.join(PLANTS_FOLDER, plant_name)

        # Get all images in this plant folder
        all_images = [
            f for f in os.listdir(plant_path)
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS
        ]

        if not all_images:
            print(f"  ⚠️  No images found in: {plant_name}")
            continue

        # Pick 'per_plant' images randomly (or all if folder has fewer)
        selected = random.sample(all_images, min(per_plant, len(all_images)))

        copied_this_plant = 0
        for filename in selected:
            src      = os.path.join(plant_path, filename)
            new_name = f"{plant_name}_{filename}"
            dest     = os.path.join(NOT_TOMATO_DIR, new_name)

            # Avoid name collision
            counter = 1
            while os.path.exists(dest):
                name_part, ext_part = os.path.splitext(new_name)
                dest = os.path.join(NOT_TOMATO_DIR, f"{name_part}_{counter}{ext_part}")
                counter += 1

            try:
                shutil.copy2(src, dest)
                copied_this_plant += 1
                total_copied += 1
            except Exception as e:
                print(f"    ⚠️  Error copying {filename}: {e}")

        print(f"  ✅ {plant_name:<35} → {copied_this_plant} images added")

    return total_copied


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  🌿 BALANCED PLANT IMAGE MERGER")
    print("=" * 55)

    # Step 1 — Clean previous merge
    print("\n🧹 Step 1: Removing previously merged images...")
    removed = clean_old_merged_images()
    print(f"   Removed {removed} old merged images.")

    # Step 2 — Count originals
    original_count = count_original_images()
    print(f"\n📁 Step 2: Original 'not tomato' images: {original_count}")

    # Step 3 — Calculate how many per plant type
    plant_types = [
        name for name in os.listdir(PLANTS_FOLDER)
        if os.path.isdir(os.path.join(PLANTS_FOLDER, name))
    ] if os.path.exists(PLANTS_FOLDER) else []

    num_plant_types = len(plant_types)
    remaining_slots = TARGET_TOTAL - original_count
    per_plant       = max(1, remaining_slots // num_plant_types)

    print(f"   Plant types found : {num_plant_types}")
    print(f"   Slots available   : {remaining_slots}")
    print(f"   Images per type   : {per_plant}")

    # Step 4 — Copy balanced images
    print(f"\n📋 Step 3: Copying {per_plant} images from each plant type...\n")
    total_copied = copy_balanced_images(per_plant)

    # Final report
    final_total = count_original_images()
    other_classes_avg = 1000  # each tomato disease class has ~1000

    print("\n" + "=" * 55)
    print("  ✅ DONE! FINAL DATASET SUMMARY")
    print("=" * 55)
    print(f"  Original 'not tomato' images : {original_count}")
    print(f"  New plant images added       : {total_copied}")
    print(f"  ──────────────────────────────────────")
    print(f"  Total 'not tomato' images    : {final_total}")
    print(f"  Other classes (avg)          : ~{other_classes_avg}")

    diff = abs(final_total - other_classes_avg)
    balance_ok = diff < 200
    status = "✅ BALANCED" if balance_ok else "⚠️  Slightly off"
    print(f"  Balance status               : {status} (diff: {diff})")
    print("=" * 55)
    print("\n🚀 Next step: cd train_model && python trainer.py")
    print("=" * 55)


if __name__ == '__main__':
    main()
