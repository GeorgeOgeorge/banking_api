from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field
from rest_framework import serializers


class PaymentResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    loan = serializers.UUIDField()
    payment_date = serializers.DateTimeField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreateLoanRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    bank = serializers.CharField(max_length=255)
    client_name = serializers.CharField(max_length=255)


class CreateLoanRequestModel(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
    interest_rate: Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]
    bank: Annotated[str, Field(max_length=255, min_length=1)]
    client_name: Annotated[str, Field(max_length=255, min_length=1)]

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid"
    }

class CreateLoanResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    client = serializers.PrimaryKeyRelatedField(read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    ip_address = serializers.IPAddressField()
    request_date = serializers.DateTimeField()
    bank = serializers.CharField()
    client_name = serializers.CharField()
    payments = PaymentResponseSerializer(many=True)
    remaining_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
