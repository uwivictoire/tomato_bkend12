import os
import django
import sys

# Set up Django environment
sys.path.append('c:/Users/user/Desktop/tomato_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tomato_backend.settings')
django.setup()

from recommandation.recommendation_service import get_recommendation

def test_recommendations():
    test_cases = [
        "Tomato mosaic virus",
        "Bacterial spot",
        "Tomato healthy",
        "Unknown Disease"
    ]
    
    for case in test_cases:
        print(f"\nTesting: {case}")
        result = get_recommendation(case)
        if result:
            print(f"Found: {result['disease_name']}")
            print(f"Severity: {result['severity']}")
        else:
            print("No recommendation found.")

if __name__ == "__main__":
    test_recommendations()
