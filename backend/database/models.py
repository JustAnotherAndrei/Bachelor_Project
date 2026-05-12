from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime
from database.db import Base


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    n_qubits = Column(Integer)
    depolarizing_prob = Column(Float)
    measurement_error_prob = Column(Float)
    eve_intercept = Column(Boolean, default=False)
    sifted_key_length = Column(Integer)
    qber = Column(Float)
    is_secure = Column(Boolean)
    final_key = Column(String)
