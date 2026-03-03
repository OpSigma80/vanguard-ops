from abc import ABC, abstractmethod
from app.domain.models.lead import Lead

class NotificationService(ABC):

    @abstractmethod
    def send_welcome_message(self, lead: Lead) -> None:
        """Send a welcome message (email, WhatsApp, etc.)"""
        pass
