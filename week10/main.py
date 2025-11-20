# main.py
from fastapi import FastAPI

from database import Base, engine
from domain.question import router as question_router

app = FastAPI(
    title='Mars Board API',
    description='화성 연구 기지 게시판 예제',
    version='0.1.0',
)

# Alembic을 사용하는 경우에는 실제 서비스에서는 생략 가능.
# 과제 실습용으로 남겨두고, 마이그레이션이 제대로 되는지 확인했다면
# 주석 처리해도 됩니다.
Base.metadata.create_all(bind=engine)

app.include_router(question_router)
