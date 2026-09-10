"""
Views for assessment creation and historical review.
Conforming to API_SPECIFICATION.md.
"""

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent
from apps.students.services import get_or_create_student_profile
from .selectors import list_assessments_for_student
from .serializers import AssessmentCreateSerializer, AssessmentDetailSerializer
from .services import record_assessment


class AssessmentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class AssessmentListCreateView(APIView):
    """
    POST /assessments/ - Save a submitted assessment observation.
    GET /assessments/  - Paginated own assessment history.
    Student only access.
    """

    permission_classes = [IsStudent]
    pagination_class = AssessmentPagination

    def post(self, request, *args, **kwargs):
        profile = get_or_create_student_profile(request.user)
        serializer = AssessmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assessment = record_assessment(
            student=profile,
            assessment_type=serializer.validated_data["type"],
            scores_data=serializer.validated_data["scores"],
            actor=request.user,
        )

        output_serializer = AssessmentDetailSerializer(assessment)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        profile = get_or_create_student_profile(request.user)
        assessments = list_assessments_for_student(profile)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(assessments, request, view=self)
        if page is not None:
            serializer = AssessmentDetailSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AssessmentDetailSerializer(assessments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
