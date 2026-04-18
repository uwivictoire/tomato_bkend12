from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Farmer

class RegisterFarmerView(APIView):
    def post(self, request):
        # 1. Get all fields from the request
        email = request.data.get('email')
        farmer_names = request.data.get('farmernames')
        password = request.data.get('password')
        location = request.data.get('location')
        user_role = request.data.get('userrole', 'farmer') # Default to farmer if not provided

        # Simple Validation
        if not all([farmer_names, password, location]):
            return Response({"error": "Missing required fields (farmernames, password, location)"}, status=400)

        try:
            # 2. Create the Auth User
            username = email if email and email.strip() else farmer_names.replace(" ", "").lower()
            
            if User.objects.filter(username=username).exists():
                return Response({"error": "User already exists"}, status=400)

            # Map 'admin' role to staff status if desired, here we just save it in profile
            is_staff = True if user_role == 'admin' else False
            
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password,
                is_staff=is_staff
            )

            # 3. Create the Farmer profile linked to that User
            farmer = Farmer.objects.create(
                user=user,
                farmer_names=farmer_names, # Save original names
                location=location,
                role=user_role
            )

            return Response({
                "status": "success",
                "message": f"{user_role.capitalize()} registration successful",
                "farmer_id": farmer.id,
                "farmernames": farmer.farmer_names,
                "role": farmer.role,
                "username": username
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=400)