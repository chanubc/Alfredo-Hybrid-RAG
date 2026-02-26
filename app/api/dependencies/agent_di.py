from fastapi import Depends

from app.api.dependencies.auth_di import get_telegram_client
from app.api.dependencies.link_di import get_link_repository
from app.api.dependencies.rag_di import get_reranker, get_retriever
from app.application.services.agent_service import AgentService
from app.domain.repositories.i_telegram_repository import ITelegramRepository
from app.infrastructure.repository.link_repository import LinkRepository
from app.rag.reranker import SimpleReranker
from app.rag.retriever import HybridRetriever


def get_agent_service(
    retriever: HybridRetriever = Depends(get_retriever),
    reranker: SimpleReranker = Depends(get_reranker),
    link_repo: LinkRepository = Depends(get_link_repository),
    telegram: ITelegramRepository = Depends(get_telegram_client),
) -> AgentService:
    return AgentService(retriever, reranker, link_repo, telegram)
