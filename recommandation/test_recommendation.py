import os
import django
import sys

# Set up Django environment
sys.path.append('c:/Users/user/Desktop/tomato_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tomato_backend.settings')
django.setup()

from recommandation.recommendation_service import get_recommendation

def test_recommendations():
    print("==================================================")
    print("STARTING TOMATO RECOMMENDATION SYSTEM UNIT TESTS")
    print("==================================================")
    
    test_cases = [
        {
            "desc": "Tomato Healthy - Normal Conditions",
            "disease": "Tomato healthy",
            "temp": 22.0,
            "hum": 70.0,
            "expected_rec_snippet": "Continue normal watering"
        },
        {
            "desc": "Tomato Healthy - High Temp / Low Humidity",
            "disease": "Tomato healthy",
            "temp": 30.0,
            "hum": 50.0,
            "expected_rec_snippet": "Increase watering and maintain moisture"
        },
        {
            "desc": "Tomato Healthy - Low Temp / High Humidity",
            "disease": "Tomato healthy",
            "temp": 15.0,
            "hum": 85.0,
            "expected_rec_snippet": "Monitor plant and improve air circulation"
        },
        {
            "desc": "Tomato Healthy - None environmental parameters (Fallback check)",
            "disease": "Healthy",
            "temp": None,
            "hum": None,
            "expected_rec_snippet": "Continue normal watering"
        },
        {
            "desc": "Bacterial Spot - Standard conditions matching",
            "disease": "Bacterial Spot",
            "temp": 25.0,
            "hum": 82.0,
            "expected_rec_snippet": "Spray Copper hydroxide"
        },
        {
            "desc": "Spider Mites - High temp / low humidity matching",
            "disease": "Spider Mites",
            "temp": 28.0,
            "hum": 55.0,
            "expected_rec_snippet": "Apply Neem oil"
        },
        {
            "desc": "Non-Tomato Image - Out of domain check",
            "disease": "Non-Tomato Image",
            "temp": None,
            "hum": None,
            "expected_rec_snippet": "re-upload a valid tomato leaf image"
        }
    ]
    
    success_count = 0
    
    for case in test_cases:
        print(f"\n--- {case['desc']} ---")
        print(f"Input: Disease='{case['disease']}', Temp={case['temp']}, Humidity={case['hum']}")
        
        result = get_recommendation(case["disease"], case["temp"], case["hum"])
        if result:
            print(f"Matched Disease Name: {result['disease_name']}")
            print(f"Matched Temp Cond:    {result['temperature_condition']}")
            print(f"Matched Hum Cond:     {result['humidity_condition']}")
            print(f"Recommendation:       {result['recommendation']}")
            print(f"Severity Level:       {result['severity']}")
            print(f"System Alert Message: {result['alert_message']}")
            
            snippet = case["expected_rec_snippet"].lower()
            rec_text = result["recommendation"].lower()
            alert_text = result["alert_message"].lower()
            
            if snippet in rec_text or snippet in alert_text:
                print("Result: [PASS]")
                success_count += 1
            else:
                print(f"Result: [FAIL] (Expected snippet '{case['expected_rec_snippet']}' not found)")
        else:
            print("Result: [FAIL] (No recommendation returned)")
            
    print("\n==================================================")
    print(f"TEST RESULTS: {success_count}/{len(test_cases)} PASSED")
    print("==================================================")
    
    if success_count == len(test_cases):
        print("ALL TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME TESTS FAILED! PLEASE CHECK THE LOGS.")
        sys.exit(1)

if __name__ == "__main__":
    test_recommendations()
