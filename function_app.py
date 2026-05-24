import azure.functions as func
from backend.main import fastapi_app as fastapi_app

# Azure Functions V2 programming model wraps ASGI applications natively
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
