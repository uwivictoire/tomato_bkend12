import os
import tensorflow as tf
from tensorflow.keras import layers, models

# 1. SETUP PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'training_data')
# Changed extension to .keras
MODEL_SAVE_PATH = os.path.join(BASE_DIR, 'tomato_model.keras')

def start_training():
    # 2. PARAMETERS
    IMG_HEIGHT = 224
    IMG_WIDTH = 224
    BATCH_SIZE = 32
    EPOCHS = 20 

    print(f"--- Starting AI Training for Tomatoes ---")
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

    # 4. DATA AUGMENTATION
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
    ])

    # 5. BUILD THE CNN MODEL
    model = models.Sequential([
        data_augmentation,
        layers.Rescaling(1./255, input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D(),
        
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D(),
        
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D(),
        
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5), 
        layers.Dense(len(class_names), activation='softmax')
    ])

    # 6. COMPILE
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    # 7. TRAIN
    print("Training in progress... please wait.")
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )

    # 8. SAVE THE MODEL (Using the new .keras format)
    model.save(MODEL_SAVE_PATH)
    print(f"--- Training Complete! ---")
    print(f"Model saved successfully at: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    start_training()