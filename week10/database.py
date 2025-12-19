from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

SQLALCHEMY_DATABASE_URL = 'sqlite:///./app.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={'check_same_thread': False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# contextlib.contextmanager 를 이용한 DB 세션 컨텍스트
@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    실제로 SessionLocal()을 만들고,
    with 블록이 끝나면 자동으로 close 되는 컨텍스트 매니저.
    """
    db = SessionLocal()
    try:
        # 여기서 DB 연결이 '열려 있는 상태'
        yield db
    finally:
        # 여기서 항상 세션 정리
        db.close()


# FastAPI Depends 에서 사용할 의존성 함수
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI의 Depends 용 의존성 함수.
    내부에서 contextlib 컨텍스트 매니저(db_session)를 사용해서
    세션을 열고, 요청이 끝나면 자동으로 닫힌다.
    """
    with db_session() as db:
        yield db
