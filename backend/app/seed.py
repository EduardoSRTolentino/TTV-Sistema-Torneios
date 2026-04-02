"""Cria usuário admin inicial (MVP). Execute: python -m app.seed (na pasta backend)."""
from app.database import Base, SessionLocal, engine
from app.models.user import User, UserRole
from app.security import hash_password


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Use a valid domain: Pydantic EmailStr rejects special-use TLDs like `.local`.
        admin_email = "admin@ttv.com"
        if db.query(User).filter(User.email == admin_email).first():
            print("Admin já existe.")
            return
        admin = User(
            email=admin_email,
            hashed_password=hash_password("Admin123!"),
            full_name="Administrador TTV",
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
        print(f"Criado {admin_email} / Admin123! (altere em produção).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
