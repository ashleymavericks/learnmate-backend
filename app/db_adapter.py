from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.schema import UserQuestion, ChatInteraction, ChatMessage

DATABASE_URL = "sqlite+aiosqlite:///./database.db"
engine = create_async_engine(DATABASE_URL)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
async def get_session():
    async with AsyncSession(engine) as session:
        yield session

async def insert_into_sqlite(data: UserQuestion | ChatInteraction | ChatMessage):
    session = get_session()
    session.add(data)
    await session.commit()
    await session.refresh(data)
    return data
