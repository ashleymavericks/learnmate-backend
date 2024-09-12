from sqlmodel import SQLModel, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.schema import UserQuestion, ChatInteraction, ChatMessage, UserAssessment
from uuid import UUID
from typing import List, Dict


DATABASE_URL = "sqlite+aiosqlite:///./database.db"
engine = create_async_engine(DATABASE_URL)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
async def get_record(model, record_id: UUID):
    async with AsyncSession(engine) as session:
        record = await session.get(model, record_id)
        return record

  
async def get_all_records(model, filter_by: Dict = None, include_related: List[str] = None):
    async with AsyncSession(engine) as session:
        statement = select(model)
        if filter_by:
            for key, value in filter_by.items():
                statement = statement.where(getattr(model, key) == value)
                
        if include_related:
            for relation in include_related:
                if hasattr(model, relation):
                    statement = statement.options(selectinload(getattr(model, relation)))

        result = await session.execute(statement)
        records = result.scalars().all()
        return records


async def insert_into_sqlite(data: UserQuestion | UserAssessment | ChatInteraction | ChatMessage | List[UserQuestion | ChatMessage]):
    async with AsyncSession(engine) as session:
        if isinstance(data, list):
            session.add_all(data)
        else:
            session.add(data)
        await session.commit()
        if not isinstance(data, list):
            await session.refresh(data)
        return data


async def update_record(model, record_id: UUID, **kwargs):
    async with AsyncSession(engine) as session:
        record = await session.get(model, record_id)
        if record:
            for key, value in kwargs.items():
                setattr(record, key, value)
            await session.commit()
            await session.refresh(record)
            return record
        return None


async def bulk_update_records(model, updates: List[Dict[str, any]]):
    async with AsyncSession(engine) as session:
        for update in updates:
            record_id = update.pop('id', None)
            if record_id:
                record = await session.get(model, record_id)
                if record:
                    for key, value in update.items():
                        setattr(record, key, value)
        await session.commit()
