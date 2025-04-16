import uuid

from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    GenericIPAddressField,
    Model,
    UUIDField
)


class Loan(Model):
    '''
    Represents a loan taken by a client (user). Stores information such as
    loan amount, interest rate, client details, and IP address from which
    the loan was requested.

    Attributes:
        id (UUID): Unique identifier for the loan.
        client (User): The user who requested the loan.
        amount (Decimal): The principal loan amount.
        interest_rate (Decimal): The interest rate per month (%).
        ip_address (str): The IP address from which the request originated.
        request_date (datetime): The timestamp when the loan was requested.
        bank (str): Bank name involved in the loan.
        client_name (str): Name of the client at the moment of request.
    '''

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = ForeignKey(User, on_delete=CASCADE, related_name='loans')
    amount = DecimalField(max_digits=12, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    ip_address = GenericIPAddressField()
    request_date = DateTimeField(auto_now_add=True)
    bank = CharField(max_length=100)
    client_name = CharField(max_length=100)


class Payment(Model):
    '''
    Represents a single payment made towards a loan.

    Attributes:
        loan (Loan): The loan this payment is associated with.
        payment_date (datetime): The timestamp when the payment was made.
        amount (Decimal): The amount paid.
    '''

    loan = ForeignKey(Loan, on_delete=CASCADE, related_name='payments')
    payment_date = DateTimeField(auto_now_add=True)
    amount = DecimalField(max_digits=12, decimal_places=2)
