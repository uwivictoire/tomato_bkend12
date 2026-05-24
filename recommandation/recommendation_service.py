import pandas as pd
import os
import re
from django.conf import settings

# Global cache for disease data
_DISEASE_ROWS_CACHE = None

def _load_disease_data():
    """
    Loads the CSV into memory and prepares a list of clean dictionaries for matching.
    """
    global _DISEASE_ROWS_CACHE
    if _DISEASE_ROWS_CACHE is not None:
        return _DISEASE_ROWS_CACHE

    csv_path = os.path.join(settings.BASE_DIR, 'recommandation', 'tomato_diseases.csv')
    if not os.path.exists(csv_path):
        print(f"[WARNING] Recommendation CSV not found at {csv_path}")
        return []

    try:
        # Read the CSV with correct encoding
        df = pd.read_csv(csv_path, encoding='latin-1')
        
        # Clean column names (strip whitespace)
        df.columns = [c.strip() for c in df.columns]
        
        rows_list = []
        for _, row in df.iterrows():
            temp_cond = str(row.get("Temperature Condition", "")).strip().replace('\x96', '-').replace('\u2013', '-')
            hum_cond = str(row.get("Humidity Condition", "")).strip().replace('\x96', '-').replace('\u2013', '-')
            
            rec = {
                "image_result": str(row.get("Image Result", "")).strip(),
                "temperature_condition": temp_cond,
                "humidity_condition": hum_cond,
                "recommendation": str(row.get("Recommendation", "")).strip()
            }
            rows_list.append(rec)
            
        _DISEASE_ROWS_CACHE = rows_list
        print(f"--- [SYSTEM] Tomato Disease Recommendations Cached ({len(_DISEASE_ROWS_CACHE)} items) ---")
        return _DISEASE_ROWS_CACHE
    except Exception as e:
        print(f"[ERROR] Failed to cache recommendations: {str(e)}")
        return []

def _check_condition(value, condition_str):
    """
    Evaluates whether a sensor reading value matches the condition string from the CSV.
    """
    if value is None:
        return True  # If no sensor data is provided, treat as matching to ensure fallback
    if not condition_str or not isinstance(condition_str, str):
        return True

    # Normalize en-dash/em-dash to a standard hyphen and lowercase
    cond = condition_str.lower().strip()
    
    # Try to extract numeric values
    numbers = [float(x) for x in re.findall(r'[-+]?\d*\.?\d+', cond)]
    
    if '>' in cond:
        if len(numbers) >= 1:
            return value > numbers[0]
    elif '<' in cond:
        if len(numbers) >= 1:
            return value < numbers[0]
    elif '-' in cond or len(numbers) == 2:
        if len(numbers) >= 2:
            return numbers[0] <= value <= numbers[1]
            
    return True

def _normalize_disease_name(disease_name):
    """
    Normalizes input model prediction labels to match the CSV's 'Image Result' values.
    """
    if not disease_name:
        return ""
    name_lower = disease_name.lower().strip()
    if "healthy" in name_lower:
        return "tomato healthy"
    if "spider" in name_lower:
        return "spider mites (two-spotted spider mite)"
    if "yellow leaf curl" in name_lower:
        return "tomato yellow leaf curl virus"
    if "mosaic" in name_lower:
        return "tomato mosaic virus"
    return name_lower

def get_recommendation(disease_name, temperature=None, humidity=None):
    """
    Fetch recommendation details based on disease name, temperature, and humidity.
    """
    rows = _load_disease_data()
    if not rows:
        return None

    if not disease_name:
        return None

    search_term = disease_name.lower().strip()
    
    # Check for Out-of-Domain message
    if search_term == "non-tomato image":
        return {
            "disease_name": "Non-Tomato Image Detected",
            "temperature_condition": "N/A",
            "humidity_condition": "N/A",
            "recommendation": "Please upload a clear, high-resolution photo of a single tomato leaf.",
            "treatment": "Please upload a clear, high-resolution photo of a single tomato leaf.",
            "prevention": "Ensure proper lighting and focus when taking pictures of your plants.",
            "alert_message": "Action Required: Please re-upload a valid tomato leaf image for analysis.",
            "severity": "Low"
        }

    target_disease = _normalize_disease_name(disease_name)
    
    # 1. Filter rows by disease name matching
    matched_disease_rows = []
    for row in rows:
        row_name = row['image_result'].lower().strip()
        if target_disease in row_name or row_name in target_disease:
            matched_disease_rows.append(row)
            
    if not matched_disease_rows:
        return None

    # 2. Try to find a row that satisfies both temperature and humidity conditions
    best_row = None
    for row in matched_disease_rows:
        temp_match = _check_condition(temperature, row['temperature_condition'])
        hum_match = _check_condition(humidity, row['humidity_condition'])
        if temp_match and hum_match:
            best_row = row
            break

    # 3. Fallback to the first matched disease row if no perfect match found
    if not best_row:
        best_row = matched_disease_rows[0]

    # 4. Formulate the response dict (ensuring backwards compatibility)
    rec_text = best_row['recommendation']
    
    # Determine severity dynamically
    if "healthy" in target_disease:
        severity = "Low"
    elif "virus" in target_disease or "blight" in target_disease:
        severity = "High"
    else:
        severity = "Medium"
        
    # Dynamic Alert Message based on environment & severity
    if "healthy" in target_disease:
        if temperature is not None or humidity is not None:
            # Let's see if the matched row's conditions are not Normal
            if "Normal" not in best_row['temperature_condition'] or "Normal" not in best_row['humidity_condition']:
                alert_message = f"Alert: Crop is currently healthy, but environmental stressors detected (Temp: {temperature}°C, Humidity: {humidity}%)."
            else:
                alert_message = "Normal: Crop appears healthy under current conditions."
        else:
            alert_message = "Normal: Crop appears healthy under current conditions."
    else:
        alert_message = f"Warning: Crop exhibiting symptoms of {best_row['image_result']}. Action required."

    return {
        "disease_name": best_row['image_result'],
        "temperature_condition": best_row['temperature_condition'],
        "humidity_condition": best_row['humidity_condition'],
        "recommendation": rec_text,
        
        # Backwards compatibility keys
        "causal_agent": "N/A",
        "symptoms": f"Sensor Conditions - Temp: {best_row['temperature_condition']}, Humidity: {best_row['humidity_condition']}",
        "treatment": rec_text,
        "prevention": "Maintain recommended ranges and follow the suggested treatment.",
        "alert_message": alert_message,
        "severity": severity
    }
