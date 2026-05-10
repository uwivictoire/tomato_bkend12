import pandas as pd
import os
from django.conf import settings

# Global cache for disease data
_DISEASE_DATA_CACHE = None
_DISEASE_DICT_CACHE = {}

def _load_disease_data():
    """
    Loads the CSV into memory and prepares a lookup dictionary.
    """
    global _DISEASE_DATA_CACHE, _DISEASE_DICT_CACHE
    if _DISEASE_DATA_CACHE is not None:
        return _DISEASE_DATA_CACHE

    csv_path = os.path.join(settings.BASE_DIR, 'recommandation', 'tomato_diseases.csv')
    if not os.path.exists(csv_path):
        print(f"[WARNING] Recommendation CSV not found at {csv_path}")
        return None

    try:
        # Read the CSV once and cache it
        df = pd.read_csv(csv_path, encoding='latin-1')
        # Clean column names (strip whitespace)
        df.columns = [c.strip() for c in df.columns]
        _DISEASE_DATA_CACHE = df

        # Prepare dictionary cache for near-instant lookup
        search_col = "Disease Name"
        if search_col not in df.columns:
            cols = [c for c in df.columns if 'Disease' in c]
            search_col = cols[0] if cols else None

        if search_col:
            for _, row in df.iterrows():
                name = str(row[search_col]).lower().strip()
                rec = {
                    "disease_name": row.get("Disease Name", ""),
                    "causal_agent": row.get("Causal Agent", "N/A"),
                    "symptoms": row.get("Key Symptoms (Visual & Sensor Indicators)", "N/A"),
                    "treatment": row.get("Recommended Treatment", "N/A"),
                    "prevention": row.get("Preventive Measures", "N/A"),
                    "alert_message": row.get("IoT System Alert Message", "N/A"),
                    "severity": row.get("Severity Level", "N/A")
                }
                _DISEASE_DICT_CACHE[name] = rec
                
        print(f"--- [SYSTEM] Tomato Disease Recommendations Cached ({len(_DISEASE_DICT_CACHE)} items) ---")
        return _DISEASE_DATA_CACHE
    except Exception as e:
        print(f"[ERROR] Failed to cache recommendations: {str(e)}")
        return None

def get_recommendation(disease_name):
    """
    Fetch recommendation details from the cached dictionary based on disease name.
    """
    if not _DISEASE_DICT_CACHE:
        _load_disease_data()
    
    if not disease_name:
        return None

    search_term = disease_name.lower().strip()
    
    # 1. Try exact match in dict
    if search_term in _DISEASE_DICT_CACHE:
        return _DISEASE_DICT_CACHE[search_term]

    # 2. Try partial match if exact fails
    for name, rec in _DISEASE_DICT_CACHE.items():
        if search_term in name or name in search_term:
            return rec

    # 3. Fallback for common terms
    if "healthy" in search_term:
        for name, rec in _DISEASE_DICT_CACHE.items():
            if "healthy" in name:
                return rec

    return None
