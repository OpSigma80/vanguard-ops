import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from dotenv import load_dotenv

from app.domain.models.lead import LeadSource, Lead
from app.application.use_cases.process_lead import ProcessLead
# Importamos las piezas reales de infraestructura
from app.infrastructure.persistence.postgres_lead_repository import PostgresLeadRepository
from app.infrastructure.notifications.mock_notifier import MockNotifier # Seguimos con mock aquí hasta configurar Email

load_dotenv()

# --- Dependency Injection Real ---

async def get_process_lead() -> ProcessLead:
    # 1. Obtenemos la URL de tu .env
    db_url = os.getenv("DATABASE_URL")
    
    # 2. Instanciamos el repositorio real de Postgres
    repo = PostgresLeadRepository(db_url)
    
    # 3. Mantenemos el notifier como mock por ahora (luego pondremos WhatsApp/Email)
    notifier = MockNotifier()
    
    return ProcessLead(repo, notifier)

router = APIRouter()

# --- El resto de tu código se mantiene igual, ¡porque está bien diseñado! ---

class LeadRequest(BaseModel):
    full_name: str = Field(..., min_length=3, example="Jane Doe")
    email: Optional[EmailStr] = Field(None, example="jane@example.com")
    phone: Optional[str] = Field(None, example="+1234567890")
    source: LeadSource = Field(..., example=LeadSource.WEB_FORM)

@router.post("/lead-intake", status_code=201, summary="Receive a new lead")
async def lead_intake(
    payload: LeadRequest,
    use_case: ProcessLead = Depends(get_process_lead)
):
    try:
        # Aquí se ejecuta la magia y se guarda en Postgres
        lead = await use_case.execute(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            source=payload.source
        )
        return {
            "id": lead.id,
            "status": "success",
            "message": f"Welcome message triggered for {lead.full_name}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Imprime el error en consola para que podamos debugear si falla la conexión
        print(f"DEBUG ERROR: {e}") 
        raise HTTPException(status_code=500, detail="Internal Server Error")