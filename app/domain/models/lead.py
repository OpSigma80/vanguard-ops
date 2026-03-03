from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

# --- DOMAIN LAYER ---

class LeadSource(str, Enum):
    WEB_FORM = "web_form"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    OTHER = "other"

class LeadStatus(str, Enum):
    NEW = "new"
    # ... (tus otros estados)

@dataclass(frozen=True)
class Lead:
    id: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    source: LeadSource
    status: LeadStatus
    created_at: datetime

    @classmethod
    def create(cls, full_name: str, source: LeadSource, email: str = None, phone: str = None) -> "Lead":
        # Centralizamos la limpieza aquí
        clean_email = email.strip().lower() if email else None
        clean_phone = phone.strip() if phone else None
        
        return cls(
            id=str(uuid.uuid4()),
            full_name=full_name.strip(),
            email=clean_email,
            phone=clean_phone,
            source=source,
            status=LeadStatus.NEW,
            # Mejor práctica: Siempre con zona horaria (UTC)
            created_at=datetime.now(timezone.utc),
        )

# --- APPLICATION LAYER (Use Cases) ---

class ProcessLead:
    def __init__(self, repo: "LeadRepository", notifier: "NotificationService"):
        self.repo = repo
        self.notifier = notifier

    async def execute(self, **kwargs) -> Lead:
        # 1. Factory
        lead = Lead.create(
            full_name=kwargs.get('full_name'),
            email=kwargs.get('email'),
            phone=kwargs.get('phone'),
            source=kwargs.get('source', LeadSource.OTHER)
        )

        # 2. Validation (Podemos usar Pydantic aquí después)
        # LeadRules.validate(lead) 

        # 3. Check duplicates (Operación de I/O -> Async)
        existing = await self.repo.find_by_email_or_phone(lead.email, lead.phone)
        if existing:
            raise ValueError(f"Lead with contact info already exists.")

        # 4. Persistence
        await self.repo.save(lead)

        # 5. Notification (Fuego y olvido o espera asíncrona)
        # Esto ya no bloquea el motor
        await self.notifier.send_welcome_message(lead)

        return lead