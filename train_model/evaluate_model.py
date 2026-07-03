import os
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(_file_))
DATA_PATH = os.path.join(BASE_DIR, 'training_data')
MODEL_SAVE_PATH = os.path.join(BASE_DIR, 'tomato_model.keras')

def load_validation_dataset():
    """Loads the validation dataset matching the trainer setup."""
    IMG_HEIGHT = 224
    IMG_WIDTH = 224
    BATCH_SIZE = 32

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_PATH,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE
    )
    class_names = val_ds.class_names
    
    # Optimize dataset performance
    AUTOTUNE = tf.data.AUTOTUNE
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    
    return val_ds, class_names

def evaluate_model_performance(model, val_ds, class_names):
    """
    Evaluates the model on the validation dataset and displays
    accuracy, precision, recall, and F1-score.
    """
    print("\n" + "="*60)
    print("           MODEL EVALUATION ON VALIDATION DATASET           ")
    print("="*60)
    print("Generating predictions...")

    y_true = []
    y_pred = []
    
    # Predict in batches to avoid memory/ordering issues
    for images, labels in val_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy())
        y_pred.extend(np.argmax(preds, axis=1))

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average='macro'
    )
    weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average='weighted'
    )

    print("\n--- Summary Metrics ---")
    print(f"Accuracy:           {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print(f"Macro Precision:    {macro_precision:.4f}")
    print(f"Macro Recall:       {macro_recall:.4f}")
    print(f"Macro F1-Score:     {macro_f1:.4f}")
    print(f"Weighted F1-Score:  {weighted_f1:.4f}")
    
    print("\n--- Detailed Classification Report ---")
    report = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        digits=4
    )
    print(report)
    print("="*60 + "\n")

def main():
    if not os.path.exists(MODEL_SAVE_PATH):
        print(f"Error: Model file not found at '{MODEL_SAVE_PATH}'. Please run training first.")
        return

    print(f"Loading model from: {MODEL_SAVE_PATH}")
    model = tf.keras.models.load_model(MODEL_SAVE_PATH)
    
    print(f"Loading validation dataset from: {DATA_PATH}")
    val_ds, class_names = load_validation_dataset()
    
    evaluate_model_performance(model, val_ds, class_names)

if _name_ == "_main_":
    main()