from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from tomato_prediction.views import (
    TomatoPredictionView, 
    PredictionHistoryView, 
    LatestPredictionView,
    FarmerListView,
    AllPredictionsListView,
    UserPredictionHistoryView,
    DeviceListView,
    UserDeviceListView,
    FarmerDetailView,
    DeviceDetailView,
    ScanDetailView,
    DroidCamProxyView
)
from tomato_prediction.registerfarmer import RegisterFarmerView
from tomato_prediction.registerdevice import DeviceRegistrationView
from tomato_prediction.login import LoginView
from tomato_prediction.update_password import UpdatePasswordView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth & Registration Endpoints
    path('farmer/register/', RegisterFarmerView.as_view(), name='register-farmer'),
    path('device/register/', DeviceRegistrationView.as_view(), name='register-device'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/update-password/', UpdatePasswordView.as_view(), name='update_password'),
    # Farmer & Administrative Endpoints
    path('farmers/', FarmerListView.as_view(), name='farmer-list'),
    path('farmers/<int:pk>/', FarmerDetailView.as_view(), name='farmer-detail'),
    path('devices/user/<int:user_id>/', UserDeviceListView.as_view(), name='user-device-list'),
    path('devices/', DeviceListView.as_view(), name='device-list'),
    path('devices/<int:pk>/', DeviceDetailView.as_view(), name='device-detail'),
    # AI Prediction Endpoints
    path('ai/analyze/', TomatoPredictionView.as_view(), name='tomato-analyze'),
    path('ai/history/<str:device_id>/', PredictionHistoryView.as_view(), name='prediction-history'),
    path('ai/latest/<str:device_id>/', LatestPredictionView.as_view(), name='latest-prediction'),
    path('ai/all-predictions/', AllPredictionsListView.as_view(), name='all-predictions-list'),
    path('ai/history/user/<int:user_id>/', UserPredictionHistoryView.as_view(), name='user-prediction-history'),
    path('ai/scan/<int:pk>/', ScanDetailView.as_view(), name='scan-detail'),
    path('ai/droidcam-snapshot/', DroidCamProxyView.as_view(), name='droidcam-snapshot'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
