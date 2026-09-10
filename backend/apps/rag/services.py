import hashlib
import re

from django.db import transaction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import CopilotConversation, CopilotMessage, KnowledgeDocument


def _tokens(text):
    return re.findall(r"[a-zA-Z]{2,}", text.lower())


def retrieve(question, role=None, top_k=3):
    docs = KnowledgeDocument.objects.filter(status=KnowledgeDocument.Status.PUBLISHED).filter(role__isnull=True) if role is None else KnowledgeDocument.objects.filter(status=KnowledgeDocument.Status.PUBLISHED).filter(role__isnull=True) | KnowledgeDocument.objects.filter(status=KnowledgeDocument.Status.PUBLISHED, role=role)
    docs = list(docs)
    if not docs:
        return []
    corpus = [doc.title + " " + doc.topic + " " + doc.content for doc in docs]
    matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus + [question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    ranked = sorted(zip(docs, scores), key=lambda row: row[1], reverse=True)
    return [(doc, float(score)) for doc, score in ranked[:top_k] if score >= 0.06]


def grounded_answer(question, sources):
    if not sources:
        return "The curated EmployIQ knowledge base does not yet have enough coverage for that question. Try asking about SQL, Python, React, Django, projects, interviews, or communication preparation."
    excerpts = []
    for document, _ in sources:
        sentences = re.split(r"(?<=[.!?])\s+", document.content.strip())
        query_tokens = set(_tokens(question))
        best = max(sentences, key=lambda sentence: len(query_tokens.intersection(_tokens(sentence))), default=document.content)
        excerpts.append(f"**{document.title}:** {best}")
    return "Based on the curated EmployIQ guidance:\n\n" + "\n\n".join(excerpts) + "\n\nUse these as a focused next step; your readiness score remains separate from this guidance."


@transaction.atomic
def ask_copilot(*, student, question, role=None, conversation_id=None):
    conversation = CopilotConversation.objects.filter(id=conversation_id, student=student).first() if conversation_id else None
    if conversation is None:
        conversation = CopilotConversation.objects.create(student=student, role=role)
    sources = retrieve(question, role=role or conversation.role)
    answer = grounded_answer(question, sources)
    citations = [{"document_id": str(doc.id), "title": doc.title, "section": doc.topic, "relevance": round(score, 3)} for doc, score in sources]
    CopilotMessage.objects.create(conversation=conversation, role=CopilotMessage.Role.USER, content=question)
    CopilotMessage.objects.create(conversation=conversation, role=CopilotMessage.Role.ASSISTANT, content=answer, citation_ids=[item["document_id"] for item in citations])
    return conversation, answer, citations


def recommended_actions(student, role):
    if not role:
        return []
    from apps.careers.services import create_gap_analysis
    gap_snapshot = create_gap_analysis(student=student, role=role)
    return [f"Work on {gap['skill']} ({gap['priority']} priority)." for gap in gap_snapshot.gaps[:3]]


def checksum(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
