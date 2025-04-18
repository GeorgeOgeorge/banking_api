import uuid
from decimal import ROUND_HALF_UP, Decimal

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
    '''

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = DecimalField(max_digits=12, decimal_places=2)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    installments_qt = IntegerField(default=0)
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

    def _calculate_monthly_installment(self) -> Decimal:
        '''
        Calculates the monthly installment value for a loan based on the principal amount,
        interest rate, and number of installments using compound interest.

        Args:
            principal_amount (float): The principal loan amount.
            annual_interest_rate (float): The annual interest rate (in percentage).
            number_of_installments (int): The number of monthly installments to be paid.

        Returns:
            Decimal: The calculated monthly installment value, rounded to two decimal places.

        Notes:
            - The function assumes compound interest with monthly compounding.
            - If the interest rate is 0, it divides the principal amount by the number of installments.
            - If the interest rate is non-zero, the formula used is the compound interest formula for installment loans.
        '''
        monthly_interest_rate = float(self.interest_rate) / 100 / 12  # Monthly rate from annual interest rate
        principal_amount = float(principal_amount)

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

    def create_loan_installments(self) -> None:
        '''
        Creates loan installments based on the loan details and the start date.

        Args:
            loan (Loan): The loan object to which the installments belong.
            loan_request (CreateLoanModel): The loan request data.
            start_date (datetime): The date when the first installment is due.
        '''
        installment_value = self._calculate_monthly_installment(
            self.amount,
            self.interest_rate,
            self.installments_qt
        )

        for i in range(self.installments_qt):
            LoanInstallment.objects.create(
                id=uuid.uuid4(),
                loan=self,
                due_date=self.request_date + relativedelta(months=i+1),
                amount=installment_value
            )

        return None


class LoanInstallment(Model):
    '''
    Represents an installment for a loan. Each installment has a due date,
    amount, status, and payment date if the installment is paid.

    Attributes:
        id (UUID): Unique identifier for the installment.
        loan (Loan): The loan that the installment belongs to.
        due_date (datetime): The due date for the installment.
        amount (Decimal): The amount to be paid in the installment.
        paid (bool): Indicates whether the installment has been paid.
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
    payment_date = DateTimeField(null=True, blank=True)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        indexes = [
            Index(fields=['loan']),
            Index(fields=['status', 'loan']),
            Index(fields=['due_date']),
            Index(fields=['status'])
        ]


class Payment(Model):
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

