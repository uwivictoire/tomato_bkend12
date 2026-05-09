import pandas as pd
import os
from django.conf import settings

def get_recommendation(disease_name):
    """
    Fetch recommendation details from tomato_diseases.csv based on disease name.
    """
    csv_path = os.path.join(settings.BASE_DIR, 'recommandation', 'tomato_diseases.csv')
    
    if not os.path.exists(csv_path):
        return None

    try:
        # Read the CSV - using latin-1 to handle special characters common in Windows CSVs
        df = pd.read_csv(csv_path, encoding='latin-1')
        
        # Clean column names (strip whitespace)
        df.columns = [c.strip() for c in df.columns]
        
        # Normalize disease name for matching
        search_col = "Disease Name"
        if search_col not in df.columns:
            cols = [c for c in df.columns if 'Disease' in c]
            search_col = cols[0] if cols else None

        if not search_col:
            return None

        # Clean search term: lowercase and strip
        search_term = disease_name.lower().strip()
        
        # Special case for Healthy
        if "healthy" in search_term:
            match = df[df[search_col].str.lower().str.contains("healthy", na=False)]
            if not match.empty:
                row = match.iloc[0]
                return {
                    "disease_name": row.get("Disease Name", "Healthy"),
                    "causal_agent": row.get("Causal Agent", "None"),
                    "symptoms": row.get("Key Symptoms (Visual & Sensor Indicators)", "Normal"),
                    "treatment": row.get("Recommended Treatment", "N/A"),
                    "prevention": row.get("Preventive Measures", "N/A"),
                    "alert_message": row.get("IoT System Alert Message", "N/A"),
                    "severity": row.get("Severity Level", "HEALTHY")
                }

        # Try exact match first
        match = df[df[search_col].str.lower().str.strip() == search_term]
        
        # If no exact match, try "contains" match
        if match.empty:
            match = df[df[search_col].str.lower().str.contains(search_term, na=False)]
        
        # If still no match, try splitting the search term and checking first word (e.g., "Early" from "Early blight")
        if match.empty:
            first_word = search_term.split()[0]
            match = df[df[search_col].str.lower().str.contains(first_word, na=False)]

        if match.empty:
            return None
        
        # Get the first match
        row = match.iloc[0]
        
        return {
            "disease_name": row.get("Disease Name", disease_name),
            "causal_agent": row.get("Causal Agent", "N/A"),
            "symptoms": row.get("Key Symptoms (Visual & Sensor Indicators)", "N/A"),
            "treatment": row.get("Recommended Treatment", "N/A"),
            "prevention": row.get("Preventive Measures", "N/A"),
            "alert_message": row.get("IoT System Alert Message", "N/A"),
            "severity": row.get("Severity Level", "N/A")
        }
        
    except Exception as e:
        print(f"Error reading recommendations: {str(e)}")
        return None
