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


class Bank(Model):
    '''
    Represents the financial institution responsible for issuing loans.

    Attributes:
        id (UUID): Unique identifier for the bank.
        name (str): The official name of the bank.
        bic (str): Bank Identifier Code (SWIFT), used for international transfers.
        country (str): Country where the bank operates.
        interest_policy (str): Description of the bank's policy for applying interest rates.
        max_loan_amount (Decimal): The maximum loan amount the bank is willing to offer.
        created_at (datetime): Timestamp of when the bank record was created.
        updated_at (datetime): Timestamp of the last update to the bank record.
        created_by (User): User who created the bank record.
        updated_by (User): User who last updated the bank record.
    '''

    id = UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    name = CharField(max_length=100, unique=True)
    bic = CharField(blank=True, max_length=20, null=True)
    country = CharField(max_length=50)
    interest_policy = CharField(blank=True, max_length=100)
    max_loan_amount = DecimalField(decimal_places=2, default=0, max_digits=12)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='created_banks',
        null=True,
        blank=True
    )
    updated_by = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='updated_banks',
        null=True,
        blank=True
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
        bank (Bank): Bank entity responsible for the loan.
        client_name (str): Name of the client at the moment of request.
    '''

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = ForeignKey(User, on_delete=CASCADE, related_name='loans')
    amount = DecimalField(max_digits=12, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    ip_address = GenericIPAddressField()
    request_date = DateTimeField(auto_now_add=True)
    bank = ForeignKey(Bank, on_delete=CASCADE, related_name='loans')
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
