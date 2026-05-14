import os
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import EarlyStopping

# 1. SETUP PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'training_data')
MODEL_SAVE_PATH = os.path.join(BASE_DIR, 'tomato_model.keras')

def start_training():
    # 2. PARAMETERS
    IMG_HEIGHT = 224
    IMG_WIDTH = 224
    BATCH_SIZE = 32
    EPOCHS = 30  # Increased because we are using EarlyStopping

    print(f"--- Starting AI Training for Tomatoes (Transfer Learning) ---")
    print(f"Loading images from: {DATA_PATH}")

    # 3. LOAD DATASET
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_PATH,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_PATH,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE
    )

    class_names = train_ds.class_names
    print(f"Detected Classes: {class_names}")

    # Optimize datasets for performance
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # 4. DATA AUGMENTATION (Enhanced to help model generalize better)
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.2),
        layers.RandomContrast(0.2),
    ])

    # 5. BUILD THE MODEL USING TRANSFER LEARNING (MobileNetV2)
    print("Downloading/Loading pre-trained MobileNetV2 base model...")
    # MobileNetV2 is lightweight, fast, and highly accurate for image classification
    base_model = MobileNetV2(
        input_shape=(IMG_HEIGHT, IMG_WIDTH, 3),
        include_top=False,
        weights='imagenet'
    )
    # Freeze the base model so we don't destroy the pre-trained weights
    base_model.trainable = False

    # Create the complete model architecture
    inputs = tf.keras.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 3))
    
    # 5.1 Apply augmentation
    x = data_augmentation(inputs)
    
    # 5.2 Preprocess inputs specifically for MobileNetV2 
    # (It expects values from [-1, 1], this replaces the old Rescaling layer)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    
    # 5.3 Pass through the base model
    x = base_model(x, training=False)
    
    # 5.4 Flatten and predict
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(len(class_names), activation='softmax')(x)

    model = tf.keras.Model(inputs, outputs)

    # 6. COMPILE
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    # 7. EARLY STOPPING (Stops training if validation loss doesn't improve)
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    )

    # 8. INITIAL TRAINING (Training just the top classification layer)
    print("Phase 1: Training top layers...")
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=3,
        callbacks=[early_stop]
    )

    # 9. FINE-TUNING (Unfreezing top layers of base model for better accuracy)
    print("Phase 2: Fine-tuning the model...")
    base_model.trainable = True
    
    # Freeze all layers except the top 50
    fine_tune_at = len(base_model.layers) - 50
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False

    # Re-compile with a much lower learning rate for fine-tuning
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=3,
        callbacks=[early_stop]
    )

    # 10. SAVE THE MODEL
    model.save(MODEL_SAVE_PATH)
    print(f"--- Training Complete! ---")
    print(f"Model saved successfully at: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    start_training()