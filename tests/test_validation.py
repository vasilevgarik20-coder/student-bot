import pytest

def test_valid_user_id():
    try:
        user_id = int("123456789")
        assert isinstance(user_id, int)
        assert user_id > 0
    except ValueError:
        pytest.fail("Ошибка преобразования корректного ID")

def test_invalid_user_id():
    with pytest.raises(ValueError):
        user_id = int("abc123")
