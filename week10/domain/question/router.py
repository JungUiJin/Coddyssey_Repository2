# domain/question/router.py
from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Question

router = APIRouter(
    prefix='/questions',
    tags=['questions'],
)


def question_to_dict(question: Question) -> dict:
    return {
        'id': question.id,
        'subject': question.subject,
        'content': question.content,
        'create_date': (
            question.create_date.isoformat()
            if question.create_date
            else None
        ),
    }


@router.get(
    '/',
    summary='질문 목록 조회',
)
def read_questions(db: Session = Depends(get_db)) -> List[dict]:
    questions = (
        db.query(Question)
        .order_by(Question.id.desc())
        .all()
    )
    return [question_to_dict(question) for question in questions]


@router.get(
    '/{question_id}',
    summary='질문 상세 조회',
)
def read_question(
    question_id: int,
    db: Session = Depends(get_db),
) -> dict:
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
    return question_to_dict(question)


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    summary='질문 등록',
)
def create_question(
    subject: str = Body(...),
    content: str = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    question = Question(
        subject=subject,
        content=content,
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    return question_to_dict(question)
