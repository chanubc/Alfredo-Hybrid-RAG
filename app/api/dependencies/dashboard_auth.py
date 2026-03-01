from fastapi import Header, HTTPException, Query

from app.core.jwt import verify_dashboard_token


async def get_dashboard_telegram_id(
    authorization: str = Header(..., alias="Authorization"),
) -> int:
    """Authorization: Bearer {JWT} 헤더 기반 인증 (대시보드 API용)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.removeprefix("Bearer ")
    telegram_id = verify_dashboard_token(token)
    if telegram_id is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired dashboard token"
        )
    return telegram_id


async def get_dashboard_telegram_id_from_query(
    token: str = Query(..., description="Dashboard JWT"),
) -> int:
    """?token={JWT} 쿼리 파라미터 기반 인증 (리다이렉트 URL용)."""
    telegram_id = verify_dashboard_token(token)
    if telegram_id is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired dashboard token"
        )
    return telegram_id
