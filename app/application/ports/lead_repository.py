from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models.lead import Lead

class LeadRepository(ABC):
    @abstractmethod
    async def save(self, lead: Lead) -> None:
        pass

    @abstractmethod
    async def find_by_email_or_phone(self, email: Optional[str], phone: Optional[str]) -> Optional[Lead]:
        pass