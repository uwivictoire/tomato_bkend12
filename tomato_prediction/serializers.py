from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Farmer, Device, TomatoScan

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class FarmerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    farmernames = serializers.CharField(source='farmer_names', read_only=True)
    class Meta:
        model = Farmer
        fields = ['id', 'user', 'farmernames', 'location', 'role']

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'device_location', 'field_size', 'created_at']

class TomatoScanSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    location = serializers.CharField(source='device.farmer.location', read_only=True)
    farmernames = serializers.CharField(source='device.farmer.farmer_names', read_only=True)

    class Meta:
        model = TomatoScan
        fields = ['id', 'prediction', 'confidence', 'image', 'device_id', 'location', 'farmernames', 'created_at']

class CustomTokenObtainPairSerializer(serializers.Serializer):
    # The user now wants "email" and "password" for login
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        from rest_framework_simplejwt.tokens import RefreshToken

        email = attrs.get('email')
        password = attrs.get('password')

        # Try to find the user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            username = email

        user = authenticate(username=username, password=password)

        if user:
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            
            refresh = RefreshToken.for_user(user)
            
            try:
                farmer = user.farmer
                farmer_id = farmer.id
                farmernames = farmer.farmer_names # Use original names
                role = farmer.role
                # Get the device ID if they have one (first one)
                device = farmer.devices.first()
                device_id = device.device_id if device else None
            except:
                farmer_id = None
                farmernames = user.username
                role = None
                device_id = None

            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'farmer_id': farmer_id,
                'farmernames': farmernames, # Renamed to farmernames
                'role': role,
                'device_id': device_id,
                'email': user.email
            }

        raise serializers.ValidationError("Invalid credentials")
