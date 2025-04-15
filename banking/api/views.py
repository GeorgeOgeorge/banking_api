from drf_yasg.utils import swagger_auto_schema
from pydantic_core import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from banking.api.utils.serializers import CreateLoanRequestModel, CreateLoanRequestSerializer, LoanResponseSerializer
from banking.api.utils.utils import create_loan


@swagger_auto_schema(
    method='post',
    request_body=CreateLoanRequestSerializer,
    responses={
        201: LoanResponseSerializer,
        400: 'Occurs if payload is not in a valid schema.',
        500: 'Occurs if an error occurs while requesting loans.',
    },
    operation_description="Requests a new loan",
    security=[{'Bearer': []}],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_loan_request(request: Request) -> Response:
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
