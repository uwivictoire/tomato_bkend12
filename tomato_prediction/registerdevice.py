from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Farmer, Device

class DeviceRegistrationView(APIView):
    def post(self, request):
        email = request.data.get('email')
        device_id = request.data.get('device_id')
        device_location = request.data.get('device_location')
        field_size = request.data.get('field_size')

        if not email or not device_id:
            return Response({"error": "Missing required fields: email and device_id"}, status=400)

        # Check for duplicate registration
        if Device.objects.filter(device_id=device_id).exists():
            return Response({"error": "This device is already registered in the system."}, status=400)

        try:
            # 1. Find User by Email
            user = User.objects.get(email=email)
            
            # 2. Get Farmer profile
            try:
                farmer = user.farmer
            except Farmer.DoesNotExist:
                return Response({"error": "Farmer profile not found for this user"}, status=404)

            # 3. Create Device
            device = Device.objects.create(
                device_id=device_id,
                farmer=farmer,
                device_location=device_location,
                field_size=field_size
            )

            return Response({
                "status": "success",
                "message": "Device registered and linked successfully",
                "device_id": device_id,
                "farmer_email": email,
                "device_location": device.device_location,
                "field_size": device.field_size
            }, status=201)

        except User.DoesNotExist:
            return Response({"error": f"User with email {email} not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
