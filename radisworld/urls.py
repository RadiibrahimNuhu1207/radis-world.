from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from world import views

urlpatterns = [
    path("", views.home, name="home"),
    path("history/<slug:slug>/", views.share_history, name="share_history"),
    path("watch/<str:vid>/", views.share_video, name="share_video"),
    path("book/<slug:slug>/", views.share_book, name="share_book"),
    path("comic/<slug:slug>/", views.share_comic, name="share_comic"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("robots.txt", views.robots, name="robots"),
    path("api/data/", views.api_data, name="api_data"),
    path("api/subscribe/", views.api_subscribe, name="api_subscribe"),
    path("api/unsubscribe/", views.api_unsubscribe, name="api_unsubscribe"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="sw"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
