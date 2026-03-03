from app.application.ports.notification_service import NotificationService
from app.domain.models.lead import Lead

class MockNotifier(NotificationService):
    async def send_welcome_message(self, lead: Lead) -> None:
        print(f"[MOCK NOTIFIER] Enviando mensaje de bienvenida a: {lead.full_name}")