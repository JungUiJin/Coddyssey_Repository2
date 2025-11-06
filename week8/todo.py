# todo.py

from fastapi import FastAPI, APIRouter, HTTPException, status
from typing import Dict, List, Any

# --- 기본 설정 ---

# FastAPI 메인 앱 인스턴스 생성
app = FastAPI()

# APIRouter 인스턴스 생성
# (라우터를 사용하면 API 엔드포인트를 모듈화하여 관리하기 좋습니다)
router = APIRouter()

# todo_list 리스트 객체 생성 (인메모리 데이터베이스 역할)
# 타입 힌팅: Dict 객체들로 이루어진 List
todo_list: List[Dict[str, Any]] = []


# --- API 라우트 정의 ---

@router.post('/add', status_code=status.HTTP_201_CREATED)
async def add_todo(item: Dict[str, Any]):
    """
    새로운 TO-DO 항목을 todo_list에 추가합니다.
    - POST 방식
    - 입출력: Dict 타입
    - 보너스 과제: 입력값이 비어있으면 400 오류 반환
    """
    
    # 보너스 과제: 입력된 Dict가 비어있는지 확인
    if not item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Todo item cannot be empty'
        )
    
    # todo_list에 항목 추가
    todo_list.append(item)
    
    # 성공 메시지와 추가된 항목을 Dict 타입으로 반환
    return {'message': 'New todo added successfully', 'item': item}


@router.get('/list')
async def retrieve_todo():
    """
    전체 todo_list를 가져옵니다.
    - GET 방식
    - 출력: Dict 타입
    """
    
    # todo_list를 포함하는 Dict 타입으로 반환
    return {'todos': todo_list}


# --- 라우터 앱에 등록 ---

# '/api' 접두사(prefix)와 함께 메인 앱(app)에 라우터(router)를 포함시킵니다.
# 이제 엔드포인트는 /api/add, /api/list 가 됩니다.
app.include_router(router, prefix='/api')