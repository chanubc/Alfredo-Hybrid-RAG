import uuid
from datetime import datetime, timedelta, timezone


class ShortLinkStore:
    """간단한 인메모리 단기 링크 저장소.

    JWT 토큰이 텔레그램 채팅방이나 링크 열기 모달에 그대로 노출되는 것을 막기 위해,
    짧은 임시 ID를 발급하고 이 ID로 접속 시 실제 토큰이 포함된 대시보드 URL로 리다이렉트합니다.
    (주의: 단일 워커 환경에 적합한 인메모리 방식)
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, datetime]] = {}

    def create(self, token: str) -> str:
        self._cleanup()
        link_id = uuid.uuid4().hex[:8]
        # 링크 자체는 텔레그램에서 클릭하기 위해 10분간만 유효 (실제 JWT 토큰 만료와 별개)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        self._store[link_id] = (token, expires_at)
        return link_id

    def consume(self, link_id: str) -> str | None:
        self._cleanup()
        if link_id in self._store:
            token, _ = self._store.pop(link_id)
            return token
        return None

    def _cleanup(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [k for k, v in self._store.items() if v[1] < now]
        for k in expired:
            self._store.pop(k, None)


# 싱글톤 인스턴스
short_link_store = ShortLinkStore()
