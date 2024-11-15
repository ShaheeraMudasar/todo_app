import json
from functools import wraps
from textwrap import indent
from flask import Flask, render_template, request, flash, url_for, make_response
from unicodedata import category
from werkzeug.utils import redirect

app= Flask(__name__)
app.secret_key = "ninjaMessage"
tasks={}

# This method gets tasks from json file
def load_tasks():
    global tasks

    try:
        with open("tasks.json") as f:
            tasks = json.load(f)
    except json.JSONDecodeError:
        print("Warning: JSONDecodeError - tasks.json might be empty or invalid.")
        tasks = []
    except FileNotFoundError:
        print("Warning: FileNotFoundError - tasks.json not found.")
        tasks = []

load_tasks()

#frontend implementation showing all tasks and adding new task
@app.route("/")
def get_all_tasks(task_id=None):
        return render_template("todo_app.html", tasks= tasks, task_found=None)

@app.route("/add_task", methods=["POST"])
def add_task():
    task_category=request.form["category"]
    task_description=request.form["description"]

    if not task_category and not task_category:
        flash("Task category and description is required")
        return redirect(url_for("get_all_tasks"))

    if not task_category:
        flash("Task category is required")
        return redirect(url_for("get_all_tasks"))

    if not task_description:
        flash("Task description is required")
        return redirect(url_for("get_all_tasks"))

    for task in tasks:
        if task["description"] == task_description:
            flash("This task already exists")
            return redirect(url_for("get_all_tasks"))
    else:
        max_id= max(task["id"] for task in tasks) if tasks else 120
        task_id= max_id + 1
        new_task = {
            "id": task_id,
            "description": task_description,
            "category": task_category,
            "status": "pending"
        }
        tasks.append(new_task)

        with open("tasks.json", "w") as f:
            json.dump(tasks, f, indent=4)

        flash("Task successfully added")
    return redirect(url_for("get_all_tasks"))


#endpoints implementation
@app.route("/tasks")
def get_tasks():
    is_completed=request.args.get('completed')
    completed_tasks=[]
    pending_tasks=[]

    if is_completed =="true":
        for task in tasks:
            if task['status'] == "completed":
                completed_tasks.append(task)
        return completed_tasks, 200

    elif is_completed =="false":
        for task in tasks:
            if task['status'] == "pending":
                pending_tasks.append(task)
        return pending_tasks, 200

    return tasks, 200

@app.route("/tasks/<int:task_id>",  methods=["GET"])
def task_by_id(task_id):

    #finding task
    for task in tasks:
        if task["id"]==task_id:
            return task, 200

    return {"message": "task not found"}, 404

@app.route("/tasks", methods=["POST"])
def add_new_task():
    category=request.form.get('category')
    description=request.form.get('description')

    #check if category and/or description are not provided
    if not category and not description:
        return {"error": "category and description are required"}, 400

    if not category:
        return {"error": "category is required"}, 400

    if not description:
        return {"error": "description is required"}, 400

    #check if task already exists
    for task in tasks:
        if str(task["description"])==description:
            return {"error": "This task already exists"}, 400

    #get last id to get new task id and add the task
    max_id = max(task["id"] for task in tasks) if tasks else 120
    task_id = max_id + 1
    new_task = {
        "id": task_id,
        "description": description,
        "category": category,
        "status": "pending"
    }
    tasks.append(new_task)

    #updating json file
    with open("tasks.json", "w") as f:
        json.dump(tasks, f, indent=4)

    return {"message":"Task successfully added"}, 200


def require_password(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        #checking if proper json exists
        if not request.is_json:
            return {"error": "Invalid Json"}, 400

        #checking for password
        data = request.get_json()
        if data.get("password") != "786":
            return {"error": "Invalid password"}, 401

        return f(*args, **kwargs)

    return decorated_function

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@require_password
def delete_task(task_id):

    #creating a new task list without the one which is deleted and writing in json
    for task in tasks:
        if task_id == int(task["id"]):
            new_tasks = [task for task in tasks if str(task["id"]) != str(task_id)]

            with open("tasks.json", "w") as file:
                json.dump(new_tasks, file, indent=4)

            #loading new list of tasks with one task deleted from the list
            load_tasks()
            return {"message": "The task has been successfully removed"}, 200

    return {"error": "Task not found"}, 404

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task_found = None

    #finding task
    task_found, status= task_by_id(task_id)

    if status==404:
        return {"error": "Task not found"}, 404

    # Parsing json data from the request body

    description = request.form.get("description")
    category = request.form.get("category")
    status = request.form.get("status")

    #checking for required fields
    if description:
        task_found["description"]= description
    if category:
        task_found["category"]= category
    if status:
        task_found["status"] = status

    # Save the updated tasks list to the JSON file
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, indent=4)

    return {"message": "Task updated successfully"}, 200

@app.route("/tasks/<int:task_id>/complete", methods=["PUT"])
def complete_task(task_id):

    #getting task
    task_found, status=task_by_id(task_id)

    if status== 404:
        return {"error": "task not found"}, 404

    #marking 'completed' if 'pending'
    if task_found['status']=="pending":
        task_found["status"]="completed"

    #updating json
        with open("tasks.json", "w") as f:
            json.dump(tasks, f, indent=4)
        return {"message": "task marked completed"}, 200

    return {"message": "Task is already completed"}, 400

@app.route("/tasks/categories", methods=["GET"])
def get_categories():
    categories=[] #for saving all categories

    for item in tasks:
        if item["category"]:
            categories.append(item['category'])

    available_categories= list(dict.fromkeys(categories)) #removing duplicates
    available_categories.sort() #sorting for testing

    return {"message": f"All the available categories are {available_categories}" }, 200

@app.route("/tasks/categories/<category_name>",  methods=["GET"])
def task_by_category(category_name):
    tasks_in_category=[]

    for task in tasks:
        if task['category']==category_name:
            tasks_in_category.append(task)
    return tasks_in_category, 200


if __name__ == "__main__":
    app.run(debug=True)