from drf_yasg.utils import swagger_auto_schema
from pydantic_core import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from banking.api.utils.serializers import (CreateLoanRequestModel,
                                           CreateLoanRequestSerializer,
                                           CreateLoanResponseSerializer,
                                           CreatePaymentRequestModel,
                                           CreatePaymentRequestSerializer,
                                           CreatePaymentResponse,
                                           ListLoansQueryParams,
                                           ListLoansQueryParamsSerializer,
                                           ListLoansResponse)
from banking.api.utils.utils import create_loan, create_payment, list_loans


@swagger_auto_schema(
    method='post',
    request_body=CreateLoanRequestSerializer,
    responses={
        201: CreateLoanResponseSerializer,
        400: 'Occurs if payload is not in a valid schema.',
        500: 'Occurs if an error occurs while requesting loans.',
    },
    operation_description="Requests a new loan",
    security=[{'Bearer': []}],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_loan_route(request: Request) -> Response:
    """
    Endpoint for creating a new loan. Requires authentication and
    expects a valid payload with loan details.

    Arguments:
        request: HTTP request containing loan data.

    Returns:
        Response with loan data if successful or error message if failed.
    """
    try:
        loan_request = CreateLoanRequestModel(**request.data)
    except ValidationError as payload_error:
        return Response(payload_error.json(), status=status.HTTP_400_BAD_REQUEST)

    try:
        loan: dict = create_loan(request, loan_request)
    except Exception as request_loan_error:
        return Response({"error": "Error while requesting loan"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(loan, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='get',
    query_serializer=ListLoansQueryParamsSerializer,
    responses={
        200: ListLoansResponse(many=True),
        400: 'Occurs if query params are not in a valid schema.',
        500: 'Occurs if an error occurs while requesting loans.',
    },
    operation_description="Returns user requested loans",
    security=[{'Bearer': []}],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_loans_route(request: Request) -> Response:
    """
    Handles GET requests to retrieve a list of loans associated with the authenticated user.

    Args:
        request (Request): HTTP request object containing user credentials and query parameters.

    Returns:
        Response with a list of user's requested loans
    """
    try:
        query_params = ListLoansQueryParams(**request.query_params)
    except ValidationError as query_params_error:
        return Response(query_params_error.json(), status=status.HTTP_400_BAD_REQUEST)

    try:
        loans = list_loans(request, query_params)
    except Exception:
        return Response({"error": "Error fetching user loans"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(loans, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    request_body=CreatePaymentRequestSerializer,
    responses={
        200: CreatePaymentResponse,
        400: 'Occurs if payload is not in a valid schema.',
        404: 'Occurs if not able to find selected loan or loan is not owned by user.',
        500: 'Occurs if an error occurs while paying loan.',
    },
    operation_description='Pays user loan',
    security=[{'Bearer': []}],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_route(request: Request) -> Response:
    """
    Handles the payment creation route.

    Args:
        request (Request): HTTP request containing payment data.

    Returns:
        Response: API response with payment data or error message.
    """
    try:
        payment_request = CreatePaymentRequestModel(**request.data)
    except ValidationError as payload_error:
        return Response(payload_error.json(), status=status.HTTP_400_BAD_REQUEST)

    try:
        payment = create_payment(request, payment_request)
    except ValueError as user_doesnt_own_loan:
        return Response({'error': str(user_doesnt_own_loan)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as loan_payment_error:
        return Response({'error': 'Error while paying loan'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(payment, status=status.HTTP_201_CREATED)
