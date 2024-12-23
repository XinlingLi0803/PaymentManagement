from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class Payment(BaseModel):
    payee_first_name: str
    payee_last_name: str
    payee_payment_status: str = Field(
        pattern="^(completed|due_now|overdue|pending)$")
    payee_added_date_utc: datetime
    payee_due_date: str  # YYYY-MM-DD
    payee_address_line_1: str
    payee_address_line_2: Optional[str]
    payee_city: str
    payee_country: str  # ISO 3166-1 alpha-2
    payee_province_or_state: Optional[str]
    payee_postal_code: str
    payee_phone_number: str  # E.164 format
    payee_email: EmailStr
    currency: str  # ISO 4217
    discount_percent: Optional[float] = 0
    tax_percent: Optional[float] = 0
    due_amount: float
    total_due: Optional[float] = 0


class PaymentUpdate(BaseModel):
    payee_due_date: Optional[str]
    due_amount: Optional[float]
    payee_payment_status: Optional[str]
