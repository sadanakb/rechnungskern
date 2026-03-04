"""
Pydantic schemas for Quote (Angebot) request/response validation.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class QuoteStatus(str, Enum):
    draft = 'draft'
    sent = 'sent'
    accepted = 'accepted'
    rejected = 'rejected'
    expired = 'expired'
    converted = 'converted'


class QuoteLineItem(BaseModel):
    description: str = Field(..., max_length=1000)
    quantity: Decimal = Field(Decimal('1'), gt=0, le=Decimal('999999'))
    unit_price: Decimal = Field(..., ge=0, le=Decimal('99999999'))
    net_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None


class QuoteCreate(BaseModel):
    quote_date: Optional[date] = None
    valid_until: Optional[date] = None
    seller_name: Optional[str] = Field(None, max_length=500)
    seller_vat_id: Optional[str] = Field(None, max_length=50)
    seller_address: Optional[str] = Field(None, max_length=2000)
    buyer_name: Optional[str] = Field(None, max_length=500)
    buyer_vat_id: Optional[str] = Field(None, max_length=50)
    buyer_address: Optional[str] = Field(None, max_length=2000)
    tax_rate: Optional[Decimal] = Decimal('19.00')
    currency: Optional[str] = Field('EUR', pattern=r'^[A-Z]{3}$')
    line_items: Optional[List[QuoteLineItem]] = None
    intro_text: Optional[str] = Field(None, max_length=5000)
    closing_text: Optional[str] = Field(None, max_length=5000)
    internal_notes: Optional[str] = Field(None, max_length=10000)
    iban: Optional[str] = Field(None, max_length=34)
    bic: Optional[str] = Field(None, max_length=11)
    payment_account_name: Optional[str] = Field(None, max_length=200)


class QuoteUpdate(BaseModel):
    quote_date: Optional[date] = None
    valid_until: Optional[date] = None
    seller_name: Optional[str] = Field(None, max_length=500)
    seller_vat_id: Optional[str] = Field(None, max_length=50)
    seller_address: Optional[str] = Field(None, max_length=2000)
    buyer_name: Optional[str] = Field(None, max_length=500)
    buyer_vat_id: Optional[str] = Field(None, max_length=50)
    buyer_address: Optional[str] = Field(None, max_length=2000)
    tax_rate: Optional[Decimal] = None
    currency: Optional[str] = Field(None, pattern=r'^[A-Z]{3}$')
    line_items: Optional[List[QuoteLineItem]] = None
    intro_text: Optional[str] = Field(None, max_length=5000)
    closing_text: Optional[str] = Field(None, max_length=5000)
    internal_notes: Optional[str] = Field(None, max_length=10000)
    iban: Optional[str] = Field(None, max_length=34)
    bic: Optional[str] = Field(None, max_length=11)
    payment_account_name: Optional[str] = Field(None, max_length=200)


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
    converted_invoice_id: Optional[int] = None
    organization_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QuoteListResponse(BaseModel):
    quotes: List[QuoteResponse]
    total: int
