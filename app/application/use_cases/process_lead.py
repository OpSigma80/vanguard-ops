from app.domain.models.lead import Lead
from app.domain.services.lead_rules import LeadRules
from app.application.ports.lead_repository import LeadRepository
from app.application.ports.notification_service import NotificationService
from typing import Optional

class ProcessLead:

    def __init__(self, repo: LeadRepository, notifier: NotificationService):
        self.repo = repo
        self.notifier = notifier

    # 1️⃣ Agregamos 'async' aquí
    async def execute(self,
        *,
        full_name: str,
        email: Optional[str],
        phone: Optional[str],
        source: str
    ) -> Lead:

        # 2️⃣ Create Lead (Sigue siendo sincrónico, es solo lógica)
        lead = Lead.create(
            full_name=full_name,
            email=email,
            phone=phone,
            source=source
        )

        # 3️⃣ Validate business rules
        LeadRules.must_have_contact_method(lead)
        LeadRules.full_name_is_valid(lead)

        # 4️⃣ Check duplicates (Llamada asíncrona a la DB)
        existing = await self.repo.find_by_email_or_phone(lead.email, lead.phone)
        if existing:
            raise ValueError("Lead already exists.")

        # 5️⃣ Persist lead (Agregamos 'await' porque guardar en Postgres toma tiempo)
        await self.repo.save(lead)

        # 6️⃣ Send notification (Agregamos 'await')
        await self.notifier.send_welcome_message(lead)

        return lead