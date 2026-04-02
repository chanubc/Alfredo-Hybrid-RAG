from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.usecases.generate_weekly_report_usecase import GenerateWeeklyReportUseCase


def _make_user(telegram_id: int) -> MagicMock:
    user = MagicMock()
    user.telegram_id = telegram_id
    return user


@pytest.fixture
def catchup_dependencies() -> dict:
    return {
        "db": AsyncMock(),
        "user_repo": AsyncMock(),
        "link_repo": AsyncMock(),
        "rec_repo": AsyncMock(),
        "openai": AsyncMock(),
        "telegram": AsyncMock(),
    }


@pytest.fixture
def catchup_usecase(catchup_dependencies) -> GenerateWeeklyReportUseCase:
    return GenerateWeeklyReportUseCase(**catchup_dependencies)


@pytest.mark.asyncio
async def test_startup_catch_up_sends_only_users_missing_this_weeks_report(
    catchup_usecase,
    catchup_dependencies,
):
    catchup_dependencies["user_repo"].get_all_users.return_value = [
        _make_user(111),
        _make_user(222),
    ]
    catchup_dependencies["rec_repo"].has_recommendation_since.side_effect = [False, True]

    with patch.object(catchup_usecase, "execute", new=AsyncMock()) as mock_execute:
        await catchup_usecase.execute_startup_catch_up(
            now=datetime(2026, 3, 31, 1, 0, tzinfo=timezone.utc)
        )

    catchup_dependencies["rec_repo"].has_recommendation_since.assert_any_await(
        111,
        datetime(2026, 3, 30, 0, 0, tzinfo=timezone.utc),
    )
    mock_execute.assert_awaited_once_with(111)


@pytest.mark.asyncio
async def test_startup_catch_up_skips_before_monday_9am_kst(
    catchup_usecase,
    catchup_dependencies,
):
    with patch.object(catchup_usecase, "execute", new=AsyncMock()) as mock_execute:
        await catchup_usecase.execute_startup_catch_up(
            now=datetime(2026, 3, 29, 23, 59, tzinfo=timezone.utc)
        )

    catchup_dependencies["user_repo"].get_all_users.assert_not_called()
    catchup_dependencies["rec_repo"].has_recommendation_since.assert_not_called()
    mock_execute.assert_not_called()


@pytest.mark.asyncio
async def test_startup_catch_up_rolls_back_and_continues_on_user_failure(
    catchup_usecase,
    catchup_dependencies,
):
    catchup_dependencies["user_repo"].get_all_users.return_value = [
        _make_user(111),
        _make_user(222),
    ]
    catchup_dependencies["rec_repo"].has_recommendation_since.side_effect = [False, False]

    async def _execute_side_effect(user_id: int) -> None:
        if user_id == 111:
            raise RuntimeError("catch-up failure")

    with patch.object(catchup_usecase, "execute", new=AsyncMock(side_effect=_execute_side_effect)) as mock_execute:
        await catchup_usecase.execute_startup_catch_up(
            now=datetime(2026, 3, 31, 1, 0, tzinfo=timezone.utc)
        )

    assert mock_execute.await_count == 2
    catchup_dependencies["db"].rollback.assert_awaited_once()
