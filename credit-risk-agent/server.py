import logging
from datetime import datetime
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from logic import assess_credit_risk, extract_risk_category, extract_approval_status, extract_loan_amount

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Credit Risk Assessment API",
    description="Assess credit risk using applicant profile, historical credit data, and pre-indexed financial documents.",
    version="1.0.0"
)


# ============================================================================
# REQUEST MODEL
# ============================================================================
class ApplicantProfile(BaseModel):
    model_config = {"json_schema_extra": {"example": {
        "customer_id": "C002",
        "gender": "Male",
        "age": 45,
        "monthly_income_rs": 50000,
        "income_stability": "Medium",
        "profession": "Manager",
        "employment_type": "Permanent",
        "location": "Semi-Urban",
        "loan_request_rs": 500000,
        "current_loan_expenses_rs": 10000,
        "house_ownership": "No",
        "car_ownership": "No",
        "dependents": 2,
        "credit_score": 750,
        "defaults": 0,
        "active_credit_card": "No",
        "property_location": "Rural",
        "co_applicant": "Yes",
        "property_price": 100000,
    }}}

    customer_id: str = Field(..., description="Unique customer identifier, e.g. C001")
    gender: Literal["Male", "Female"]
    age: int = Field(..., ge=18, le=75)
    monthly_income_rs: int = Field(..., ge=0, description="Monthly income in RS")
    income_stability: Literal["Low", "Medium", "High"]
    profession: str = Field(..., description="Applicant's profession")
    employment_type: Literal[
        "Unemployed", "Self-Employed", "Casual", "Contractual",
        "Permanent", "Part-time", "Seasonal", "Freelance",
        "Full-time", "Internship", "Apprentice", "Not Specified"
    ]
    location: Literal["Urban", "Semi-Urban", "Rural"]
    loan_request_rs: int = Field(..., ge=0, description="Requested loan amount in RS")
    current_loan_expenses_rs: int = Field(..., ge=0, description="Current loan EMI/expenses in RS")
    house_ownership: Literal["No", "Yes"]
    car_ownership: Literal["No", "Yes"]
    dependents: int = Field(..., ge=0, le=5)
    credit_score: int = Field(..., ge=500, le=900)
    defaults: int = Field(..., ge=0, le=6)
    active_credit_card: Literal["No", "Yes"]
    property_location: Literal["Urban", "Semi-Urban", "Rural"]
    co_applicant: Literal["No", "Yes"]
    property_price: int = Field(..., ge=0, description="Property price in RS")


# ============================================================================
# RESPONSE MODEL
# ============================================================================
class AssessmentResponse(BaseModel):
    customer_id: str
    approval_status: str
    risk_category: str
    loan_sanction_amount: str
    reasoning: str
    timestamp: str


# ============================================================================
# ENDPOINT
# ============================================================================
@app.post("/assess", response_model=AssessmentResponse)
def assess(profile: ApplicantProfile):
    """
    Submit an applicant profile for credit risk assessment.

    - **customer_id**: included in the JSON body
    - Financial documents must already be indexed in Pinecone for this customer_id.
    """
    customer_id = profile.customer_id
    logger.info(f"Received assessment request for customer_id={customer_id}")

    profile_dict = {
        "customer_id": customer_id,
        "gender": profile.gender,
        "age": profile.age,
        "monthly_income_rs": profile.monthly_income_rs,
        "income_stability": profile.income_stability,
        "profession": profile.profession,
        "employment_type": profile.employment_type,
        "location": profile.location,
        "loan_request_rs": profile.loan_request_rs,
        "current_loan_expenses_rs": profile.current_loan_expenses_rs,
        "house_ownership": profile.house_ownership,
        "car_ownership": profile.car_ownership,
        "dependents": profile.dependents,
        "credit_score": profile.credit_score,
        "defaults": profile.defaults,
        "active_credit_card": profile.active_credit_card,
        "property_location": profile.property_location,
        "co_applicant": profile.co_applicant,
        "property_price": profile.property_price,
    }

    profile_text = "\n".join(f"{k}: {v}" for k, v in profile_dict.items())

    try:
        decision_text = assess_credit_risk(
            customer_id,
            profile_text,
            uploaded_files=None
        )
    except Exception as e:
        logger.error(f"Assessment failed for {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

    return AssessmentResponse(
        customer_id=customer_id,
        approval_status=extract_approval_status(decision_text),
        risk_category=extract_risk_category(decision_text),
        loan_sanction_amount=extract_loan_amount(decision_text),
        reasoning=decision_text,
        timestamp=datetime.utcnow().isoformat(),
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================
@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    print("Starting Credit Risk Agent Server on http://0.0.0.0:8101")
    uvicorn.run(app, host="0.0.0.0", port=8101, log_level="info")