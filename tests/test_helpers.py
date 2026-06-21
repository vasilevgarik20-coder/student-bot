import pytest
from bot import delete_previous, last_msg

@pytest.mark.asyncio
async def test_delete_previous(mocker):
    mock_delete = mocker.patch("bot.bot.delete_message", return_value=None)
    user_id = 123
    chat_id = 456
    last_msg[user_id] = 789
    await delete_previous(user_id, chat_id)
    mock_delete.assert_called_once_with(chat_id, 789)
    assert user_id not in last_msg

@pytest.mark.asyncio
async def test_delete_previous_no_message(mocker):
    mock_delete = mocker.patch("bot.bot.delete_message", return_value=None)
    user_id = 123
    chat_id = 456
    await delete_previous(user_id, chat_id)
    mock_delete.assert_not_called()
    assert user_id not in last_msg
