# todo.py

import csv
import os
from fastapi import FastAPI, APIRouter, HTTPException, status
from typing import Dict, List, Any

# 1. model.py에서 TodoItem 모델 가져오기
from model import TodoItem 

# --- 기본 설정 ---
app = FastAPI()
router = APIRouter()

# --- CSV 설정 ---
# 데이터를 저장할 CSV 파일 이름
CSV_FILE = 'todos.csv'
# CSV 파일의 헤더 (필드 이름)
FIELDNAMES = ['id', 'task', 'completed']


# --- CSV 헬퍼(Helper) 함수 ---

def initialize_csv():
    """
    CSV 파일이 존재하지 않으면, 헤더를 포함하여 새로 생성합니다.
    """
    if not os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()
        except IOError as e:
            # 파일 쓰기 권한이 없는 등 예외 처리
            print(f'Error initializing CSV file: {e}')
            raise

def read_todos_from_csv() -> List[Dict[str, Any]]:
    """
    CSV 파일에서 모든 TO-DO 항목을 읽어 리스트로 반환합니다.
    """
    initialize_csv() # 파일이 없으면 생성
    
    todos = []
    try:
        with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # CSV에서 읽은 데이터의 타입을 변환합니다. (CSV는 모든 것을 문자열로 저장)
                try:
                    row['id'] = int(row['id'])
                    # 'true' (대소문자 무관)일 때만 True, 나머지는 False
                    row['completed'] = row['completed'].lower() == 'true'
                    todos.append(row)
                except (ValueError, TypeError):
                    # id가 숫자가 아니거나 형식이 잘못된 데이터는 무시
                    print(f'Skipping malformed row: {row}')
                    
    except IOError as e:
        print(f'Error reading CSV file: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not read data file'
        )
    return todos

def write_todos_to_csv(todos: List[Dict[str, Any]]):
    """
    TO-DO 리스트 전체를 CSV 파일에 덮어씁니다.
    """
    try:
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            
            # CSV에 쓰기 위해 completed 값을 문자열로 변환
            for todo in todos:
                # 원본 딕셔너리를 수정하지 않기 위해 복사
                csv_row = todo.copy()
                csv_row['completed'] = str(csv_row['completed']) 
                writer.writerow(csv_row)
                
    except IOError as e:
        print(f'Error writing CSV file: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Could not write data file'
        )

def get_next_id(todos: List[Dict[str, Any]]) -> int:
    """
    현재 TO-DO 리스트를 기반으로 다음 ID를 생성합니다.
    """
    if not todos:
        return 1
    # max() 함수를 안전하게 사용하기 위해 리스트가 비어있지 않을 때만 실행
    return max(todo['id'] for todo in todos) + 1


# --- API 라우트 정의 (기존 + 신규) ---

@router.post('/add', status_code=status.HTTP_201_CREATED)
async def add_todo(item_data: Dict[str, Any]):
    """
    (수정됨) 새로운 TO-DO 항목을 CSV에 추가합니다.
    - 입력값 (Dict)에서 'task' 키를 기대합니다.
    """
    
    # 입력값 유효성 검사 (task 키가 있는지)
    if not item_data or 'task' not in item_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todo 리스트는 'task' 필드를 포함해야 합니다."
        )
    
    todos = read_todos_from_csv()
    next_id = get_next_id(todos)
    
    # 새 TO-DO 항목 생성 (completed 기본값은 False)
    new_todo = {
        'id': next_id,
        'task': item_data['task'],
        'completed': False 
    }
    
    todos.append(new_todo)
    write_todos_to_csv(todos) # CSV 파일에 저장
    
    return {'message': 'New todo added successfully', 'item': new_todo}


@router.get('/list')
async def retrieve_todo():
    """
    (수정됨) CSV에서 전체 todo_list를 가져옵니다.
    """
    todos = read_todos_from_csv()
    return {'todos': todos}


# --- ⬇️ 문제 3: 신규 추가 기능 ⬇️ ---

@router.get('/{item_id}')
async def get_single_todo(item_id: int):
    """
    (신규) 개별 TO-DO 항목을 조회합니다.
    - 경로 매개변수로 ID를 받습니다.
    """
    todos = read_todos_from_csv()
    
    for todo in todos:
        if todo['id'] == item_id:
            return {'todo': todo}
    
    # 항목을 찾지 못한 경우 404 오류 반환
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Todo with id {item_id} not found'
    )


@router.put('/{item_id}')
async def update_todo(item_id: int, item_update: TodoItem):
    """
    (신규) 개별 TO-DO 항목을 수정합니다.
    - 경로 매개변수로 ID를 받습니다.
    - 요청 본문(body)으로 TodoItem 모델을 받습니다.
    """
    todos = read_todos_from_csv()
    
    found = False
    updated_todo = None
    
    for i, todo in enumerate(todos):
        if todo['id'] == item_id:
            # Pydantic 모델(item_update)의 데이터로 기존 항목(todo)을 업데이트
            todos[i]['task'] = item_update.task
            todos[i]['completed'] = item_update.completed
            updated_todo = todos[i]
            found = True
            break
            
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Todo with id {item_id} not found'
        )
    
    write_todos_to_csv(todos) # 변경 사항을 CSV에 저장
    
    return {'message': 'Todo updated successfully', 'item': updated_todo}


@router.delete('/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_single_todo(item_id: int):
    """
    (신규) 개별 TO-DO 항목을 삭제합니다.
    - 경로 매개변수로 ID를 받습니다.
    - 성공 시 204 No Content 상태 코드를 반환합니다.
    """
    todos = read_todos_from_csv()
    
    todo_to_delete = None
    for todo in todos:
        if todo['id'] == item_id:
            todo_to_delete = todo
            break
            
    if todo_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Todo with id {item_id} not found'
        )
        
    # 리스트에서 해당 항목 제거
    todos.remove(todo_to_delete)
    
    write_todos_to_csv(todos) # 변경 사항을 CSV에 저장
    
    # 204 응답은 본문(body)을 포함하지 않으므로, None 또는 빈 Response를 반환
    return


# --- 라우터 앱에 등록 ---

# (기억하고 있던 코드)
# /api 접두사로 라우터를 앱에 포함시킵니다.
# (순서 중요: /list가 /{item_id}보다 먼저 정의되어야 '/list'를 ID로 착각하지 않습니다.)
app.include_router(router, prefix='/api')