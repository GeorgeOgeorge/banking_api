from django.db import connection
from rest_framework.request import Request

from banking.api.utils.queries import (CREATE_LOAN_QUERY, CREATE_PAYMENT_QUERY,
                                       LIST_LOAN_QUERY, USER_OWNS_LOAN)
from banking.api.utils.serializers import (CreateLoanRequestModel,
                                           CreatePaymentRequestModel,
                                           ListLoansQueryParams)


def create_loan(
    request: Request,
    loan_request: CreateLoanRequestModel
) -> dict:
    """
    Creates a new loan entry in the database.

    Args:
        request (Request): The incoming HTTP request, used to get the authenticated user and IP address.
        loan_request (CreateLoanRequestModel): Validated request data with loan details.

    Returns:
        dict: Dictionary containing the newly created loan's data.
    """
    user_ip_addres = request.META.get(
        'HTTP_X_FORWARDED_FOR',
        request.META.get('REMOTE_ADDR')
    ).split(',')[0]

    with connection.cursor() as cursor:
        cursor.execute(CREATE_LOAN_QUERY, {
            "client_id": request.user.id,
            "amount": loan_request.amount,
            "interest_rate": loan_request.interest_rate,
            "bank": loan_request.bank,
            "client_name": loan_request.client_name,
            "ip_address": user_ip_addres
        })
        row_data = cursor.fetchone()

        loan = {
            "id": row_data[0],
            "client_id": row_data[1],
            "amount": row_data[2],
            "interest_rate": row_data[3],
            "bank": row_data[4],
            "client_name": row_data[5],
            "ip_address": row_data[6],
            "request_date": row_data[7],
        }

    return loan


def list_loans(
    request: Request,
    query_params: ListLoansQueryParams
) -> list[dict]:
    """
    Returns a paginated list of loans for the authenticated user.

    Args:
        request (Request): HTTP request object containing the authenticated user.
        query_params (ListLoansQueryParams): Pagination parameters, including limit and offset.

    Returns:
        list[dict]: List of loans.
    """
    with connection.cursor() as cursor:
        cursor.execute(LIST_LOAN_QUERY, {
            "client_id": request.user.id,
            "limit": query_params.limit,
            "offset": query_params.offset,
        })

        loans = [
            {
                "id": row_data[0],
                "amount": row_data[1],
                "interest_rate": row_data[2],
                "bank": row_data[3],
                "request_date": row_data[4],
            }
            for row_data in cursor
        ]

    return loans


def create_payment(
    request: Request,
    payment_request: CreatePaymentRequestModel
) -> dict:
    """
    Creates a loan payment.

    Args:
        request (Request): Request containing the authenticated user.
        payment_request (CreatePaymentRequestModel): Payment input data.

    Raises:
        ValueError: If the user does not own the loan.

    Returns:
        dict: Created payment data.
    """
    with connection.cursor() as cursor:
        cursor.execute(USER_OWNS_LOAN, {
            "client_id": request.user.id,
            "loan_id": payment_request.loan_id,
        })

        user_owns_loan = cursor.fetchone()
        if not user_owns_loan:
            raise ValueError(f"User {request.user.id} is not owner of loan {payment_request.loan_id}")

        cursor.execute(CREATE_PAYMENT_QUERY, {
            "amount": payment_request.amount,
            "loan_id": payment_request.loan_id,
        })
        row_data = cursor.fetchone()

        payment = {
            "id": row_data[0],
            "payment_date": row_data[1],
            "amount": row_data[2],
            "loan_id": row_data[3]
        }

    return payment
