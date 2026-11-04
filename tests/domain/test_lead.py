import pytest

from app.domain.models.lead import Lead, LeadSource
from app.domain.services.lead_rules import LeadRules


def test_lead_model_validation():
    lead = Lead.create(
        full_name="  Israel Pro  ",
        email="  ISRAEL@PRO.COM ",
        phone=" 555-123 ",
        source=LeadSource.WEB_FORM,
    )
    assert lead.full_name == "Israel Pro"
    assert lead.email == "israel@pro.com"
    assert lead.phone == "555-123"


def test_lead_model_empty_name():
    lead = Lead.create(
        full_name="A",
        email="test@test.com",
        source=LeadSource.WEB_FORM,
    )
    with pytest.raises(ValueError, match="too short"):
        LeadRules.full_name_is_valid(lead)
