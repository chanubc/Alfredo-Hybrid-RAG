from fastapi import Depends

from app.api.dependencies.link_di import get_chunk_repository, get_openai_client
from app.application.usecases.search_usecase import SearchUseCase
from app.domain.repositories.i_openai_repository import IOpenAIRepository
from app.infrastructure.repository.chunk_repository import ChunkRepository
from app.rag.reranker import SimpleReranker
from app.rag.retriever import HybridRetriever


def get_retriever(
    openai: IOpenAIRepository = Depends(get_openai_client),
    chunk_repo: ChunkRepository = Depends(get_chunk_repository),
) -> HybridRetriever:
    return HybridRetriever(openai, chunk_repo)


def get_reranker() -> SimpleReranker:
    return SimpleReranker()


def get_search_usecase(
    retriever: HybridRetriever = Depends(get_retriever),
    reranker: SimpleReranker = Depends(get_reranker),
) -> SearchUseCase:
    return SearchUseCase(retriever, reranker)
