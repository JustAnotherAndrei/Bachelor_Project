from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./sequre.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from database.models import SimulationRun  # noqa: F401 — ensures model is registered
    Base.metadata.create_all(bind=engine)
    # Migrate: add channel_distance_km column to existing databases
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE simulation_runs ADD COLUMN channel_distance_km REAL DEFAULT 0.0"
            ))
            conn.commit()
        except Exception:
            pass  # column already exists
