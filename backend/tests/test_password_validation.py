import pytest

from app.password_validation import validate_password_strength


def test_valid_password():
    validate_password_strength("Aa1!aaaa")


@pytest.mark.parametrize(
    "pwd",
    [
        "short1!",
        "nouppercase1!",
        "NOLOWERCASE1!",
        "NoDigits!!",
        "NoSpecial123",
    ],
)
def test_invalid_password_raises(pwd: str):
    with pytest.raises(ValueError):
        validate_password_strength(pwd)
