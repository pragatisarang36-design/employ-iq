from django.urls import path
from .views import CopilotAskView, CopilotConversationListView

urlpatterns = [path("copilot/ask/", CopilotAskView.as_view(), name="copilot-ask"), path("copilot/conversations/", CopilotConversationListView.as_view(), name="copilot-conversations")]
