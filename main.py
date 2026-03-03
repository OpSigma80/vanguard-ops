import os
import time
import psycopg
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

# Configuración de carga: Se busca el .env en la raíz del proyecto
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="VanguardOps - Automation Engine")
templates = Jinja2Templates(directory="templates")

class Lead(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    source: str

def init_db():
    """Inicializa la infraestructura de la base de datos"""
    retries = 20
    while retries > 0:
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    # Crear tabla de Leads
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS leads (
                            id SERIAL PRIMARY KEY,
                            full_name TEXT NOT NULL,
                            email TEXT NOT NULL,
                            phone TEXT,
                            source TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    # Crear tabla de Logs de Auditoría
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS audit_logs (
                            id SERIAL PRIMARY KEY,
                            action TEXT NOT NULL,
                            details TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                print("✅ [VanguardOps] Infrastructure Synced: Tables Ready.")
                return
        except Exception as e:
            retries -= 1
            print(f"⚠️ [VanguardOps] DB not ready... Retrying in 5s ({retries} attempts left)")
            time.sleep(5)
    exit(1)

# Ejecutar inicialización al arrancar
init_db()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Renderiza el Dashboard con datos reales de la DB"""
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # 1. Obtener TOTAL real de leads para el contador
                cur.execute("SELECT COUNT(*) FROM leads")
                total_count = cur.fetchone()[0]
                
                # 2. Obtener los últimos 10 Leads para la tabla
                cur.execute("SELECT id, full_name, email, phone, source, created_at FROM leads ORDER BY created_at DESC LIMIT 10")
                leads = cur.fetchall()
                
                # 3. Obtener los últimos 10 Logs del sistema
                cur.execute("SELECT id, action, details, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10")
                logs = cur.fetchall()
                
                stats = {
                    "total_leads": total_count,
                    "active_nodes": 1,
                    "system_status": "Operational",
                    "uptime": "99.9%"
                }
                
                return templates.TemplateResponse("index.html", {
                    "request": request,
                    "leads": leads,
                    "logs": logs,
                    "stats": stats,
                    "status": "Online",
                    "version": "v1.0.4-stable",
                    "creator": "Israel Rovira"
                })
    except Exception as e:
        return HTMLResponse(content=f"🛡️ VanguardOps Error: {e}", status_code=500)

@app.post("/api/v1/lead-intake")
async def lead_intake(lead: Lead):
    """Endpoint para procesar nuevos leads"""
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Insertar Lead
                cur.execute(
                    "INSERT INTO leads (full_name, email, phone, source) VALUES (%s, %s, %s, %s) RETURNING id",
                    (lead.full_name, lead.email, lead.phone, lead.source)
                )
                lead_id = cur.fetchone()[0]
                
                # Registrar en Logs
                cur.execute(
                    "INSERT INTO audit_logs (action, details) VALUES (%s, %s)",
                    ("LEAD_INGESTED", f"New lead registered: {lead.email}")
                )
                conn.commit()
                return {"status": "success", "lead_id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))