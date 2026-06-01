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


# Idempotent column additions for SQLite — applied on every startup. SQLite ignores
# the ADD COLUMN if it already exists (we swallow the OperationalError).
_MIGRATIONS = [
    "ALTER TABLE simulation_runs ADD COLUMN channel_distance_km REAL DEFAULT 0.0",
    "ALTER TABLE simulation_runs ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
]


def init_db():
    # noqa: F401 — these imports register the models on Base before create_all
    from database.models import User, PasswordResetToken, SimulationRun  # noqa: F401
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        for stmt in _MIGRATIONS:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass  # column already exists / migration already applied
