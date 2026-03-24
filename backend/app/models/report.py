import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReportStatus(str, enum.Enum):
    open = "open"
    reviewing = "reviewing"
    closed = "closed"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject_type: Mapped[str] = mapped_column(String(50))
    subject_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[ReportStatus] = mapped_column(SAEnum(ReportStatus), default=ReportStatus.open)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
