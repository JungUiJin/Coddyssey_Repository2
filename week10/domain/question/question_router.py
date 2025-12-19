from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models import Question

router = APIRouter(
    prefix='/api/question',
    tags=['questions'],
)


# --------------------------
# Pydantic 질문 스키마 정의
# --------------------------

class QuestionBase(BaseModel):
    subject: str
    content: str


class QuestionCreate(QuestionBase):
    """
    질문 생성 요청 바디에서 사용할 스키마
    (subject, content는 빈 값을 허용하지 않음)
    """
    subject: str = Field(..., min_length=1, description='질문 제목')
    content: str = Field(..., min_length=1, description='질문 내용')


class QuestionRead(QuestionBase):
    """
    클라이언트에게 응답으로 돌려줄 때 사용할 스키마
    """
    id: int
    create_date: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get(
    '/',
    summary='질문 목록 조회',
    response_model=List[QuestionRead],
)
def question_list(
    db: Session = Depends(get_db),
) -> List[QuestionRead]:
    """
    등록된 모든 질문을 최신순으로 조회합니다.
    """
    questions = (
        db.query(Question)
        .order_by(Question.id.desc())
        .all()
    )
    return questions


@router.get(
    '/{question_id}',
    summary='질문 상세 조회',
    response_model=QuestionRead,
)
def read_question(
    question_id: int,
    db: Session = Depends(get_db),
) -> QuestionRead:
    """
    특정 질문의 상세 정보를 조회합니다.
    """
    question = (
        db.query(Question)
        .filter(Question.id == question_id)
        .first()
    )
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='질문을 찾을 수 없습니다.',
        )
    return question


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    summary='질문 등록',
    response_model=QuestionRead,
)
def create_question(
    question_in: QuestionCreate,
    db: Session = Depends(get_db),
) -> QuestionRead:
    """
    새로운 질문을 등록합니다.
    제목과 내용은 필수이며 빈 값을 허용하지 않습니다.
    """
    question = Question(
        subject=question_in.subject,
        content=question_in.content,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question