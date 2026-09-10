from django.urls import path
from .views import CurrentRoadmapView, RoadmapCreateView, RoadmapItemUpdateView

urlpatterns = [path("roadmaps/", RoadmapCreateView.as_view(), name="roadmap-create"), path("roadmaps/current/", CurrentRoadmapView.as_view(), name="roadmap-current"), path("roadmaps/<uuid:roadmap_id>/items/<uuid:item_id>/", RoadmapItemUpdateView.as_view(), name="roadmap-item-update")]
