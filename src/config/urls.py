from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

def home(_request):
    return redirect("/admin/")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sessions/", include("quiz_sessions.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("quizzes.urls")),
    path("", home),
]
