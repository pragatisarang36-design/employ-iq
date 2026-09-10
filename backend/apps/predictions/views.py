from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent
from apps.students.services import get_or_create_student_profile
from ml.inference import ModelUnavailableError

from .selectors import get_latest_prediction, get_prediction_for_student
from .serializers import PredictionSerializer
from .services import create_prediction


class PredictionCreateView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        try:
            prediction = create_prediction(student=get_or_create_student_profile(request.user), actor=request.user)
        except (ModelUnavailableError, ValueError) as exc:
            return Response({"code": "model_unavailable", "message": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(PredictionSerializer(prediction).data, status=status.HTTP_201_CREATED)


class LatestPredictionView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        prediction = get_latest_prediction(get_or_create_student_profile(request.user))
        if not prediction:
            return Response({"code": "not_found", "message": "No prediction is available yet."}, status=status.HTTP_404_NOT_FOUND)
        return Response(PredictionSerializer(prediction).data)


class PredictionDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, prediction_id):
        prediction = get_prediction_for_student(prediction_id, get_or_create_student_profile(request.user))
        if not prediction:
            return Response({"code": "not_found", "message": "Prediction not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(PredictionSerializer(prediction).data)
