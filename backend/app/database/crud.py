from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Base

ModelT = TypeVar("ModelT", bound=Base)


def create_record(session: Session, record: ModelT) -> ModelT:
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_record(session: Session, model: type[ModelT], record_id: str) -> ModelT | None:
    return session.get(model, record_id)


def list_records(
    session: Session,
    model: type[ModelT],
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[ModelT]:
    statement = select(model).offset(offset).limit(limit)
    return list(session.scalars(statement))


def update_record(session: Session, record: ModelT, values: dict[str, Any]) -> ModelT:
    for key, value in values.items():
        if hasattr(record, key):
            setattr(record, key, value)
    session.commit()
    session.refresh(record)
    return record
