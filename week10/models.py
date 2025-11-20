# models.py
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Question(Base):
    __tablename__ = 'question'

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    create_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    answers = relationship(
        'Answer',
        back_populates='question',
        cascade='all, delete-orphan',
    )


class Answer(Base):
    __tablename__ = 'answer'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    create_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    question_id = Column(
        Integer,
        ForeignKey('question.id'),
        nullable=False,
    )

    question = relationship(
        'Question',
        back_populates='answers',
    )
