"""
URL configuration for sanfelipe project.

San Felipe Government Backoffice URL routing.
Microservice architecture with Django Admin for backoffice UI.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static


def health_check(request: HttpResponse) -> HttpResponse:
    """Health check endpoint for monitoring."""
    return HttpResponse("OK", status=200)


def home(request: HttpResponse) -> HttpResponse:
    """Home page - redirect to admin."""
    return HttpResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backoffice San Felipe</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    color: white;
                    max-width: 600px;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                }
                h1 {
                    margin-bottom: 20px;
                    font-size: 2.5em;
                }
                p {
                    margin-bottom: 30px;
                    font-size: 1.1em;
                }
                .btn {
                    display: inline-block;
                    padding: 15px 40px;
                    background: white;
                    color: #667eea;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    transition: all 0.3s;
                }
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 20px rgba(0,0,0,0.2);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Backoffice San Felipe</h1>
                <p>Sistema de Gestión de Trámites</p>
                <a href="/admin/" class="btn">Ingresar al Sistema</a>
            </div>
        </body>
        </html>
        """,
        status=200,
    )


urlpatterns = [
    # Home page
    path("", home, name="home"),
    # Health check
    path("health/", health_check, name="health-check"),
    # Django Admin
    path("admin/", admin.site.urls),
    # Future APIs can be added here
    # path('api/reportes/', include('reportes.urls')),
]

# Static files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
