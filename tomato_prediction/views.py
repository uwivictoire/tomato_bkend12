import os
import io
import numpy as np
import tensorflow as tf
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Make sure these models exist in tomato_prediction/models.py
from tomato_prediction.models import Farmer, Device, TomatoScan
from .serializers import TomatoScanSerializer, FarmerSerializer

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

CLASS_NAMES = [
  "Bacterial spot",
  "Early blight",
  "Late blight",
  "Leaf Mold",
  "Septoria leaf spot",
  "Spider mites Two-spotted spider mite",
  "Target Spot",
  "Tomato healthy",
  "Tomato mosaic virus",
  "Tomato Yellow Leaf Curl Virus"
]

@method_decorator(csrf_exempt, name='dispatch')
class TomatoPredictionView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        device_id = request.data.get('device_id')

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
            print(f"[AI] Prediction complete: {prediction_label} ({confidence:.2f}%)")

            # 3. SAVE TO POSTGRES & CLOUDINARY
            image_file.seek(0)
            scan = TomatoScan.objects.create(
                device=device, # Linked to Device now
                image=image_file, 
                prediction=prediction_label,
                confidence=round(confidence, 2)
            )
            print(f"[AI] Scan saved. URL: {scan.image.url}")

            return Response({
                "status": "success",
                "prediction": prediction_label,
                "confidence": f"{confidence:.2f}%",
                "image_url": scan.image.url,
                "timestamp": scan.created_at
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
        scans = TomatoScan.objects.all()
        serializer = TomatoScanSerializer(scans, many=True)
        return Response(serializer.data)