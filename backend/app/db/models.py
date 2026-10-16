"""Database tables (docs/PLAN.md section 5).

Portable SQLAlchemy 2.0 models: PostgreSQL in Docker, SQLite in tests.
Money is stored as Float in whole or 2-decimal BDT; engines round outputs to 2 decimals.
"""

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Pharmacy(Base):
    __tablename__ = "pharmacy"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    city: Mapped[str]
    cash_on_hand: Mapped[float] = mapped_column(Float, default=0)  # at the start of settings.as_of_date
    settings: Mapped[dict] = mapped_column(JSON)


class Supplier(Base):
    __tablename__ = "supplier"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    name: Mapped[str]
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    return_cutoff_days: Mapped[int] = mapped_column(Integer, default=30)


class Invoice(Base):
    __tablename__ = "invoice"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("supplier.id"))
    invoice_no: Mapped[str]
    invoice_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    total: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="unpaid")  # unpaid | paid
    supplier_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    capture_id: Mapped[str | None] = mapped_column(String, nullable=True)
    supplier: Mapped[Supplier] = relationship()
    lines: Mapped[list["InvoiceLine"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_line"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice.id"))
    product: Mapped[str]
    strength: Mapped[str | None] = mapped_column(String, nullable=True)
    pack: Mapped[str | None] = mapped_column(String, nullable=True)
    batch_no: Mapped[str]
    expiry_date: Mapped[date] = mapped_column(Date)
    qty: Mapped[int]
    unit_cost: Mapped[float] = mapped_column(Float)
    line_total: Mapped[float] = mapped_column(Float)
    invoice: Mapped[Invoice] = relationship(back_populates="lines")


class Payment(Base):
    __tablename__ = "payment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice.id"))
    amount: Mapped[float] = mapped_column(Float)
    paid_on: Mapped[date] = mapped_column(Date)
    invoice: Mapped[Invoice] = relationship(back_populates="payments")


class SalesDay(Base):
    __tablename__ = "sales_day"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    date: Mapped[date] = mapped_column(Date)
    cash_sales: Mapped[float] = mapped_column(Float, default=0)
    credit_sales: Mapped[float] = mapped_column(Float, default=0)
    dues_collected: Mapped[float] = mapped_column(Float, default=0)
    expenses: Mapped[float] = mapped_column(Float, default=0)


class PatientDue(Base):
    """Amounts only, under an alias. Never medicine names."""

    __tablename__ = "patient_dues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    label: Mapped[str]
    amount: Mapped[float] = mapped_column(Float)
    since: Mapped[date] = mapped_column(Date)


class ExpenseSchedule(Base):
    __tablename__ = "expense_schedule"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    category: Mapped[str]
    amount: Mapped[float] = mapped_column(Float)
    day_of_month: Mapped[int]


class StockBatch(Base):
    __tablename__ = "stock_batch"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("supplier.id"))
    product: Mapped[str]
    batch_no: Mapped[str]
    expiry_date: Mapped[date] = mapped_column(Date)
    qty: Mapped[int]
    unit_cost: Mapped[float] = mapped_column(Float)
    supplier: Mapped[Supplier] = relationship()


class PlannedOrder(Base):
    __tablename__ = "planned_order"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("supplier.id"))
    ref: Mapped[str]
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default="planned")  # planned | paid | cancelled
    supplier: Mapped[Supplier] = relationship()
    lines: Mapped[list["PlannedOrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    @property
    def total(self) -> float:
        return sum(l.qty * l.unit_cost for l in self.lines)


class PlannedOrderLine(Base):
    __tablename__ = "planned_order_line"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("planned_order.id"))
    product: Mapped[str]
    qty: Mapped[int]
    unit_cost: Mapped[float] = mapped_column(Float)
    expiry_date: Mapped[date] = mapped_column(Date)
    order: Mapped[PlannedOrder] = relationship(back_populates="lines")


class Lender(Base):
    __tablename__ = "lender"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    kind: Mapped[str]
    products: Mapped[list["LenderProduct"]] = relationship(back_populates="lender", cascade="all, delete-orphan")


class LenderProduct(Base):
    __tablename__ = "lender_product"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lender_id: Mapped[str] = mapped_column(ForeignKey("lender.id"))
    key: Mapped[str]
    label: Mapped[str]
    apr_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    fee_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_amount: Mapped[float] = mapped_column(Float)
    max_amount: Mapped[float] = mapped_column(Float)
    tenor_days: Mapped[int]
    min_history_invoices: Mapped[int] = mapped_column(Integer, default=0)
    min_history_months: Mapped[int] = mapped_column(Integer, default=0)
    cost_bearer: Mapped[str] = mapped_column(String, default="pharmacy")
    lender: Mapped[Lender] = relationship(back_populates="products")


class Capture(Base):
    __tablename__ = "capture"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    kind: Mapped[str]
    status: Mapped[str] = mapped_column(String, default="needs_review")
    extraction: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


# Used from F4/F5 on (consents, lender applications, registry, actions, audit log).

class Consent(Base):
    __tablename__ = "consent"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    lender_id: Mapped[str] = mapped_column(ForeignKey("lender.id"))
    scopes: Mapped[list] = mapped_column(JSON)
    granted_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Application(Base):
    __tablename__ = "application"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    lender_id: Mapped[str] = mapped_column(ForeignKey("lender.id"))
    product_key: Mapped[str]
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="pending")
    decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class RegistryLock(Base):
    __tablename__ = "registry_lock"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commitment: Mapped[str] = mapped_column(String, unique=True)
    application_id: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Action(Base):
    __tablename__ = "action"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    pharmacy_id: Mapped[str] = mapped_column(ForeignKey("pharmacy.id"))
    kind: Mapped[str]
    status: Mapped[str] = mapped_column(String, default="proposed")
    payload: Mapped[dict] = mapped_column(JSON)
    proposed_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime)
    tier: Mapped[str]
    component: Mapped[str]
    event: Mapped[str]
    data: Mapped[dict] = mapped_column(JSON)
