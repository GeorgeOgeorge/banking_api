import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from rest_framework.serializers import (
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    IntegerField,
    IPAddressField,
    PrimaryKeyRelatedField,
    Serializer,
    UUIDField
)


# generics
class PaginationQueryParams(BaseModel):
    page: Annotated[int, Field(ge=1, description='Page number')] = 1
    limit: Annotated[int, Field(ge=1, description='Items per page')] = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginationQueryParamsSerializer(Serializer):
    page = IntegerField(min_value=1, default=1, help_text='Page number')
    limit = IntegerField(min_value=1, default=10, help_text='Items per page')


# create_loan_request
class PaymentResponseSerializer(Serializer):
    id = UUIDField()
    loan = UUIDField()
    payment_date = DateTimeField()
    amount = DecimalField(max_digits=10, decimal_places=2)


class CreateLoanRequestSerializer(Serializer):
    amount = DecimalField(max_digits=10, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    bank_id = UUIDField()
    client_name = CharField(max_length=255)


class CreateLoanRequestModel(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
    interest_rate: Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]
    bank_id: UUID
    client_name: Annotated[str, Field(max_length=255, min_length=1)]

    model_config = {
        'str_strip_whitespace': True,
        'extra': 'forbid'
    }

class CreateLoanResponseSerializer(Serializer):
    id = UUIDField()
    client = PrimaryKeyRelatedField(read_only=True)
    amount = DecimalField(max_digits=10, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    ip_address = IPAddressField()
    request_date = DateTimeField()
    bank_id = UUIDField()
    client_name = CharField()
    payments = PaymentResponseSerializer(many=True)
    remaining_balance = DecimalField(max_digits=10, decimal_places=2)

# list_loans_route
class ListLoansQueryParamsSerializer(PaginationQueryParamsSerializer):
    ...

class ListLoansQueryParams(PaginationQueryParams):

    model_config = {
        'str_strip_whitespace': True,
        'extra': 'forbid'
    }

class ListLoansResponse(Serializer):
    id = UUIDField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    bank_name = CharField()
    request_date = DateTimeField()

# create_payment_route
class CreatePaymentRequestSerializer(Serializer):
    loan = UUIDField()
    amount = DecimalField(max_digits=10, decimal_places=2)


class CreatePaymentRequestModel(BaseModel):
    loan_id: UUID
    amount: float

    model_config = {
        'str_strip_whitespace': True,
        'extra': 'forbid'
    }


class CreatePaymentResponse(Serializer):
    id = UUIDField()
    payment_date = DateTimeField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    loan_id = UUIDField()

# list_payments_route
class ListPaymentsQueryParams(PaginationQueryParams):
    payment_id: UUID | None = None
    loan_id: UUID | None = None
    payment_date: date | None = None

    model_config = {
        'str_strip_whitespace': True,
        'extra': 'forbid'
    }

    @field_validator('payment_date', mode='before')
    @classmethod
    def validate_date_format(cls, date_str: str) -> str | None:
        valid_format = r'^\d{4}-\d{2}-\d{2}$'

        if isinstance(date_str, str) and not re.match(valid_format, date_str):
            raise ValueError('payment_date must be in format YYYY-MM-DD')

        return date_str


class ListPaymentsQueryParamsSerializer(PaginationQueryParamsSerializer):
    payment_id = UUIDField(required=False, default=None, allow_null=True)
    loan_id = UUIDField(required=False, default=None, allow_null=True)
    payment_date = DateField(required=False, default=None, allow_null=True, format='%Y-%m-%d')

# list_loan_balance_route
class LoanBalanceResponse(Serializer):
    id = UUIDField()
    bank_name = CharField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    interest_rate = DecimalField(max_digits=10, decimal_places=2)
    request_date = DateField()
    total_paid = DecimalField(max_digits=10, decimal_places=2)
    remaining_debt = DecimalField(max_digits=10, decimal_places=2)

# create_bank_route
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


class CreateBankSerializer(Serializer):
    name = CharField(max_length=100)
    bic = CharField(max_length=20, allow_blank=True, required=False)
    country = CharField(max_length=50)
    interest_policy = CharField(max_length=100, allow_blank=True, required=False)
    max_loan_amount = DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0'), required=False
    )


class CreateBankResponse(CreateBankSerializer):
    id = UUIDField()
