from main import LeadBase
import pytest

def test_lead_model_validation():
    # Verificamos que Pydantic acepte datos correctos
    lead = LeadBase(full_name="Israel Pro", email="israel@pro.com")
    assert lead.full_name == "Israel Pro"

def test_lead_model_empty_name():
    # Verificamos que falle si falta el nombre
    with pytest.raises(ValueError):
        LeadBase(email="test@test.com") # Falta full_name