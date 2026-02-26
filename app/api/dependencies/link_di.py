from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_di import (
    get_notion_client,
    get_telegram_client,
    get_user_repository,
)
from app.application.usecases.save_link_usecase import SaveLinkUseCase
from app.application.usecases.save_memo_usecase import SaveMemoUseCase
from app.domain.repositories.i_notion_repository import INotionRepository
from app.domain.repositories.i_openai_repository import IOpenAIRepository
from app.domain.repositories.i_scraper_repository import IScraperRepository
from app.domain.repositories.i_telegram_repository import ITelegramRepository
from app.infrastructure.database import get_db
from app.infrastructure.external.scraper_client import ScraperRepository
from app.infrastructure.llm.openai_client import OpenAIRepository
from app.infrastructure.repository.chunk_repository import ChunkRepository
from app.infrastructure.repository.link_repository import LinkRepository
from app.infrastructure.repository.user_repository import UserRepository


def get_openai_client() -> IOpenAIRepository:
    return OpenAIRepository()


def get_scraper_client() -> IScraperRepository:
    return ScraperRepository()


def get_link_repository(db: AsyncSession = Depends(get_db)) -> LinkRepository:
    return LinkRepository(db)


def get_chunk_repository(db: AsyncSession = Depends(get_db)) -> ChunkRepository:
    return ChunkRepository(db)


def get_save_link_usecase(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    link_repo: LinkRepository = Depends(get_link_repository),
    chunk_repo: ChunkRepository = Depends(get_chunk_repository),
    openai: IOpenAIRepository = Depends(get_openai_client),
    scraper: IScraperRepository = Depends(get_scraper_client),
    telegram: ITelegramRepository = Depends(get_telegram_client),
    notion: INotionRepository = Depends(get_notion_client),
) -> SaveLinkUseCase:
    return SaveLinkUseCase(db, user_repo, link_repo, chunk_repo, openai, scraper, telegram, notion)


def get_save_memo_usecase(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    link_repo: LinkRepository = Depends(get_link_repository),
    chunk_repo: ChunkRepository = Depends(get_chunk_repository),
    openai: IOpenAIRepository = Depends(get_openai_client),
    telegram: ITelegramRepository = Depends(get_telegram_client),
    notion: INotionRepository = Depends(get_notion_client),
) -> SaveMemoUseCase:
    return SaveMemoUseCase(db, user_repo, link_repo, chunk_repo, openai, telegram, notion)
