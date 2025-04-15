from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field
from rest_framework.serializers import (
    CharField,
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
    page: Annotated[int, Field(ge=1, description="Número da página")] = 1
    limit: Annotated[int, Field(ge=1, description="Quantidade de itens por página")] = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginationQueryParamsSerializer(Serializer):
    page = IntegerField(min_value=1, default=1, help_text="Page number")
    limit = IntegerField(min_value=1, default=10, help_text="Items per page")


# create_loan_request
class PaymentResponseSerializer(Serializer):
    id = UUIDField()
    loan = UUIDField()
    payment_date = DateTimeField()
    amount = DecimalField(max_digits=10, decimal_places=2)


class CreateLoanRequestSerializer(Serializer):
    amount = DecimalField(max_digits=10, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    bank = CharField(max_length=255)
    client_name = CharField(max_length=255)


class CreateLoanRequestModel(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
    interest_rate: Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]
    bank: Annotated[str, Field(max_length=255, min_length=1)]
    client_name: Annotated[str, Field(max_length=255, min_length=1)]

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid"
    }

class CreateLoanResponseSerializer(Serializer):
    id = UUIDField()
    client = PrimaryKeyRelatedField(read_only=True)
    amount = DecimalField(max_digits=10, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    ip_address = IPAddressField()
    request_date = DateTimeField()
    bank = CharField()
    client_name = CharField()
    payments = PaymentResponseSerializer(many=True)
    remaining_balance = DecimalField(max_digits=10, decimal_places=2)

# list_loans_route
class ListLoansQueryParamsSerializer(PaginationQueryParamsSerializer):
    ...

class ListLoansQueryParams(PaginationQueryParams):
    ...

class ListLoansResponse(Serializer):
    id = UUIDField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    bank = CharField()
    request_date = DateTimeField()
