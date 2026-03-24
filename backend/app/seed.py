"""Cria usuário admin inicial (MVP). Execute: python -m app.seed (na pasta backend)."""
from app.database import Base, SessionLocal, engine
from app.models.user import User, UserRole
from app.security import hash_password


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "admin@ttv.local").first():
            print("Admin já existe.")
            return
        admin = User(
            email="admin@ttv.local",
            hashed_password=hash_password("admin123"),
            full_name="Administrador TTV",
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
        print("Criado admin@ttv.local / admin123 (altere em produção).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
