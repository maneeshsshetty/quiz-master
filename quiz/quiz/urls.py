"""quiz URL Configuration

The global URL configuration. 
This list serves as the highest-level traffic director.
Every single request comes here first.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # The Administrative Interface.
    # Django provides a fully-functional CRUD interface for all models "out of the box".
    # Access it at /admin/.
    path('admin/', admin.site.urls),
    
    # Delegating to Apps.
    # Instead of writing all 100+ URLs here, we use 'include()'.
    # This tells Django: "If the URL matches the empty string (basically everything not matched above),
    # chop off that part (nothing) and send the rest of the URL string to 'quiz_master.urls' for further processing."
    # This keeps our project modular. Each app handles its own URLs.
    path('', include('quiz_master.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
