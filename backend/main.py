from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).with_name("nido.db")


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS members (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          initials TEXT NOT NULL, color TEXT NOT NULL, role TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
          category TEXT NOT NULL, due_date TEXT NOT NULL, due_time TEXT,
          assignee_id INTEGER REFERENCES members(id), completed INTEGER NOT NULL DEFAULT 0,
          priority TEXT NOT NULL DEFAULT 'normal', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
          event_date TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT,
          location TEXT, category TEXT NOT NULL, member_id INTEGER REFERENCES members(id)
        );
        CREATE TABLE IF NOT EXISTS shopping_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          quantity TEXT NOT NULL DEFAULT '1', section TEXT NOT NULL,
          checked INTEGER NOT NULL DEFAULT 0, added_by INTEGER REFERENCES members(id)
        );
        CREATE TABLE IF NOT EXISTS expenses (
          id INTEGER PRIMARY KEY AUTOINCREMENT, concept TEXT NOT NULL,
          amount REAL NOT NULL, category TEXT NOT NULL, expense_date TEXT NOT NULL,
          member_id INTEGER REFERENCES members(id)
        );
        """)
        if db.execute("SELECT COUNT(*) FROM members").fetchone()[0]:
            return
        db.executemany("INSERT INTO members(name,initials,color,role) VALUES(?,?,?,?)", [
            ("Mara", "MA", "#315c4a", "Administradora"),
            ("Leo", "LE", "#bd795d", "Adulto"),
            ("Nora", "NO", "#d2a953", "Hija"),
            ("Teo", "TE", "#6b86a0", "Hijo"),
        ])
        today = date.today()
        db.executemany("INSERT INTO tasks(title,category,due_date,due_time,assignee_id,completed,priority) VALUES(?,?,?,?,?,?,?)", [
            ("Pedir cita con el pediatra", "Salud", str(today), "10:30", 1, 0, "alta"),
            ("Entregar autorización de la excursión", "Colegio", str(today), "17:00", 2, 0, "normal"),
            ("Preparar mochila de natación", "Rutina", str(today), "18:15", 3, 0, "normal"),
            ("Revisar seguro del coche", "Casa", str(today + timedelta(days=1)), None, 2, 0, "normal"),
            ("Cambiar sábanas", "Casa", str(today - timedelta(days=1)), None, 1, 1, "normal"),
        ])
        db.executemany("INSERT INTO events(title,event_date,start_time,end_time,location,category,member_id) VALUES(?,?,?,?,?,?,?)", [
            ("Tutoría de Nora", str(today), "16:30", "17:00", "Colegio Mirador", "Colegio", 3),
            ("Natación", str(today), "18:30", "19:30", "Polideportivo", "Actividad", 3),
            ("Dentista de Teo", str(today + timedelta(days=1)), "11:15", "12:00", "Clínica Norte", "Salud", 4),
            ("Cena con los abuelos", str(today + timedelta(days=2)), "20:30", "22:30", "Casa", "Familia", 1),
        ])
        db.executemany("INSERT INTO shopping_items(name,quantity,section,checked,added_by) VALUES(?,?,?,?,?)", [
            ("Leche entera", "2 bricks", "Despensa", 0, 2),
            ("Plátanos", "1 manojo", "Fruta y verdura", 0, 1),
            ("Yogur natural", "8 uds.", "Frío", 0, 1),
            ("Pan de molde", "1 ud.", "Despensa", 1, 3),
            ("Detergente", "1 botella", "Hogar", 0, 2),
        ])
        db.executemany("INSERT INTO expenses(concept,amount,category,expense_date,member_id) VALUES(?,?,?,?,?)", [
            ("Compra semanal", 86.40, "Alimentación", str(today), 1),
            ("Natación Nora", 42.00, "Actividades", str(today - timedelta(days=2)), 2),
            ("Farmacia", 18.75, "Salud", str(today - timedelta(days=4)), 1),
            ("Electricidad", 67.32, "Casa", str(today - timedelta(days=6)), 2),
        ])


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Nido API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    category: str = "Casa"
    due_date: date
    due_time: str | None = None
    assignee_id: int | None = None
    priority: Literal["normal", "alta"] = "normal"


class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    event_date: date
    start_time: str
    end_time: str | None = None
    location: str | None = None
    category: str = "Familia"
    member_id: int | None = None


class ShoppingCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    quantity: str = "1"
    section: str = "Otros"
    added_by: int | None = None


class ExpenseCreate(BaseModel):
    concept: str = Field(min_length=2, max_length=120)
    amount: float = Field(gt=0)
    category: str = "Otros"
    expense_date: date = Field(default_factory=date.today)
    member_id: int | None = None


def rows(sql: str, params: tuple = ()) -> list[dict]:
    with connect() as db:
        return [dict(row) for row in db.execute(sql, params).fetchall()]


@app.get("/api/health")
def health(): return {"status": "ok"}


@app.get("/api/members")
def members(): return rows("SELECT * FROM members ORDER BY id")


@app.get("/api/tasks")
def tasks(status: Literal["all", "open", "done"] = "all"):
    where = {"all": "", "open": "WHERE t.completed=0", "done": "WHERE t.completed=1"}[status]
    return rows(f"SELECT t.*,m.name assignee_name,m.initials,m.color FROM tasks t LEFT JOIN members m ON m.id=t.assignee_id {where} ORDER BY t.completed,t.due_date,t.due_time")


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    with connect() as db:
        cur = db.execute("INSERT INTO tasks(title,category,due_date,due_time,assignee_id,priority) VALUES(?,?,?,?,?,?)", (task.title, task.category, str(task.due_date), task.due_time, task.assignee_id, task.priority))
        task_id = cur.lastrowid
    return rows("SELECT * FROM tasks WHERE id=?", (task_id,))[0]


@app.patch("/api/tasks/{task_id}/toggle")
def toggle_task(task_id: int):
    with connect() as db:
        cur = db.execute("UPDATE tasks SET completed=1-completed WHERE id=?", (task_id,))
        if not cur.rowcount: raise HTTPException(404, "Tarea no encontrada")
    return {"ok": True}


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with connect() as db: db.execute("DELETE FROM tasks WHERE id=?", (task_id,))


@app.get("/api/events")
def events(from_date: date | None = Query(None)):
    start = str(from_date or date.today() - timedelta(days=30))
    return rows("SELECT e.*,m.name member_name,m.initials,m.color FROM events e LEFT JOIN members m ON m.id=e.member_id WHERE event_date>=? ORDER BY event_date,start_time", (start,))


@app.post("/api/events", status_code=201)
def create_event(event: EventCreate):
    with connect() as db:
        cur = db.execute("INSERT INTO events(title,event_date,start_time,end_time,location,category,member_id) VALUES(?,?,?,?,?,?,?)", (event.title,str(event.event_date),event.start_time,event.end_time,event.location,event.category,event.member_id))
    return {"id": cur.lastrowid}


@app.get("/api/shopping")
def shopping(): return rows("SELECT s.*,m.name added_by_name FROM shopping_items s LEFT JOIN members m ON m.id=s.added_by ORDER BY checked,section,name")


@app.post("/api/shopping", status_code=201)
def create_shopping(item: ShoppingCreate):
    with connect() as db:
        cur = db.execute("INSERT INTO shopping_items(name,quantity,section,added_by) VALUES(?,?,?,?)", (item.name,item.quantity,item.section,item.added_by))
    return {"id": cur.lastrowid}


@app.patch("/api/shopping/{item_id}/toggle")
def toggle_shopping(item_id: int):
    with connect() as db: db.execute("UPDATE shopping_items SET checked=1-checked WHERE id=?", (item_id,))
    return {"ok": True}


@app.delete("/api/shopping/{item_id}", status_code=204)
def delete_shopping(item_id: int):
    with connect() as db: db.execute("DELETE FROM shopping_items WHERE id=?", (item_id,))


@app.get("/api/expenses")
def expenses(): return rows("SELECT e.*,m.name member_name FROM expenses e LEFT JOIN members m ON m.id=e.member_id ORDER BY expense_date DESC,id DESC")


@app.post("/api/expenses", status_code=201)
def create_expense(expense: ExpenseCreate):
    with connect() as db:
        cur = db.execute("INSERT INTO expenses(concept,amount,category,expense_date,member_id) VALUES(?,?,?,?,?)", (expense.concept,expense.amount,expense.category,str(expense.expense_date),expense.member_id))
    return {"id": cur.lastrowid}


@app.get("/api/dashboard")
def dashboard():
    today = str(date.today())
    month = date.today().strftime("%Y-%m")
    with connect() as db:
        stats = {
            "open_tasks": db.execute("SELECT COUNT(*) FROM tasks WHERE completed=0").fetchone()[0],
            "today_events": db.execute("SELECT COUNT(*) FROM events WHERE event_date=?", (today,)).fetchone()[0],
            "shopping_left": db.execute("SELECT COUNT(*) FROM shopping_items WHERE checked=0").fetchone()[0],
            "month_spend": db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE expense_date LIKE ?", (month + "%",)).fetchone()[0],
        }
    return {"stats": stats, "tasks": tasks("open")[:4], "events": rows("SELECT e.*,m.name member_name,m.initials,m.color FROM events e LEFT JOIN members m ON m.id=e.member_id WHERE event_date>=? ORDER BY event_date,start_time LIMIT 4", (today,))}
