from datetime import datetime, timezone
from uuid import UUID, uuid4

from django.db import connection
from rest_framework.request import Request

from banking.api.models import Bank, Loan
from banking.api.utils.exceptions import FailedToCreateInstallments, LoanAlreadyPaid, RowNotFound
from banking.api.utils.queries import LOAN_STATISTICS_QUERY, list_loans_query, list_payments_query
from banking.api.utils.serializers import (
    CreateBankModel,
    CreateLoanModel,
    CreatePaymentModel,
    ListLoansQueryParams,
    ListPaymentsQueryParams,
)


def get_user_ip_address(request: Request) -> str:
    '''Retrieve the user's IP address from the request headers.

    Args:
        request (Request): The HTTP request object.

    Returns:
        str: The user's IP address.
    '''
    ip_address = request.META.get(
        'HTTP_X_FORWARDED_FOR',
        request.META.get('REMOTE_ADDR')
    ).split(',')[0]

    return ip_address


def create_bank(request: Request, bank_data: CreateBankModel) -> dict:
    '''
    Creates a new bank.

    Args:
        request (Request): Authenticated user context.
        bank_data (CreateBankModel): Bank info to be created.

    Returns:
        dict: Created bank data.
    '''
    bank = Bank.objects.create(
        name=bank_data.name,
        bic=bank_data.bic,
        country=bank_data.country,
        interest_policy=bank_data.interest_policy,
        max_loan_amount=bank_data.max_loan_amount,
        created_by=request.user,
    )

    return {
        'id': str(bank.id),
        'name': bank.name,
        'bic': bank.bic,
        'country': bank.country,
        'interest_policy': bank.interest_policy,
        'max_loan_amount': str(bank.max_loan_amount),
    }


def create_loan(request: Request, loan_request: CreateLoanModel) -> dict:
    '''
    Creates a new loan entry in the database and generates the corresponding installments.
    If the installments cannot be created, the loan is deleted to maintain data integrity.

    Args:
        request (Request): The incoming HTTP request.
        loan_request (CreateLoanModel): Validated request data with loan details.

    Returns:
        dict: Dictionary containing the newly created loan's data.

    Raises:
        RowNotFound: If the specified bank does not exist.
        ValueError: If the requested loan amount exceeds the bank's limit.
        FailedToCreateInstallments: If an error occurs while creating the loan installments.
    '''
    bank = Bank.objects.filter(pk=loan_request.bank_id).first()

    if bank is None:
        raise RowNotFound('Bank not found.')
    if loan_request.amount > bank.max_loan_amount:
        raise ValueError('Requested amount exceeds bank limit.')

    loan = Loan.objects.create(
        id=uuid4(),
        client=request.user,
        bank=bank,
        amount=loan_request.amount,
        interest_rate=loan_request.interest_rate,
        installments_qt=loan_request.installments_qt,
        ip_address=get_user_ip_address(request),
        request_date=datetime.now(tz=timezone.utc),
    )

    try:
        loan_installments = [
            {
                "id": loan_installment.id,
                "due_date": loan_installment.due_date,
                "amount": loan_installment.amount,
            }
            for loan_installment in loan.generate_loan_installments()
        ]
    except Exception:
        loan.delete()
        raise FailedToCreateInstallments

    loan_data = {
        'id': str(loan.id),
        'amount': loan.amount,
        'interest_rate': loan.interest_rate,
        'request_date': loan.request_date.isoformat(),
        'bank_name': loan.bank.name,
        'loan_installments': loan_installments,
    }

    return loan_data


def pay_loan(request: Request, payment_request: CreatePaymentModel) -> dict:
    '''
    Creates a loan payment.

    Args:
        request (Request): Request containing the authenticated user.
        payment_request (CreatePaymentModel): Payment input data.

    Raises:
        RowNotFound: If the user does not own the loan.
        ValueError: If the loan is already paid or other validation fails.

    Returns:
        dict: Created payment data.
    '''
    loan = Loan.objects.filter(id=payment_request.loan_id, client=request.user).first()

    if loan is None:
        raise RowNotFound(f'User {request.user.id} is not owner of loan {payment_request.loan_id}')
    if loan.paid:
        raise LoanAlreadyPaid('Loan has already been paid')

    payment, change = loan.pay(payment_request.amount)

    return {
        'id': str(payment.id),
        'payment_date': payment.payment_date.isoformat(),
        'amount': payment.amount,
        'change': change,
    }


def list_loans(request: Request, query_params: ListLoansQueryParams) -> list[dict]:
    '''
    Returns a paginated list of loans for the authenticated user.

    Args:
        request (Request): HTTP request object containing the authenticated user.
        query_params (ListLoansQueryParams): Pagination parameters, including limit and offset.

    Returns:
        list[dict]: List of loans.
    '''
    query = list_loans_query(query_params)
    filters = query_params.model_dump(exclude_none=True)

    with connection.cursor() as cursor:
        cursor.execute(query, {
            **filters,
            'client_id': request.user.id,
            'limit': query_params.limit,
            'offset': query_params.offset,
        })

        loans = [
            {
                'id': row_data[0],
                'amount': row_data[1],
                'interest_rate': row_data[2],
                'paid': row_data[3],
                'request_date': row_data[4],
                'bank_name': row_data[5],
                'outstanding_balance': row_data[6],
                'loan_installments': row_data[7],
            }
            for row_data in cursor
        ]

    return loans


def list_loan_balance(request: Request, loan_id: UUID) -> dict:
    '''
    Retrieves the remaining balance of a loan for the authenticated user.

    Args:
        request (Request): The HTTP request containing the authenticated user.
        loan_id (UUID): The ID of the loan to fetch the balance for.

    Raises:
        ValueError: If the loan does not belong to the authenticated user.

    Returns:
        dict: A dictionary containing loan and remaining balance information.
    '''
    with connection.cursor() as cursor:
        cursor.execute(LOAN_STATISTICS_QUERY, {
            'client_id': request.user.id,
            'loan_id': loan_id,
        })
        row_data = cursor.fetchone()
        if not row_data:
            raise ValueError(f'User {request.user.id} is not owner of loan {loan_id}')

        loan_balance = {
            'id': row_data[0],
            'amount': row_data[1],
            'interest_rate': row_data[2],
            'paid': row_data[3],
            'bank_name': row_data[4],
            'installments_count': row_data[5],
            'paid_installments': row_data[6],
            'pending_installments': row_data[7],
            'overdue_installments': row_data[8],
            'total_paid': row_data[9],
            'outstanding_balance': row_data[10],
            'total_pending': row_data[11],
            'total_overdue': row_data[12],
        }

    return loan_balance


def list_payments(request: Request, query_params: ListPaymentsQueryParams) -> list[dict]:
    '''
    Retrieves a filtered and paginated list of payments for the authenticated user.

    Args:
        request (Request): HTTP request containing the authenticated user.
        query_params (ListPaymentsQueryParams): Query parameters for filtering and pagination.

    Returns:
        list[dict]: List of payments matching the filters.
    '''
    query = list_payments_query(query_params)
    filters = query_params.model_dump(exclude_none=True)

    with connection.cursor() as cursor:
        cursor.execute(query, {
            **filters,
            'client_id': request.user.id,
            'limit': query_params.limit,
            'offset': query_params.offset,
        })

        payments = [
            {
                'id': row_data[0],
                'payment_date': row_data[1],
                'amount': row_data[2],
                'loan_installment_id': row_data[3],
                'bank_name': row_data[4],
                'loan_id': row_data[5],
            }
            for row_data in cursor
        ]

    return payments
