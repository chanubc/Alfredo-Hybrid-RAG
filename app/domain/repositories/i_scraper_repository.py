from abc import ABC, abstractmethod


class IScraperRepository(ABC):
    """웹 스크래핑 인터페이스."""

    @abstractmethod
    async def scrape(self, url: str) -> str:
        """URL에서 콘텐츠 추출."""
        pass
