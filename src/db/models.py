from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    age: Mapped[int] = mapped_column(Integer)
    occupation: Mapped[str] = mapped_column(String(50))
    income: Mapped[float] = mapped_column(Float)
    employment_years: Mapped[float] = mapped_column(Float)
    credit_history_years: Mapped[float] = mapped_column(Float)
    num_existing_loans: Mapped[int] = mapped_column(Integer)
    num_credit_inquiries_6m: Mapped[int] = mapped_column(Integer)
    total_debt: Mapped[float] = mapped_column(Float)
    monthly_payment: Mapped[float] = mapped_column(Float)
    credit_utilization: Mapped[float] = mapped_column(Float)
    num_late_payments: Mapped[int] = mapped_column(Integer)
    account_balance: Mapped[float] = mapped_column(Float)
    transaction_intensity: Mapped[float] = mapped_column(Float)
    debt_to_income: Mapped[float] = mapped_column(Float)
    payment_to_income: Mapped[float] = mapped_column(Float)
    ground_truth_default: Mapped[int] = mapped_column(Integer, default=0)

    loans: Mapped[list["Loan"]] = relationship(back_populates="customer")
    credit_history: Mapped[list["CreditHistory"]] = relationship(back_populates="customer")
    transactions: Mapped[list["TransactionMonthly"]] = relationship(back_populates="customer")
    risk_predictions: Mapped[list["RiskPrediction"]] = relationship(back_populates="customer")
    risk_alerts: Mapped[list["RiskAlert"]] = relationship(back_populates="customer")


class Loan(Base):
    __tablename__ = "loans"

    loan_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    loan_amount: Mapped[float] = mapped_column(Float)
    term_months: Mapped[int] = mapped_column(Integer)
    interest_rate: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")

    customer: Mapped["Customer"] = relationship(back_populates="loans")


class CreditHistory(Base):
    __tablename__ = "credit_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    month_index: Mapped[int] = mapped_column(Integer)
    credit_utilization: Mapped[float] = mapped_column(Float)
    account_balance: Mapped[float] = mapped_column(Float)
    cumulative_late_payments: Mapped[int] = mapped_column(Integer)

    customer: Mapped["Customer"] = relationship(back_populates="credit_history")


class TransactionMonthly(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    month_index: Mapped[int] = mapped_column(Integer)
    transaction_count: Mapped[int] = mapped_column(Integer)
    cash_withdrawal_count: Mapped[int] = mapped_column(Integer)

    customer: Mapped["Customer"] = relationship(back_populates="transactions")


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    model_version: Mapped[str] = mapped_column(String(50))
    probability_of_default: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(20))
    decision: Mapped[str] = mapped_column(String(20))
    suggested_interest_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    approved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_risk_drivers: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="risk_predictions")


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    previous_risk_level: Mapped[str] = mapped_column(String(20))
    current_risk_level: Mapped[str] = mapped_column(String(20))
    previous_pd: Mapped[float] = mapped_column(Float)
    current_pd: Mapped[float] = mapped_column(Float)
    signals: Mapped[list] = mapped_column(JSON, default=list)
    recommended_action: Mapped[str] = mapped_column(String(100))
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="risk_alerts")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_name: Mapped[str] = mapped_column(String(50))
    champion_model: Mapped[str] = mapped_column(String(50))
    roc_auc: Mapped[float] = mapped_column(Float)
    pr_auc: Mapped[float] = mapped_column(Float)
    gini: Mapped[float] = mapped_column(Float)
    ks_statistic: Mapped[float] = mapped_column(Float)
    brier_score: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
