from cloudinary.models import CloudinaryField
from django.db import models
from django.contrib.auth.models import User

class Farmer(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('farmer', 'Farmer'),
    ]

    # Links to the User account for login
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer')
    
    # Store the original names from registration
    farmer_names = models.CharField(max_length=255, null=True, blank=True)
    
    location = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='farmer')
    
    # device_id removed from here and moved to separate Device model

    def __str__(self):
        return f"{self.farmer_names} ({self.role}) | Location: {self.location}"

class Device(models.Model):
    # A Farmer can have multiple devices
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=100, unique=True)
    
    # New Fields for device-specific data
    device_location = models.CharField(max_length=255, null=True, blank=True)
    field_size = models.CharField(max_length=100, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Device: {self.device_id} (Owner: {self.farmer.farmer_names})"

class TomatoScan(models.Model):
    # Links this scan to the specific device
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='scans', null=True, blank=True)
    
    # Stored on Cloudinary via django-cloudinary-storage
    image = models.ImageField(upload_to='scans/') 
    
    prediction = models.CharField(max_length=100)
    confidence = models.FloatField()
    
    # NEW: Environmental data from ESP32/User
    humidity = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    
    # THE TIME STAMP: Recorded automatically when the photo is uploaded
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Newest scans appear first

    def __str__(self):
        return f"{self.prediction} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class PredictionResult(models.Model):
    result = models.IntegerField()
    image_url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction {self.result} at {self.timestamp}"