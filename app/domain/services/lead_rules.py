from app.domain.models.lead import Lead


class LeadRules:

    @staticmethod
    def must_have_contact_method(lead: Lead) -> None:
        if not lead.email and not lead.phone:
            raise ValueError("Lead must have at least email or phone.")

    @staticmethod
    def full_name_is_valid(lead: Lead) -> None:
        if len(lead.full_name) < 3:
            raise ValueError("Lead full name is too short.")
