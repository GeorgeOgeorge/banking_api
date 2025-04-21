import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DecimalField,
    IntegerField,
    Serializer,
    UUIDField,
)


####################################### generics #######################################
class PaginationQueryParams(BaseModel):
    page: Annotated[int, Field(ge=1, description='Page number')] = 1
    limit: Annotated[int, Field(ge=1, description='Items per page')] = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginationQueryParamsSerializer(Serializer):
    page = IntegerField(min_value=1, default=1, help_text='Page number')
    limit = IntegerField(min_value=1, default=10, help_text='Items per page')


####################################### create_loan_request #######################################
class LoanInstallment(Serializer):
    id = UUIDField(help_text='Unique identifier for the installment.')
    due_date = DateTimeField(help_text='Due date for the installment.')
    amount = DecimalField(max_digits=12, decimal_places=2, help_text='Amount to be paid for this installment.')

class CreateLoanRequest(Serializer):
    amount = DecimalField(max_digits=12, decimal_places=2, help_text='The principal loan amount requested.')
    interest_rate = DecimalField(max_digits=5, decimal_places=2, help_text='Monthly interest rate (%) to apply to the loan.')
    installments_qt = IntegerField(min_value=1, help_text='Number of monthly installments for the loan.')
    bank_id = UUIDField(help_text='Identifier of the bank where the loan is being requested.')

class CreateLoanModel(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    interest_rate: Annotated[Decimal, Field(gt=0, max_digits=5, decimal_places=2)]
    installments_qt: Annotated[int, Field(gt=0)]
    bank_id: UUID

    model_config = {
        'str_strip_whitespace': True,
        'extra': 'forbid'
    }

class CreateLoanResponse(Serializer):
    id = UUIDField(help_text='Unique identifier for the created loan.')
    amount = DecimalField(max_digits=12, decimal_places=2, help_text='Loan amount that was approved.')
    interest_rate = DecimalField(max_digits=5, decimal_places=2, help_text='Interest rate (%) applied to the loan.')
    request_date = DateTimeField(help_text='Timestamp when the loan was requested.')
    bank_name = CharField(help_text='Name of the bank that issued the loan.')
    loan_installments = LoanInstallment(many=True, help_text='List of generated loan installments.')


####################################### create_payment_route #######################################
class CreatePaymentSerializer(Serializer):
    loan_id = UUIDField(help_text='Loan ID to which the payment will be applied.')
    amount = DecimalField(min_value=1, max_digits=10, decimal_places=2, help_text='Amount to pay toward the loan (must be at least 1).')

class CreatePaymentModel(BaseModel):
    loan_id: UUID
    amount: float

    model_config = {
        'str_strip_whitespace': True,
        'extra': 'forbid'
    }

class CreatePaymentResponse(Serializer):
    id = UUIDField(help_text='Unique identifier for the created payment.')
    payment_date = DateTimeField(help_text='Timestamp when the payment was recorded.')
    amount = DecimalField(max_digits=10, decimal_places=2, help_text='Amount that was actually applied to the installment.')
    change = DecimalField(max_digits=10, decimal_places=2, help_text='Amount returned as change.')


####################################### list_loans_route #######################################
class ListLoansQueryParamsSerializer(PaginationQueryParamsSerializer):
    paid = BooleanField(required=False, help_text='Indicates whether the loan is paid (true) or not (false).')
    interest_rate = DecimalField(max_digits=10, decimal_places=2, required=False, help_text='Interest rate requested for the loan.')
    amount = DecimalField(max_digits=10, decimal_places=2, required=False, help_text='Amount requested as loan.')
    bank_name = CharField(required=False, allow_blank=True, help_text='Name of the bank that granted the loan.')
    request_date = DateField(required=False, help_text='Date the loan was requested.')

class ListLoansQueryParams(PaginationQueryParams):
    paid: bool | None = None
    interest_rate: float | None = None
    amount: float | None = None
    bank_name: str | None = None
    request_date: date | None = None

    model_config = {
        'str_strip_whitespace': True,
    }

class LoanInstallmentResponse(Serializer):
    paid_amount = DecimalField(max_digits=10, decimal_places=2, help_text='Amount already paid for the installment.')
    status = ChoiceField(choices=['pending', 'paid', 'overdue'], help_text='Current status of the installment.')

class ListLoansResponse(Serializer):
    id = UUIDField(help_text='Unique identifier of the loan.')
    amount = DecimalField(max_digits=10, decimal_places=2, help_text='Total amount granted for the loan.')
    interest_rate = DecimalField(max_digits=5, decimal_places=2, help_text='Interest rate applied to the loan.')
    bank_name = CharField(help_text='Name of the bank that granted the loan.')
    request_date = DateTimeField(help_text='Date and time when the loan was requested.')
    outstanding_balance = DecimalField(max_digits=10, decimal_places=2, help_text='Amount to be paid on the loan.')
    loan_installments = LoanInstallmentResponse(many=True, help_text='List of loan installments.')


####################################### list_payments_route #######################################
class ListPaymentsQueryParams(PaginationQueryParams):
    payment_id: UUID | None = None
    loan_id: UUID | None = None
    payment_date: date | None = None

    model_config = {
        'str_strip_whitespace': True,
    }

    @field_validator('payment_date', mode='before')
    @classmethod
    def validate_date_format(cls, date_str: str) -> str | None:
        valid_format = r'^\d{4}-\d{2}-\d{2}$'

        if isinstance(date_str, str) and not re.match(valid_format, date_str):
            raise ValueError('payment_date must be in format YYYY-MM-DD')

        return date_str

class ListPaymentsQueryParamsSerializer(PaginationQueryParamsSerializer):
    payment_id = UUIDField(required=False, default=None, allow_null=True, help_text="Filter payments by payment unique identifier.")
    loan_id = UUIDField(required=False, default=None, allow_null=True, help_text="Filter payments by associated loan identifier.")
    payment_date = DateField(required=False, default=None, allow_null=True, format='%Y-%m-%d', help_text="Filter payments by specific date in format YYYY-MM-DD.")

class ListPaymentsResponse(CreatePaymentResponse):
    loan_installment_id = UUIDField(help_text='Loan installment associated with the payment.')
    bank_name = CharField(help_text='Name of the bank that granted the loan.')
    loan_id = UUIDField(help_text='Loan associated with the payment.')


####################################### loan_statistics_route #######################################
class LoanStatisticsResponse(Serializer):
    id = UUIDField(help_text="Unique identifier of the loan.")
    amount = DecimalField(max_digits=10, decimal_places=2, help_text="Total amount granted for the loan.")
    interest_rate = DecimalField(max_digits=5, decimal_places=2, help_text="Interest rate applied to the loan.")
    paid = BooleanField(help_text="Indicates whether the loan is fully paid.")
    bank_name = CharField(help_text="Name of the bank that granted the loan.")
    installments_count = IntegerField(help_text="Total number of installments associated with the loan.")
    paid_installments = IntegerField(help_text="Number of installments that have been paid.")
    pending_installments = IntegerField(help_text="Number of installments that are still pending.")
    overdue_installments = IntegerField(help_text="Number of installments that are overdue.")
    total_paid = DecimalField(max_digits=12, decimal_places=2, help_text="Total amount that has been paid.")
    outstanding_balance = DecimalField(max_digits=12, decimal_places=2, help_text="Remaining balance to be paid on the loan.")
    total_pending = DecimalField(max_digits=12, decimal_places=2, help_text="Total amount pending across all pending installments.")
    total_overdue = DecimalField(max_digits=12, decimal_places=2, help_text="Total overdue amount across all overdue installments.")


####################################### create_bank_route #######################################
class CreateBankModel(BaseModel):
    name: Annotated[str, Field(max_length=100)]
    bic: Optional[Annotated[str, Field(max_length=20)]] = None
    country: Annotated[str, Field(max_length=50)]
    interest_policy: Optional[Annotated[str, Field(max_length=100)]] = None
    max_loan_amount: Annotated[Decimal, Field(default=0, max_digits=12, decimal_places=2)]

    model_config = {
        'str_strip_whitespace': True,
        'extra': 'forbid'
    }

class CreateBankRequest(Serializer):
    name = CharField(max_length=100, help_text='Name of the bank.')
    bic = CharField(max_length=20, allow_blank=True, required=False, help_text='Bank Identifier Code (optional).')
    country = CharField(max_length=50, help_text='Country where the bank operates.')
    interest_policy = CharField(max_length=100, allow_blank=True, required=False, help_text='Description of the banks interest policy (optional).')
    max_loan_amount = DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'), required=False, help_text='Maximum loan amount the bank allows. Defaults to 0 if not provided.')

class CreateBankResponse(CreateBankRequest):
    id = UUIDField(help_text='Unique identifier of the created bank.')
