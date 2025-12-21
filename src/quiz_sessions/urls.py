from django.urls import path
from . import views

urlpatterns = [
    path("create/<int:quiz_id>/", views.create_session, name="create_session"),
    path("host/<str:code>/", views.host_session, name="host_session"),
    path("host/<str:code>/qr.png", views.session_qr_png, name="session_qr_png"),
    path("host/<str:code>/results/", views.host_results, name="host_results"),
    path("host/<str:code>/stats/", views.host_stats, name="host_stats"),
    path("join/<str:code>/", views.join_session, name="join_session"),
    path("play/<str:code>/", views.play_session, name="play_session"),
    path("state/<str:code>/", views.session_state, name="session_state"),
    path("answer/<str:code>/", views.submit_answer, name="submit_answer"),
    path("final/<str:code>/", views.final_session, name="final_session"),
    path("quiz/<int:quiz_id>/", views.quiz_sessions_list, name="quiz_sessions_list"),

]
