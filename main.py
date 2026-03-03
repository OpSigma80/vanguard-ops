import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="VanguardOps Engine", version="1.1.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# --- INICIALIZADOR DE INFRAESTRUCTURA ---
def init_db():
    """Asegura que las tablas existan al arrancar"""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Crear tabla de Leads
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id UUID PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    source TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Crear tabla de Logs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
    print("🛡️ INFRAESTRUCTURA VANGUARDOPS VALIDADA POR EL MOTOR")

# Ejecutamos la inicialización al cargar el script
init_db()

class LeadBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    source: Optional[str] = "web"

def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

async def create_audit_log(event_type: str, description: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_logs (id, event_type, description) VALUES (%s, %s, %s)",
                    (uuid.uuid4(), event_type, description)
                )
                conn.commit()
    except Exception as e:
        print(f"Error grabando log: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM leads ORDER BY created_at DESC")
                leads = cur.fetchall()
                
                cur.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10")
                logs = cur.fetchall()
                
                total = len(leads)
                contacted = len([l for l in leads if l['status'] == 'contacted'])
                conv_rate = round((contacted / total * 100), 1) if total > 0 else 0
                
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "leads": leads, 
            "logs": logs,
            "stats": {"total": total, "conv_rate": conv_rate, "contacted": contacted}
        })
    except Exception as e:
        print(f"ERROR CRÍTICO DASHBOARD: {e}")
        return HTMLResponse(content=f"<html><body style='background:#050C1F;color:white;font-family:sans-serif;padding:50px;'><h1>🛡️ VanguardOps: Error de Sincronización</h1><p>{e}</p></body></html>", status_code=500)

# ... El resto de tus rutas (POST, PATCH, DELETE) se mantienen igual ...
@app.post("/api/v1/lead-intake", status_code=201)
async def create_lead(lead: LeadBase, background_tasks: BackgroundTasks):
    lead_id = uuid.uuid4()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO leads (id, full_name, email, phone, source, status) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
                (lead_id, lead.full_name, lead.email, lead.phone, lead.source, "new")
            )
            new_lead = cur.fetchone()
            conn.commit()
            background_tasks.add_task(create_audit_log, "LEAD_INGESTED", f"Entity {lead.full_name} breached the wall.")
            return new_lead

@app.patch("/api/v1/leads/{lead_id}/status")
async def update_lead_status(lead_id: uuid.UUID, background_tasks: BackgroundTasks):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE leads SET status = 'contacted' WHERE id = %s RETURNING full_name", (lead_id,))
            res = cur.fetchone()
            if not res: raise HTTPException(status_code=404)
            conn.commit()
            background_tasks.add_task(create_audit_log, "STATUS_UPDATED", f"Lead {res['full_name']} escalated.")
            return {"message": "Updated"}

@app.delete("/api/v1/leads/{lead_id}")
async def delete_lead(lead_id: uuid.UUID, background_tasks: BackgroundTasks):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM leads WHERE id = %s RETURNING full_name", (lead_id,))
            res = cur.fetchone()
            if not res: raise HTTPException(status_code=404)
            conn.commit()
            background_tasks.add_task(create_audit_log, "DATA_PURGE", f"Record {res['full_name']} purged.")
            return {"message": "Deleted"}