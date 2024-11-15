import json
from todo_app import app
import pytest

#Populate tasks.json before testing
def populate_tasks():
    with open("test_tasks.json", "r") as f:
        tasks= json.load(f)
        with open("tasks.json", "w") as file:
            json.dump(tasks, file, indent=4)

@pytest.fixture
def client():
    app.config['TESTING']=True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def setup_tasks():
    populate_tasks()

def test_get_all_tasks(client):
    response= client.get('/tasks')
    assert response.status_code==200
    assert isinstance(response.json, list)

def test_get_completed_tasks(client):
    response= client.get('/tasks?completed=true')
    assert response.status_code==200
    assert isinstance(response.json, list)
    assert all(task['status']=='completed' for task in response.json)

def test_get_incomplete_tasks(client):
    response = client.get('/tasks?completed=false')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert all(task['status'] != 'completed' for task in response.json)


def test_task_by_id(client):
    # A task from json file
    test_task={
        "id": 122,
        "description": "Hello143",
        "category": "shopping",
        "status": "completed"
    }
    response= client.get("/tasks/122")
    assert response.status_code==200
    assert dict(response.json) == test_task

def test_task_by_id_not_found(client):
    response=client.get("/tasks/199")
    assert response.status_code==404
    assert response.json== {"message": "task not found"}

def test_add_new_task(client):
    new_task= {
        "description": "new clothes",
        "category": "shopping",
    }
    response = client.post("/tasks", data= new_task)
    assert response.status_code==200
    assert response.json=={"message":"Task successfully added"}

def test_add_new_task_missing_info(client):
    new_task= {
        "category": "shopping",
    }
    response = client.post("/tasks", data= new_task)
    assert response.status_code==400
    print(response)
    assert response.json=={"error":"description is required"}

def test_add_new_task_duplicate_check(client):
    new_task = {
        "id": 126,
        "description": "new clothes",
        "category": "shopping",
        "status": "pending"
    }
    response = client.post("/tasks", data=new_task)
    assert response.status_code == 400
    assert response.json == {"error": "This task already exists"}

def test_update_task(client):
    new_task_info= {
        "description": "new description",
        "category": "cleaning",
        "status": "completed"
    }
    response= client.put("/tasks/121", data=new_task_info)
    assert response.status_code==200
    updated_task = client.get("/tasks/121").json
    assert updated_task["description"] == "new description"
    assert updated_task["category"] == "cleaning"
    assert updated_task["status"] == "completed"
    assert response.json=={"message": "Task updated successfully"}

def test_update_task_not_found(client):
    updated_task= {
        "description": "new description",
        "category": "shopping",
        "status": "completed"
    }
    response= client.put("/tasks/199", data=updated_task)
    assert response.status_code==404
    assert response.json=={"error": "Task not found"}

def test_complete_task(client):
    response= client.put("/tasks/125/complete")
    assert response.status_code == 200

    assert response.json=={"message": "task marked completed"}

def test_complete_task_not_found(client):
    response=client.put("/tasks/199/complete")
    assert response.status_code==404
    assert response.json=={"error": "task not found"}

def test_complete_task_when_already_completed(client):
    response= client.put("/tasks/122/complete")
    assert response.status_code==400
    assert response.json=={"message": "Task is already completed"}

def test_show_categories(client):
    available_categories = ["cleaning","shopping"]
    available_categories.sort()
    response= client.get("/tasks/categories")
    assert response.status_code==200
    assert response.json== {"message": f"All the available categories are {available_categories}" }

def test_task_by_category(client):
    response= client.get("/tasks/categories/cleaning")
    assert response.status_code==200
    assert all(task['category']=='cleaning' for task in response.json)

def test_delete_task(client):
    response = client.delete("/tasks/123", json={"password": "786"})
    assert response.status_code==200
    assert response.json=={"message": "The task has been successfully removed"}

def test_delete_task_not_found(client):
    response = client.delete("/tasks/199", json={"password": "786"})
    assert response.status_code == 404
    assert response.json == {"error": "Task not found"}

def test_delete_task_unauthorized(client):
    response = client.delete("/tasks/123", json={"password": "987"})
    assert response.status_code == 401
    assert response.json == {"error": "Invalid password"}


def test_delete_task_invalid_json(client):
    response = client.delete("/tasks/123", data="sending invalid data")
    assert response.status_code == 400
    assert response.json == {"error": "Invalid Json"}
