"""Port → Adapter 매핑 (Infrastructure 구현체 생성)."""

from fastapi import Depends

from app.application.ports.agent_port import AgentPort
from app.application.ports.intent_classifier_port import IntentClassifierPort
from app.infrastructure.adapters.knowledge_agent_adapter import KnowledgeAgentAdapter
from app.infrastructure.adapters.openai_intent_classifier import OpenAIIntentClassifier
from app.application.agents.knowledge_agent import KnowledgeAgent
from app.domain.repositories.i_telegram_repository import ITelegramRepository
from app.api.dependencies.auth_di import get_telegram_client
from app.api.dependencies.agent_di import get_knowledge_agent


def get_intent_classifier() -> IntentClassifierPort:
    """Port 반환: IntentClassifierPort 구현체는 OpenAI."""
    return OpenAIIntentClassifier()


def get_agent(
    knowledge_agent: KnowledgeAgent = Depends(get_knowledge_agent),
    telegram: ITelegramRepository = Depends(get_telegram_client),
) -> AgentPort:
    """Port 반환: AgentPort 구현체는 KnowledgeAgentAdapter."""
    return KnowledgeAgentAdapter(knowledge_agent, telegram)
