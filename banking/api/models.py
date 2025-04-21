import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Generator
from uuid import uuid4

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    GenericIPAddressField,
    Index,
    IntegerField,
    Model,
    UUIDField,
)
from django_prometheus.models import ExportModelOperationsMixin


class Bank(ExportModelOperationsMixin('bank'), Model):
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


class Loan(ExportModelOperationsMixin('loan'), Model):
    '''
    Represents a loan taken by a client (user). Stores information such as
    loan amount, interest rate, client details, and IP address from which
    the loan was requested.

    Attributes:
        id (UUID): Unique identifier for the loan.
        client (User): The user who requested the loan.
        amount (Decimal): The principal loan amount.
        interest_rate (Decimal): The interest rate per month (%).
        paid (bool): Indicates whether the loan has been paid.
        ip_address (str): The IP address from which the request originated.
        request_date (datetime): The timestamp when the loan was requested.
        bank (Bank): Bank entity responsible for the loan.
    '''

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = DecimalField(max_digits=12, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    installments_qt = IntegerField(default=0)
    paid = BooleanField(default=False)
    ip_address = GenericIPAddressField()
    request_date = DateTimeField(auto_now_add=True)
    client = ForeignKey(User, on_delete=CASCADE, related_name='loans')
    bank = ForeignKey(Bank, on_delete=CASCADE, related_name='loans')

    class Meta:
        indexes = [
            Index(fields=['client']),
            Index(fields=['bank']),
            Index(fields=['client', 'bank']),
        ]

    @property
    def _installment_value(self) -> Decimal:
        '''
        Calculates the monthly installment value for a loan based on the principal amount,
        interest rate, and number of installments using compound interest.

        Returns:
            Decimal: The calculated monthly installment value, rounded to two decimal places.

        Notes:
            - The function assumes compound interest with monthly compounding.
            - If the interest rate is 0, it divides the principal amount by the number of installments.
            - If the interest rate is non-zero, the formula used is the compound interest formula for installment loans.
        '''
        monthly_interest_rate = float(self.interest_rate) / 100 / 12  # Monthly rate from annual interest rate
        principal_amount = float(self.amount)

        if monthly_interest_rate == 0:  # IMPORTANT, in case of no interest rate
            monthly_payment = Decimal(principal_amount / self.installments_qt)
        else:
            # Compound interest formula for installment loans
            compound_factor = (1 + monthly_interest_rate) ** self.installments_qt
            monthly_payment = principal_amount * monthly_interest_rate * compound_factor / (compound_factor - 1)
            monthly_payment = Decimal(monthly_payment)

        # Round to two decimal places
        installment_value = monthly_payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return installment_value

    def generate_loan_installments(self) -> Generator['LoanInstallment', None, None]:
        '''
        Lazily generates and yields loan installments based on the loan details.

        Yields:
            LoanInstallment: A created loan installment instance.
        '''
        for i in range(self.installments_qt):
            installment = LoanInstallment.objects.create(
                id=uuid.uuid4(),
                loan=self,
                due_date=self.request_date + relativedelta(months=i + 1),
                amount=self._installment_value
            )
            yield installment

    def pay(self, payment_amount: float) -> tuple['Payment', float]:
        '''
        Applies a payment to the next pending or overdue installment. If the amount exceeds
        the needed value, the difference is returned as change.

        Args:
            payment_amount (float): The total amount to be paid toward the loan.

        Returns:
            tuple[Payment, float]: The created payment and the remaining amount as change.
        '''
        loan_installment = LoanInstallment.objects.filter(
            loan=self,
            status__in=[LoanInstallment.PENDING, LoanInstallment.OVERDUE]
        ).order_by('due_date').first()

        if loan_installment is None:
            raise ValueError('There are no pending or overdue installments to pay.')

        ammount_to_pay = min(Decimal(payment_amount), loan_installment.amount - loan_installment.paid_ammount)
        payment = loan_installment.pay(ammount_to_pay)

        change = float(Decimal(payment_amount) - ammount_to_pay)

        if not LoanInstallment.objects.filter(loan=self, paid=False).exists():
            self.paid = True
            self.save()

        return payment, change


class LoanInstallment(ExportModelOperationsMixin('loan_installment'), Model):
    '''
    Represents an installment for a loan. Each installment has a due date,
    amount, status, and payment date if the installment is paid.

    Attributes:
        id (UUID): Unique identifier for the installment.
        loan (Loan): The loan that the installment belongs to.
        due_date (datetime): The due date for the installment.
        amount (Decimal): The amount to be paid in the installment.
        paid (bool): Indicates whether the installment has been paid.
        paid_ammount (Decimal): Amount already paid to installment.
        payment_date (datetime): The date when the installment was paid (nullable).
        status (str): The status of the installment (pending, paid, overdue).
    '''

    PENDING = 'pending'
    PAID = 'paid'
    OVERDUE = 'overdue'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PAID, 'Paid'),
        (OVERDUE, 'Overdue'),
    ]

    id = UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    loan = ForeignKey(Loan, on_delete=CASCADE, related_name='installments')
    due_date = DateTimeField()
    amount = DecimalField(max_digits=12, decimal_places=2)
    paid = BooleanField(default=False)
    paid_ammount = DecimalField(default=0, max_digits=12, decimal_places=2)
    payment_date = DateTimeField(null=True, blank=True)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        indexes = [
            Index(fields=['loan']),
            Index(fields=['status', 'loan']),
            Index(fields=['due_date']),
            Index(fields=['status'])
        ]

    def pay(self, payment_amount: float) -> 'Payment':
        '''
        Registers a payment for this installment. If the total paid amount reaches or
        exceeds the required amount, marks the installment as fully paid.

        Args:
            payment_amount (float): The amount to be paid in this transaction.

        Returns:
            Payment: The created payment instance.
        '''
        payment = Payment.objects.create(
            id=uuid4(),
            loan_installment=self,
            payment_date=datetime.now(tz=timezone.utc),
            amount=Decimal(payment_amount),
        )

        self.paid_ammount += payment_amount

        if self.paid_ammount >= self.amount:
            self.paid = True
            self.payment_date = datetime.now(tz=timezone.utc)
            self.status = self.PAID

        self.save()
        return payment


class Payment(ExportModelOperationsMixin('payment'), Model):
    '''
    Represents a single payment made towards a specific loan installment.

    Attributes:
        id (UUID): Unique identifier for the payment.
        loan_installment (LoanInstallment): The installment this payment is associated with.
        payment_date (datetime): The timestamp when the payment was made.
        amount (Decimal): The amount paid.
    '''
    id = UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    loan_installment = ForeignKey(LoanInstallment, on_delete=CASCADE, related_name='payments', null=True)
    payment_date = DateTimeField(auto_now_add=True)
    amount = DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            Index(fields=['loan_installment']),
            Index(fields=['payment_date'])
        ]
