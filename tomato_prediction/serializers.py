from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Farmer, Device, TomatoScan

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class FarmerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    farmer_names = serializers.CharField(required=False)
    farmernames = serializers.CharField(source='farmer_names', read_only=True)
    class Meta:
        model = Farmer
        fields = ['id', 'user', 'farmer_names', 'farmernames', 'location', 'role']

class DeviceSerializer(serializers.ModelSerializer):
    farmer_names = serializers.CharField(source='farmer.farmer_names', read_only=True)
    farmer_id = serializers.IntegerField(source='farmer.id', read_only=True)
    
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'device_location', 'field_size', 'farmer_names', 'farmer_id', 'created_at']

class TomatoScanSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    location = serializers.CharField(source='device.farmer.location', read_only=True)
    farmernames = serializers.CharField(source='device.farmer.farmer_names', read_only=True)
    recommendation = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TomatoScan
        fields = ['id', 'prediction', 'confidence', 'image', 'image_url', 'humidity', 'temperature', 'device_id', 'location', 'farmernames', 'recommendation', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            # Fallback if request is not in context
            return f"http://127.0.0.1:8000{obj.image.url}"
        return None

    def get_recommendation(self, obj):
        from recommandation.recommendation_service import get_recommendation
        return get_recommendation(obj.prediction)

class TomatoScanSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight version for dashboard lists and charts.
    Excludes recommendation to save processing time.
    """
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    farmernames = serializers.CharField(source='device.farmer.farmer_names', read_only=True)
    image_url = serializers.SerializerMethodField()
    recommendation = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = TomatoScan
        fields = ['id', 'prediction', 'confidence', 'image_url', 'humidity', 'temperature', 'device_id', 'farmernames', 'recommendation', 'timestamp', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return f"http://127.0.0.1:8000{obj.image.url}"
        return None

    def get_recommendation(self, obj):
        from recommandation.recommendation_service import get_recommendation
        return get_recommendation(obj.prediction)

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
                'user_id': user.id,
                'farmer_id': farmer_id,
                'farmernames': farmernames, # Renamed to farmernames
                'role': role,
                'device_id': device_id,
                'email': user.email
            }

        raise serializers.ValidationError("Invalid credentials")
