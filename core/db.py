from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

db_path = Path(__file__).with_name('data') / 'cost.db'   # 任意位置
db_path.parent.mkdir(exist_ok=True)                      # 关键！

engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.absolute()}")

async_session = async_sessionmaker(bind=engine,class_=AsyncSession, expire_on_commit=False)
