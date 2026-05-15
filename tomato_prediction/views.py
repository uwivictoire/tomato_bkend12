import os
import io
import numpy as np
import tensorflow as tf
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Make sure these models exist in tomato_prediction/models.py
from tomato_prediction.models import Farmer, Device, TomatoScan
from .serializers import TomatoScanSerializer, TomatoScanSummarySerializer, FarmerSerializer, DeviceSerializer

# Import Recommendation and Email services
from recommandation.recommendation_service import get_recommendation
from recommandation.email_service import send_disease_report

# Load the model once
MODEL_PATH = os.path.join(settings.BASE_DIR, 'train_model', 'tomato_model.keras')
model = None

try:
    print(f"--- [SYSTEM] Loading AI Model from: {MODEL_PATH} ---")
    if os.path.exists(MODEL_PATH):
        model = tf.keras.models.load_model(MODEL_PATH)
        print("--- [SYSTEM] AI Model Loaded Successfully ---")
    else:
        print(f"--- [WARNING] AI Model file not found at {MODEL_PATH}. Prediction will fail until a model is trained. ---")
except Exception as e:
    print(f"--- [ERROR] Failed to load AI Model: {str(e)} ---")

# IMPORTANT: This list MUST match the exact order detected by TensorFlow (alphabetical by folder name).
# Detected by trainer.py: ['Bacterial spot', 'Early blight', 'Late blight', 'Leaf Mold',
# 'Septoria leaf spot', 'Spider mites Two-spotted spider mite', 'Target Spot',
# 'This picture does not have relationship with Tomato', 'Tomato Yellow Leaf Curl Virus',
# 'Tomato healthy', 'Tomato mosaic virus']
CLASS_NAMES = [
  "Bacterial Spot",          # 0 (Bacterial spot)
  "Early Blight",            # 1 (Early blight)
  "Late Blight",             # 2 (Late blight)
  "Leaf Mold",               # 3 (Leaf Mold)
  "Septoria Leaf Spot",      # 4 (Septoria leaf spot)
  "Spider Mites",            # 5 (Spider mites Two-spotted spider mite)
  "Target Spot",             # 6 (Target Spot)
  "Non-Tomato Image",        # 7 (This picture does not have relationship with Tomato)
  "Yellow Leaf Curl Virus",  # 8 (Tomato Yellow Leaf Curl Virus)
  "Healthy",                 # 9 (Tomato healthy)
  "Mosaic Virus",            # 10 (Tomato mosaic virus)
]

def safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        # Extract numeric part (e.g., '12h' -> 12.0)
        match = re.search(r"[-+]?\d*\.?\d+", str(value))
        if match:
            return float(match.group())
        return None

@method_decorator(csrf_exempt, name='dispatch')
class TomatoPredictionView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        device_id = request.data.get('device_id')
        humidity = request.data.get('humidity')
        temperature = request.data.get('temperature')

        if not image_file or not device_id:
            print(f"[AI] Missing data: image={bool(image_file)}, device_id={device_id}")
            return Response({"error": "Missing image or device_id"}, status=400)

        print(f"[AI] New prediction request for Device: {device_id}")

        try:
            # 1. Find the Device record
            device = Device.objects.get(device_id=device_id)

            # 2. AI PREDICTION 
            image_file.seek(0)
            img = tf.keras.preprocessing.image.load_img(io.BytesIO(image_file.read()), target_size=(224, 224))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0) 

            predictions = model.predict(img_array)
            prediction_label = CLASS_NAMES[np.argmax(predictions[0])]
            confidence = float(np.max(predictions[0])) * 100
            
            if confidence < 20.0:
                prediction_label = "Non-Tomato Image"
            
                
            print(f"[AI] Prediction complete: {prediction_label} ({confidence:.2f}%)")

            # 3. SAVE TO POSTGRES & CLOUDINARY
            image_file.seek(0)
            scan = TomatoScan.objects.create(
                device=device, # Linked to Device now
                image=image_file, 
                prediction=prediction_label,
                confidence=round(confidence, 2),
                humidity=safe_float(humidity),
                temperature=safe_float(temperature)
            )
            print(f"[AI] Scan saved. URL: {scan.image.url}")

            # 4. FETCH RECOMMENDATION
            recommendation = get_recommendation(prediction_label) or {}
            
            # 5. SEND EMAIL TO FARMER
            try:
                farmer = device.farmer
                farmer_email = farmer.user.email
                farmer_name = farmer.farmer_names or farmer.user.username
                
                prediction_data = {
                    "prediction": prediction_label,
                    "confidence": f"{confidence:.2f}%",
                    "image_url": scan.image.url
                }
                
                # Send email (Sync for now, consider async/celery in production)
                send_disease_report(farmer_email, farmer_name, prediction_data, recommendation)
            except Exception as email_err:
                print(f"[WARNING] Email failed but scan saved: {str(email_err)}")

            return Response({
                "status": "success",
                "prediction": prediction_label,
                "confidence": f"{confidence:.2f}%",
                "image_url": request.build_absolute_uri(scan.image.url),
                "humidity": scan.humidity,
                "temperature": scan.temperature,
                "timestamp": scan.created_at,
                "recommendation": recommendation # Added recommendation to response
            }, status=201)

        except Device.DoesNotExist:
            return Response({"error": "Device ID not registered. Please register the device first."}, status=404)
        except Exception as e:
            print(f"AI Error: {str(e)}")
            return Response({"error": f"Internal Error: {str(e)}"}, status=500)

class PredictionHistoryView(APIView):
    def get(self, request, device_id):
        try:
            device = Device.objects.get(device_id=device_id)
            scans = TomatoScan.objects.filter(device=device)
            serializer = TomatoScanSerializer(scans, many=True)
            return Response(serializer.data)
        except Device.DoesNotExist:
            return Response({"error": "Device ID not found"}, status=404)

class LatestPredictionView(APIView):
    def get(self, request, device_id):
        try:
            device = Device.objects.get(device_id=device_id)
            latest_scan = TomatoScan.objects.filter(device=device).order_by('-created_at').first()
            if not latest_scan:
                return Response({"error": "No predictions found for this device"}, status=404)
            serializer = TomatoScanSerializer(latest_scan)
            return Response(serializer.data)
        except Device.DoesNotExist:
            return Response({"error": "Device ID not found"}, status=404)

class FarmerListView(APIView):
    def get(self, request):
        farmers = Farmer.objects.all()
        serializer = FarmerSerializer(farmers, many=True)
        return Response(serializer.data)

class AllPredictionsListView(APIView):
    def get(self, request):
        # Optimization: Limit to most recent 100 scans for dashboard performance
        # Use select_related for foreign keys and use Summary Serializer
        scans = TomatoScan.objects.select_related('device', 'device__farmer').all().order_by('-created_at')[:100]
        serializer = TomatoScanSummarySerializer(scans, many=True)
        return Response(serializer.data)

class DeviceListView(APIView):
    def get(self, request):
        devices = Device.objects.all()
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)

class UserPredictionHistoryView(APIView):
    def get(self, request, user_id):
        try:
            farmer = Farmer.objects.get(user_id=user_id)
            devices = Device.objects.filter(farmer=farmer)
            # Optimization: Limit to most recent 50 scans for dashboard and use Summary Serializer
            scans = TomatoScan.objects.filter(device__in=devices).select_related('device').order_by('-created_at')[:50]
            serializer = TomatoScanSummarySerializer(scans, many=True)
            return Response(serializer.data)
        except Farmer.DoesNotExist:
            return Response({"error": "User/Farmer not found"}, status=404)

class UserDeviceListView(APIView):
    def get(self, request, user_id):
        try:
            farmer = Farmer.objects.get(user_id=user_id)
            devices = Device.objects.filter(farmer=farmer)
            serializer = DeviceSerializer(devices, many=True)
            return Response(serializer.data)
        except Farmer.DoesNotExist:
            return Response({"error": "User/Farmer not found"}, status=404)

class FarmerDetailView(APIView):
    def get(self, request, pk):
        try:
            farmer = Farmer.objects.get(pk=pk)
            serializer = FarmerSerializer(farmer)
            return Response(serializer.data)
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=404)

    def put(self, request, pk):
        try:
            farmer = Farmer.objects.get(pk=pk)
            user = farmer.user
            if 'email' in request.data:
                user.email = request.data['email']
                user.username = request.data['email']
                user.save()
            
            serializer = FarmerSerializer(farmer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=404)

    def delete(self, request, pk):
        try:
            farmer = Farmer.objects.get(pk=pk)
            farmer.user.delete()
            return Response({"message": "Farmer deleted successfully"}, status=204)
        except Farmer.DoesNotExist:
            return Response({"error": "Farmer not found"}, status=404)

class DeviceDetailView(APIView):
    def get(self, request, pk):
        try:
            device = Device.objects.get(pk=pk)
            serializer = DeviceSerializer(device)
            return Response(serializer.data)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=404)

    def put(self, request, pk):
        try:
            device = Device.objects.get(pk=pk)
            serializer = DeviceSerializer(device, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=404)

    def delete(self, request, pk):
        try:
            device = Device.objects.get(pk=pk)
            device.delete()
            return Response({"message": "Device deleted successfully"}, status=204)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=404)

class ScanDetailView(APIView):
    def get(self, request, pk):
        try:
            scan = TomatoScan.objects.get(pk=pk)
            # Use full serializer to include recommendation
            serializer = TomatoScanSerializer(scan)
            return Response(serializer.data)
        except TomatoScan.DoesNotExist:
            return Response({"error": "Scan record not found"}, status=404)

    def delete(self, request, pk):
        try:
            scan = TomatoScan.objects.get(pk=pk)
            scan.delete()
            return Response({"message": "Scan record deleted successfully"}, status=204)
        except TomatoScan.DoesNotExist:
            return Response({"error": "Scan record not found"}, status=404)