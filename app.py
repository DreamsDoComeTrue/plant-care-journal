import json
import os
from datetime import date, datetime, timedelta, timezone

import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, flash, g, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")


def get_db():
    if "db" not in g:
        if not firebase_admin._apps:
            service_account = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
            if service_account:
                firebase_admin.initialize_app(credentials.Certificate(json.loads(service_account)))
            else:
                firebase_admin.initialize_app()
        g.db = firestore.client()
    return g.db


def task_due(task):
    if not task.get("last_completed"):
        return True
    completed = date.fromisoformat(task["last_completed"])
    return date.today() >= completed + timedelta(days=int(task["interval_days"]))


def plant_with_tasks(snapshot):
    plant = {"id": snapshot.id, **snapshot.to_dict()}
    task_docs = get_db().collection("plants").document(snapshot.id).collection("tasks").stream()
    plant["tasks"] = []
    for task_doc in task_docs:
        task = {"id": task_doc.id, **task_doc.to_dict(), "due": False}
        task["due"] = task_due(task)
        plant["tasks"].append(task)
    return plant


@app.teardown_appcontext
def close_db(_error=None):
    g.pop("db", None)


@app.route("/")
def index():
    snapshots = get_db().collection("plants").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    plants = [plant_with_tasks(snapshot) for snapshot in snapshots]
    due_count = sum(task["due"] for plant in plants for task in plant["tasks"])
    return render_template("index.html", plants=plants, due_count=due_count)

@app.post("/task/<plant_id>/<task_id>/delete")
def delete_task(plant_id, task_id):
    task_ref = get_db().collection("plants").document(plant_id).collection("tasks").document(task_id)

    if not task_ref.get().exists:
        return "Task not found", 404

    task_ref.delete()
    flash("Task removed.", "success")
    return redirect(url_for("plant_detail", plant_id=plant_id))

@app.route("/plant/<plant_id>")
def plant_detail(plant_id):
    snapshot = get_db().collection("plants").document(plant_id).get()
    if not snapshot.exists:
        return "Plant not found", 404
    plant = plant_with_tasks(snapshot)
    note_docs = get_db().collection("plants").document(plant_id).collection("notes").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    notes = [{"id": note.id, **note.to_dict()} for note in note_docs]
    return render_template("plant_detail.html", plant=plant, notes=notes)


@app.route("/plants/add", methods=["GET", "POST"])
def add_plant():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        species = request.form.get("species", "").strip()
        light = request.form.get("light", "Bright indirect")
        interval = max(1, int(request.form.get("watering_interval", 7)))
        if not name:
            flash("Plant nickname is required.", "error")
            return render_template("add_plant.html")

        db = get_db()
        plant_ref = db.collection("plants").document()
        plant_ref.set({"name": name, "species": species, "light": light, "created_at": datetime.now(timezone.utc).isoformat()})
        plant_ref.collection("tasks").document().set({"task_name": "Watering", "interval_days": interval, "last_completed": None})
        flash(f"{name} was added to your garden.", "success")
        return redirect(url_for("plant_detail", plant_id=plant_ref.id))
    return render_template("add_plant.html")


@app.post("/plant/<plant_id>/tasks")
def add_task(plant_id):
    task_name = request.form.get("task_name", "").strip()
    interval = max(1, int(request.form.get("interval_days", 7)))
    plant_ref = get_db().collection("plants").document(plant_id)
    if task_name and plant_ref.get().exists:
        plant_ref.collection("tasks").document().set({"task_name": task_name, "interval_days": interval, "last_completed": None})
    return redirect(url_for("plant_detail", plant_id=plant_id))


@app.post("/task/<plant_id>/<task_id>/complete")
def complete_task(plant_id, task_id):
    task_ref = get_db().collection("plants").document(plant_id).collection("tasks").document(task_id)
    if not task_ref.get().exists:
        return "Task not found", 404
    task_ref.update({"last_completed": date.today().isoformat()})
    return redirect(url_for("plant_detail", plant_id=plant_id))


@app.post("/plant/<plant_id>/notes")
def add_note(plant_id):
    body = request.form.get("body", "").strip()
    plant_ref = get_db().collection("plants").document(plant_id)
    if body and plant_ref.get().exists:
        plant_ref.collection("notes").document().set({"body": body, "created_at": datetime.now(timezone.utc).isoformat()})
    return redirect(url_for("plant_detail", plant_id=plant_id))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
