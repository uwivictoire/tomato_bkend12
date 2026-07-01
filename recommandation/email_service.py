import resend
import os
from django.conf import settings

# Initialize Resend with the API Key
resend.api_key = os.getenv("RESEND_API_KEY")

def send_disease_report(to_email, farmer_name, prediction_data, recommendation):
    """
    Sends a detailed disease report to the farmer.
    """
    from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    
    disease = prediction_data.get('prediction')
    confidence = prediction_data.get('confidence')
    image_url = prediction_data.get('image_url')
    
    # Recommendation details
    treatment = recommendation.get('treatment', 'N/A')
    prevention = recommendation.get('prevention', 'N/A')
    severity = recommendation.get('severity', 'N/A')
    alert = recommendation.get('alert_message', 'N/A')

    html_content = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
        <h2 style="color: #2e7d32;">Tomato Disease Analysis Report</h2>
        <p>Hello <strong>{farmer_name}</strong>,</p>
        <p>Our AI system has analyzed the image uploaded from your device. Here are the results:</p>
        
        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p><strong>Detected Condition:</strong> <span style="color: #d32f2f; font-size: 1.2em;">{disease}</span></p>
            <p><strong>Confidence:</strong> {confidence}</p>
            <p><strong>Severity Level:</strong> {severity}</p>
        </div>

        <img src="{image_url}" alt="Analyzed Leaf" style="width: 100%; border-radius: 5px; margin-bottom: 20px;">

        <h3 style="color: #1976d2;">Recommended Actions</h3>
        <p><strong>Treatment:</strong><br>{treatment}</p>
        <p><strong>Prevention:</strong><br>{prevention}</p>
        
        <div style="background: #fff3e0; border-left: 5px solid #ff9800; padding: 10px; margin-top: 20px;">
            <p><strong>System Alert:</strong> {alert}</p>
        </div>

        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 0.8em; color: #777;">This is an automated report from the Tomato AI Monitoring System. Please consult with an agronomist for critical decisions.</p>
    </div>
    """

    try:
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": f"Alert: {disease} Detected in Your Field",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"[SYSTEM] Email sent successfully to {to_email}. ID: {email['id']}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {str(e)}")
        return False
