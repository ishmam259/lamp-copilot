from typing import Literal

from .common import ISODate, Model

CaptureKind = Literal["invoice", "sales_page"]


class ExtractionLine(Model):
    product: str
    strength: str | None = None
    pack: str | None = None
    batch_no: str
    expiry_date: ISODate
    qty: int
    unit_cost: float
    line_total: float


class ExtractedInvoice(Model):
    supplier_name: str
    invoice_no: str
    invoice_date: ISODate
    due_date: ISODate
    total: float
    lines: list[ExtractionLine]


class SalesDay(Model):
    date: ISODate
    cash_sales: float
    credit_sales: float
    dues_collected: float
    expenses: float


class ExtractedSalesPage(Model):
    days: list[SalesDay]


class Check(Model):
    name: str
    passed: bool
    detail: str


class ExtractionResult(Model):
    kind: CaptureKind
    invoice: ExtractedInvoice | None = None
    sales_page: ExtractedSalesPage | None = None
    field_confidence: dict[str, float] = {}
    checks: list[Check] = []
    suspicious_text: list[str] = []
    model: str
    prompt_version: str
    mode: Literal["live", "replay"]


class CaptureOut(Model):
    id: str
    kind: CaptureKind
    status: Literal["needs_review", "confirmed"]
    image_url: str | None = None
    extraction: ExtractionResult


class CaptureConfirm(Model):
    """Owner-corrected draft. Send the part that matches the capture kind."""

    invoice: ExtractedInvoice | None = None
    sales_page: ExtractedSalesPage | None = None
