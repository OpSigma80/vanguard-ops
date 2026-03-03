import psycopg
from typing import Optional
from app.domain.models.lead import Lead
from app.application.ports.lead_repository import LeadRepository

class PostgresLeadRepository(LeadRepository):
    def __init__(self, connection_string: str):
        self.conn_info = connection_string

    async def save(self, lead: Lead) -> None:
        # Abrimos conexión asíncrona
        async with await psycopg.AsyncConnection.connect(self.conn_info) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO leads (id, full_name, email, phone, source, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        lead.id, lead.full_name, lead.email, 
                        lead.phone, lead.source.value, 
                        lead.status.value, lead.created_at
                    )
                )

    async def find_by_email_or_phone(self, email: Optional[str], phone: Optional[str]) -> Optional[bool]:
        async with await psycopg.AsyncConnection.connect(self.conn_info) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT 1 FROM leads WHERE email = %s OR phone = %s LIMIT 1",
                    (email, phone)
                )
                return await cur.fetchone() is not None