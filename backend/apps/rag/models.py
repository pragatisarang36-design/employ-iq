import uuid
from django.conf import settings
from django.db import models


class KnowledgeDocument(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    role = models.ForeignKey("careers.CareerRole", on_delete=models.SET_NULL, null=True, blank=True, related_name="knowledge_documents")
    topic = models.CharField(max_length=100)
    content = models.TextField()
    source_type = models.CharField(max_length=50, default="curated")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    version = models.CharField(max_length=30, default="v1")
    checksum = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_documents"
        ordering = ["title"]


class CopilotConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="copilot_conversations")
    role = models.ForeignKey("careers.CareerRole", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "copilot_conversations"
        ordering = ["-created_at"]


class CopilotMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(CopilotConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    citation_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "copilot_messages"
        ordering = ["created_at"]
