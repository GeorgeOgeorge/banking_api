from uuid import UUID

from drf_yasg.utils import swagger_auto_schema
from pydantic_core import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from banking.api.utils.exceptions import FailedToCreateInstallments, LoanAlreadyPaid, RowNotFound
from banking.api.utils.serializers import (
    CreateBankModel,
    CreateBankRequest,
    CreateBankResponse,
    CreateLoanModel,
    CreateLoanRequest,
    CreateLoanResponse,
    CreatePaymentModel,
    CreatePaymentResponse,
    CreatePaymentSerializer,
    ListLoansQueryParams,
    ListLoansQueryParamsSerializer,
    ListLoansResponse,
    ListPaymentsQueryParams,
    ListPaymentsQueryParamsSerializer,
    ListPaymentsResponse,
    LoanStatisticsResponse,
)
from banking.api.utils.utils import (
    create_bank,
    create_loan,
    list_loan_balance,
    list_loans,
    list_payments,
    pay_loan,
)


@swagger_auto_schema(
    method='post',
    request_body=CreateBankRequest,
    responses={
        201: CreateBankResponse,
        400: 'Occurs if payload is not in a valid schema.',
        500: 'Occurs if an error occurs while creating bank.',
    },
    operation_description='Creates bank',
    security=[{'Bearer': []}],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_bank_route(request: Request) -> Response:
    '''
    Creates a new bank.

    Attributes:
        request (Request): The HTTP request containing the bank creation data.

    Returns:
        Response: Created bank data.
    '''
    try:
        bank_data = CreateBankModel(**request.data)
    except ValidationError as payload_error:
        return Response(payload_error.json(), status=status.HTTP_400_BAD_REQUEST)

    try:
        bank: dict = create_bank(request, bank_data)
    except Exception:
        return Response({'error': 'Error while creating bank'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(bank, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    request_body=CreateLoanRequest,
    responses={
        201: CreateLoanResponse,
        400: 'Occurs if payload is not in a valid schema.',
        404: 'Occurs if bank is not found',
        500: 'Occurs if an error occurs while requesting loans.',
    },
    operation_description='Requests a new loan',
    security=[{'Bearer': []}],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_loan_route(request: Request) -> Response:
    '''
    Endpoint for creating a new loan. Requires authentication and
    expects a valid payload with loan details.

    Arguments:
        request: HTTP request containing loan data.

    Returns:
        Response with loan data if successful or error message if failed.
    '''
    try:
        loan_request = CreateLoanModel(**request.data)
    except ValidationError as payload_error:
        return Response(payload_error.errors(), status=status.HTTP_400_BAD_REQUEST)

    try:
        loan = create_loan(request, loan_request)
    except RowNotFound as bank_not_found:
        return Response({'error': str(bank_not_found)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as validation_error:
        return Response({'error': str(validation_error)}, status=status.HTTP_400_BAD_REQUEST)
    except FailedToCreateInstallments:
        return Response(
            {'error': 'Error while creating loan installments'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception:
        return Response(
            {'error': 'Unexpected error while requesting loan.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(loan, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    request_body=CreatePaymentSerializer,
    responses={
        200: CreatePaymentResponse,
        400: 'Occurs if payload is not in a valid schema, or if loan has already been paid',
        404: 'Occurs if not able to find selected loan or loan is not owned by user.',
        500: 'Occurs if an error occurs while paying loan.',
    },
    operation_description='Pays user loan',
    security=[{'Bearer': []}],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_route(request: Request) -> Response:
    '''
    Handles the payment creation route.

    Args:
        request (Request): HTTP request containing payment data.

    Returns:
        Response: API response with payment data or error message.
    '''
    try:
        payment_request = CreatePaymentModel(**request.data)
    except ValidationError as payload_error:
        return Response(payload_error.json(), status=status.HTTP_400_BAD_REQUEST)

    try:
        payment = pay_loan(request, payment_request)
    except RowNotFound as loan_not_found:
        return Response({'error': str(loan_not_found)}, status=status.HTTP_404_NOT_FOUND)
    except LoanAlreadyPaid:
        return Response({'error': 'Loan has already been paid'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({'error': 'Error while paying loan'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(payment, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='get',
    query_serializer=ListLoansQueryParamsSerializer,
    responses={
        200: ListLoansResponse(many=True),
        400: 'Occurs if query params are not in a valid schema.',
        500: 'Occurs if an error occurs while requesting loans.',
    },
    operation_description='Returns user requested loans',
    security=[{'Bearer': []}],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_loans_route(request: Request) -> Response:
    '''
    Handles GET requests to retrieve a list of loans associated with the authenticated user.

    Args:
        request (Request): HTTP request object containing user credentials and query parameters.

    Returns:
        Response with a list of user's requested loans
    '''
    try:
        query_params = ListLoansQueryParams(**request.query_params)
    except ValidationError as query_params_error:
        return Response(query_params_error.json(), status=status.HTTP_400_BAD_REQUEST)

    try:
        loans = list_loans(request, query_params)
    except Exception:
        return Response({'error': 'Error fetching user loans'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(loans, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    responses={
        200: LoanStatisticsResponse,
        404: 'Returned when the specified loan is not found or does not belong to the authenticated user.',
        500: 'Returned when an unexpected error occurs while retrieving loan statistics.',
    },
    operation_description='Retrieve detailed statistics for a specific loan.',
    security=[{'Bearer': []}],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_statistics_route(request: Request, loan_id: UUID) -> Response:
    '''
    Handles HTTP request to retrieve the remaining balance of a specific loan.

    Args:
        request (Request): The HTTP request containing user context.
        loan_id (UUID): The ID of the loan to retrieve the balance for.

    Returns:
        Response: A JSON response with the remaining loan balance or an error message.
    '''
    try:
        loan_balance = list_loan_balance(request, loan_id)
    except ValueError as user_doesnt_own_loan:
        return Response({'error': str(user_doesnt_own_loan)}, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return Response({'error': 'Error while paying loan'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(loan_balance, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    query_serializer=ListPaymentsQueryParamsSerializer,
    responses={
        200: ListPaymentsResponse(many=True),
        400: 'Occurs if query params are not in a valid schema.',
        500: 'Occurs if an error occurs while fetching payments.',
    },
    operation_description='List user payments',
    security=[{'Bearer': []}],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_payments_route(request: Request) -> Response:
    '''
    Handles the route for listing user payments with optional filters.

    Args:
        request (Request): HTTP request with query parameters.

    Returns:
        Response: Paginated list of payments or error response.
    '''
    try:
        query_params = ListPaymentsQueryParams(**request.query_params)
    except ValidationError as query_params_error:
        return Response(query_params_error.json(), status=status.HTTP_400_BAD_REQUEST)

    try:
        payments = list_payments(request, query_params)
    except Exception:
        return Response({'error': 'Error fetching user payments'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(payments, status=status.HTTP_200_OK)
