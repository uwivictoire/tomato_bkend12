class PrivateNetworkAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # This header is required by Google Chrome for Private Network Access (PNA)
        # It allows a public website to access this local server
        response["Access-Control-Allow-Private-Network"] = "true"
        return response
