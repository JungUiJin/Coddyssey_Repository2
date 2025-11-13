# model.py

from pydantic import BaseModel

class TodoItem(BaseModel):
    """
    Todo 항목 수정을 위한 Pydantic 모델
    task와 completed 상태를 입력받습니다.
    """
    task: str
    completed: bool