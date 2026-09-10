from django.urls import path

from .views import LatestPredictionView, PredictionCreateView, PredictionDetailView

urlpatterns = [
    path("predictions/", PredictionCreateView.as_view(), name="prediction-create"),
    path("predictions/latest/", LatestPredictionView.as_view(), name="prediction-latest"),
    path("predictions/<uuid:prediction_id>/", PredictionDetailView.as_view(), name="prediction-detail"),
]
