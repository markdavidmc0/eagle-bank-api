import pytest
import schemathesis

from app.main import app  # Import your FastAPI app instance

# Load your original starter spec file directly
schema = schemathesis.openapi.from_path("./openapi.yaml")

# Tell Schemathesis to run validation checks directly against your ASGI app
@schema.parametrize()
def test_fastapi_contract(case):
    response = case.call(app=app)
    case.validate_response(response)
