from typing import Optional

from sqlalchemy.orm import Session

from app.models.oauth_account import OAuthAccount
from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_oauth(self, provider: str, sub: str) -> Optional[OAuthAccount]:
        return (
            self.db.query(OAuthAccount)
            .filter(OAuthAccount.provider == provider, OAuthAccount.sub == sub)
            .first()
        )

    def create_oauth_user(self, *, email: str, full_name: str, provider: str, sub: str, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name, role=UserRole.player)
        self.db.add(user)
        self.db.flush()
        self.db.add(OAuthAccount(user_id=user.id, provider=provider, sub=sub))
        return user
