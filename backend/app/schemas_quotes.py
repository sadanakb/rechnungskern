"""
Pydantic schemas for Quote (Angebot) request/response validation.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class QuoteLineItem(BaseModel):
    description: str
    quantity: Decimal = Decimal('1')
    unit_price: Decimal
    net_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None


class QuoteCreate(BaseModel):
    quote_date: Optional[date] = None
    valid_until: Optional[date] = None
    seller_name: Optional[str] = None
    seller_vat_id: Optional[str] = None
    seller_address: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_vat_id: Optional[str] = None
    buyer_address: Optional[str] = None
    tax_rate: Optional[Decimal] = Decimal('19.00')
    currency: Optional[str] = 'EUR'
    line_items: Optional[List[QuoteLineItem]] = None
    intro_text: Optional[str] = None
    closing_text: Optional[str] = None
    internal_notes: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    payment_account_name: Optional[str] = None


class QuoteUpdate(QuoteCreate):
    status: Optional[str] = None


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quote_id: str
    quote_number: Optional[str] = None
    status: str
    quote_date: Optional[date] = None
    valid_until: Optional[date] = None
    buyer_name: Optional[str] = None
    net_amount: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    currency: Optional[str] = 'EUR'
    created_at: Optional[datetime] = None


class QuoteDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quote_id: str
    quote_number: Optional[str] = None
    status: str
    quote_date: Optional[date] = None
    valid_until: Optional[date] = None
    seller_name: Optional[str] = None
    seller_vat_id: Optional[str] = None
    seller_address: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_vat_id: Optional[str] = None
    buyer_address: Optional[str] = None
    net_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    currency: Optional[str] = 'EUR'
    line_items: Optional[list] = None
    intro_text: Optional[str] = None
    closing_text: Optional[str] = None
    internal_notes: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    payment_account_name: Optional[str] = None
    pdf_path: Optional[str] = None
    converted_invoice_id: Optional[int] = None
    organization_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QuoteListResponse(BaseModel):
    quotes: List[QuoteResponse]
    total: int
