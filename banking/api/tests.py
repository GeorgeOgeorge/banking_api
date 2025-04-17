from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from banking.api.views import create_loan_route, list_loans_route
from banking.api.utils.serializers import (
    CreateLoanRequestModel,
    CreateLoanRequestSerializer,
    CreateLoanResponseSerializer,
    CreatePaymentRequestModel,
    CreatePaymentRequestSerializer,
    CreatePaymentResponse,
    ListLoansQueryParams,
    ListPaymentsQueryParams,
    LoanBalanceResponse,
    PaymentResponseSerializer,
)

User = get_user_model()


class SerializerTests(TestCase):

    def test_create_loan_request_model_valid(self):
        """Test CreateLoanRequestModel validation and serialization"""
        loan_data = {
            "amount": Decimal("10000.00"),
            "interest_rate": Decimal("5.00"),
            "bank": "Banco XYZ",
            "client_name": "John Doe"
        }

        loan = CreateLoanRequestModel(**loan_data)

        self.assertEqual(loan.amount, Decimal("10000.00"))
        self.assertEqual(loan.interest_rate, Decimal("5.00"))
        self.assertEqual(loan.bank, "Banco XYZ")
        self.assertEqual(loan.client_name, "John Doe")

    def test_create_payment_request_model_valid(self):
        """Test CreatePaymentRequestModel validation and serialization"""
        payment_data = {
            "loan_id": uuid4(),
            "amount": 2000.00
        }

        payment = CreatePaymentRequestModel(**payment_data)

        self.assertIsInstance(payment.loan_id, UUID)
        self.assertEqual(payment.amount, 2000.00)

    def test_invalid_create_loan_request_model(self):
        """Test CreateLoanRequestModel validation failure for invalid data"""
        invalid_data = {
            "amount": Decimal("-100.00"),
            "interest_rate": Decimal("5.00"),
            "bank": "Banco XYZ",
            "client_name": "John Doe"
        }

        with self.assertRaises(ValueError):
            CreateLoanRequestModel(**invalid_data)

    def test_list_loans_query_params_valid(self):
        """Test ListLoansQueryParams validation"""
        query_params_data = {
            "page": 2,
            "limit": 5
        }

        query_params = ListLoansQueryParams(**query_params_data)

        self.assertEqual(query_params.page, 2)
        self.assertEqual(query_params.limit, 5)
        self.assertEqual(query_params.offset, 5)

    def test_list_loans_query_params_invalid(self):
        """Test ListLoansQueryParams validation failure for invalid data"""
        query_params_data = {
            "page": -1,
            "limit": 5
        }

        with self.assertRaises(ValueError):
            ListLoansQueryParams(**query_params_data)

    def test_loan_balance_response(self):
        """Test LoanBalanceResponse serializer"""
        loan_balance_data = {
            "id": uuid4(),
            "bank": "Banco XYZ",
            "amount": 10000.00,
            "interest_rate": 5.00,
            "request_date": "2025-04-16",
            "total_paid": 2000.00,
            "remaining_debt": 8000.00
        }

        serializer = LoanBalanceResponse(data=loan_balance_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["remaining_debt"], Decimal("8000.00"))

    def test_list_payments_query_params_valid(self):
        """Test ListPaymentsQueryParams validation"""
        query_params_data = {
            "payment_id": uuid4(),
            "loan_id": uuid4(),
            "payment_date": "2025-04-16",
            "page": 1,
            "limit": 10
        }

        query_params = ListPaymentsQueryParams(**query_params_data)

        self.assertEqual(query_params.payment_id, query_params_data["payment_id"])
        self.assertEqual(query_params.loan_id, query_params_data["loan_id"])
        self.assertEqual(query_params.payment_date, date(2025, 4, 16))
        self.assertEqual(query_params.page, 1)
        self.assertEqual(query_params.limit, 10)

    def test_list_payments_query_params_invalid_date(self):
        """Test ListPaymentsQueryParams invalid date format"""
        query_params_data = {
            "payment_date": "2025-04-32",
            "page": 1,
            "limit": 10
        }

        with self.assertRaises(ValueError):
            ListPaymentsQueryParams(**query_params_data)

    def test_create_loan_request_serializer_valid(self):
        """Test CreateLoanRequestSerializer validation and serialization"""
        loan_data = {
            "amount": Decimal("10000.00"),
            "interest_rate": Decimal("5.00"),
            "bank": "Banco XYZ",
            "client_name": "John Doe"
        }

        serializer = CreateLoanRequestSerializer(data=loan_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["amount"], Decimal("10000.00"))

    def test_create_payment_request_serializer_valid(self):
        """Test CreatePaymentRequestSerializer validation and serialization"""
        payment_data = {
            "loan": uuid4(),
            "amount": Decimal("1000.00")
        }

        serializer = CreatePaymentRequestSerializer(data=payment_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["amount"], Decimal("1000.00"))

    def test_create_loan_response_serializer(self):
        """Test CreateLoanResponseSerializer serialization"""
        loan_data = {
            "id": uuid4(),
            "client": uuid4(),
            "amount": Decimal("10000.00"),
            "interest_rate": Decimal("5.00"),
            "ip_address": "192.168.1.1",
            "request_date": "2025-04-16",
            "bank": "Banco XYZ",
            "client_name": "John Doe",
            "payments": [],
            "remaining_balance": Decimal("8000.00")
        }

        serializer = CreateLoanResponseSerializer(data=loan_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["remaining_balance"], Decimal("8000.00"))

    def test_payment_response_serializer(self):
        """Test PaymentResponseSerializer serialization"""
        payment_data = {
            "id": uuid4(),
            "loan": uuid4(),
            "payment_date": "2025-04-16",
            "amount": Decimal("1000.00")
        }

        serializer = PaymentResponseSerializer(data=payment_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["amount"], Decimal("1000.00"))

    def test_create_payment_response_serializer(self):
        """Test CreatePaymentResponse serializer"""
        payment_data = {
            "id": uuid4(),
            "payment_date": "2025-04-16",
            "amount": Decimal("1000.00"),
            "loan_id": uuid4()
        }

        serializer = CreatePaymentResponse(data=payment_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["amount"], Decimal("1000.00"))


class TestQueries(TestCase):
    def test_list_payments_query(self):
        """Test query with all parameters"""
        from banking.api.utils.queries import list_payments_query

        query = list_payments_query(ListPaymentsQueryParams(
            payment_id=uuid4(),
            loan_id=uuid4(),
            payment_date=date(2025, 4, 16),
            client_id=uuid4(),
            limit=10,
            page=1
        ))

        assert "and ap.id = %(payment_id)s" in query.strip()
        assert "and ap.loan_id = %(loan_id)s" in query.strip()
        assert "and date(ap.payment_date) = %(payment_date)s" in query.strip()


class TestUtils(TestCase):
    @patch('banking.api.utils.utils.connection.cursor')
    @patch('banking.api.utils.utils.get_user_ip_addres', return_value='192.168.1.1')
    def test_create_loan_success(self, _, mock_cursor):
        """Test Loan creation success"""
        from banking.api.utils.utils import create_loan

        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
            1,
            1,
            1000.00,
            5.0,
            'BankName',
            'ClientName',
            '192.168.1.1',
            '2025-04-15 12:00:00'
        )

        request = MagicMock()
        request.user.id = 1

        result = create_loan(
            request,
            MagicMock(
                amount=1000.00,
                interest_rate=5.0,
                bank='BankName',
                client_name= 'ClientName',
            )
        )

        expected_result = {
            'id': 1,
            'client_id': 1,
            'amount': 1000.00,
            'interest_rate': 5.0,
            'bank': 'BankName',
            'client_name': 'ClientName',
            'ip_address': '192.168.1.1',
            'request_date': '2025-04-15 12:00:00'
        }

        self.assertEqual(result, expected_result)

    @patch('banking.api.utils.utils.connection.cursor')
    @patch('banking.api.utils.utils.get_user_ip_addres', return_value='192.168.1.1')
    def test_create_loan_fail_database_error(self, _, mock_cursor):
        """Test Loan creation error"""
        from banking.api.utils.utils import create_loan

        mock_cursor.return_value.__enter__.side_effect = Exception('Database error')

        request = MagicMock()
        request.user.id = 1

        with self.assertRaises(Exception):
            create_loan(
                request,
                MagicMock(
                    amount=1000.00,
                    interest_rate=5.0,
                    bank='BankName',
                    client_name= 'ClientName',
                )
            )

    def test_get_user_ip_addres_with_forwarded_for(self):
        """Test retrieving IP from HTTP_X_FORWARDED_FOR"""
        from banking.api.utils.utils import get_user_ip_addres

        request = MagicMock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.100, 10.0.0.1',
            'REMOTE_ADDR': '127.0.0.1'
        }

        result = get_user_ip_addres(request)
        self.assertEqual(result, '192.168.1.100')

    def test_get_user_ip_addres_with_remote_addr_only(self):
        """Test retrieving IP from REMOTE_ADDR when HTTP_X_FORWARDED_FOR is missing"""
        from banking.api.utils.utils import get_user_ip_addres

        request = MagicMock()
        request.META = {
            'REMOTE_ADDR': '127.0.0.1'
        }

        result = get_user_ip_addres(request)
        self.assertEqual(result, '127.0.0.1')

    @patch('banking.api.utils.utils.connection.cursor')
    def test_list_loans_success(self, mock_cursor):
        """Test listing loans successfully"""
        from banking.api.utils.utils import list_loans

        mock_cursor.return_value.__enter__.return_value.__iter__.return_value = iter([
            (1, 1000.0, 5.0, 'BankName', '2025-04-15 12:00:00'),
            (2, 1500.0, 4.5, 'AnotherBank', '2025-04-14 10:30:00')
        ])

        request = MagicMock()
        request.user.id = 1

        query_params = MagicMock()
        query_params.limit = 10
        query_params.offset = 0

        result = list_loans(request, query_params)

        expected_result = [
            {
                'id': 1,
                'amount': 1000.0,
                'interest_rate': 5.0,
                'bank': 'BankName',
                'request_date': '2025-04-15 12:00:00'
            },
            {
                'id': 2,
                'amount': 1500.0,
                'interest_rate': 4.5,
                'bank': 'AnotherBank',
                'request_date': '2025-04-14 10:30:00'
            }
        ]

        self.assertEqual(result, expected_result)

    @patch('banking.api.utils.utils.connection.cursor')
    def test_list_loans_database_error(self, mock_cursor):
        """Test listing loans with database error"""
        from banking.api.utils.utils import list_loans

        mock_cursor.return_value.__enter__.side_effect = Exception('Database error')

        request = MagicMock()
        request.user.id = 1

        query_params = MagicMock()
        query_params.limit = 10
        query_params.offset = 0

        with self.assertRaises(Exception):
            list_loans(request, query_params)

    @patch('banking.api.utils.utils.connection.cursor')
    def test_create_payment_success(self, mock_cursor):
        """Test payment creation success"""
        from banking.api.utils.utils import create_payment

        mock_cursor_instance = mock_cursor.return_value.__enter__.return_value

        mock_cursor_instance.fetchone.side_effect = [
            True,
            (1, '2025-04-15 12:00:00', 500.0, 2)
        ]

        request = MagicMock()
        request.user.id = 1

        payment_request = MagicMock()
        payment_request.loan_id = 2
        payment_request.amount = 500.0

        result = create_payment(request, payment_request)

        expected_result = {
            'id': 1,
            'payment_date': '2025-04-15 12:00:00',
            'amount': 500.0,
            'loan_id': 2
        }

        self.assertEqual(result, expected_result)

    @patch('banking.api.utils.utils.connection.cursor')
    def test_create_payment_user_not_owner(self, mock_cursor):
        """Test payment creation with user not owning loan"""
        from banking.api.utils.utils import create_payment

        mock_cursor_instance = mock_cursor.return_value.__enter__.return_value
        mock_cursor_instance.fetchone.return_value = None

        request = MagicMock()
        request.user.id = 1

        payment_request = MagicMock()
        payment_request.loan_id = 2
        payment_request.amount = 500.0

        with self.assertRaises(ValueError):
            create_payment(request, payment_request)

    @patch('banking.api.utils.utils.connection.cursor')
    def test_create_payment_database_error(self, mock_cursor):
        """Test payment creation with database error"""
        from banking.api.utils.utils import create_payment

        mock_cursor.return_value.__enter__.side_effect = Exception('Database error')

        request = MagicMock()
        request.user.id = 1

        payment_request = MagicMock()
        payment_request.loan_id = 2
        payment_request.amount = 500.0

        with self.assertRaises(Exception):
            create_payment(request, payment_request)

    @patch('banking.api.utils.utils.connection.cursor')
    @patch('banking.api.utils.utils.list_payments_query')
    def test_list_payments_success(self, mock_query_fn, mock_cursor):
        """Test payment listing success"""
        from banking.api.utils.utils import list_payments

        mock_query_fn.return_value = 'SELECT * FROM payments'

        mock_cursor_instance = mock_cursor.return_value.__enter__.return_value
        mock_cursor_instance.__iter__.return_value = iter([
            (1, '2025-04-15 12:00:00', 250.0, 10),
            (2, '2025-04-16 12:00:00', 300.0, 11)
        ])

        request = MagicMock()
        request.user.id = 1

        query_params = MagicMock()
        query_params.limit = 10
        query_params.offset = 0
        query_params.model_dump.return_value = {}

        result = list_payments(request, query_params)

        expected_result = [
            {
                'id': 1,
                'payment_date': '2025-04-15 12:00:00',
                'amount': 250.0,
                'loan_id': 10,
            },
            {
                'id': 2,
                'payment_date': '2025-04-16 12:00:00',
                'amount': 300.0,
                'loan_id': 11,
            }
        ]

        self.assertEqual(result, expected_result)

    @patch('banking.api.utils.utils.connection.cursor')
    @patch('banking.api.utils.utils.list_payments_query')
    def test_list_payments_database_error(self, mock_query_fn, mock_cursor):
        """Test payment listing with database error"""
        from banking.api.utils.utils import list_payments

        mock_query_fn.return_value = 'SELECT * FROM payments'
        mock_cursor.return_value.__enter__.side_effect = Exception('Database error')

        request = MagicMock()
        request.user.id = 1

        query_params = MagicMock()
        query_params.limit = 10
        query_params.offset = 0
        query_params.model_dump.return_value = {}

        with self.assertRaises(Exception):
            list_payments(request, query_params)

    @patch('banking.api.utils.utils.connection.cursor')
    def test_list_loan_balance_success(self, mock_cursor):
        """Test successful retrieval of loan balance"""
        from banking.api.utils.utils import list_loan_balance

        mock_cursor_instance = mock_cursor.return_value.__enter__.return_value
        mock_cursor_instance.fetchone.return_value = (
            1, 'BankName', 1000.00, 5.0, '2025-04-15 12:00:00', 300.00, 700.00
        )

        request = MagicMock()
        request.user.id = 1
        loan_id = UUID('12345678-1234-5678-1234-567812345678')

        result = list_loan_balance(request, loan_id)

        expected_result = {
            'id': 1,
            'bank': 'BankName',
            'amount': 1000.00,
            'interest_rate': 5.0,
            'request_date': '2025-04-15 12:00:00',
            'total_paid': 300.00,
            'remaining_debt': 700.00,
        }

        self.assertEqual(result, expected_result)

    @patch('banking.api.utils.utils.connection.cursor')
    def test_list_loan_balance_not_owner(self, mock_cursor):
        """Test loan balance retrieval with unauthorized user"""
        from banking.api.utils.utils import list_loan_balance

        mock_cursor_instance = mock_cursor.return_value.__enter__.return_value
        mock_cursor_instance.fetchone.return_value = None

        request = MagicMock()
        request.user.id = 1
        loan_id = UUID('12345678-1234-5678-1234-567812345678')

        with self.assertRaises(ValueError) as context:
            list_loan_balance(request, loan_id)

        self.assertEqual(
            str(context.exception),
            f'User {request.user.id} is not owner of loan {loan_id}'
        )

    @patch('banking.api.utils.utils.connection.cursor')
    def test_list_loan_balance_database_error(self, mock_cursor):
        """Test loan balance retrieval with database error"""
        from banking.api.utils.utils import list_loan_balance

        mock_cursor.return_value.__enter__.side_effect = Exception('Database error')

        request = MagicMock()
        request.user.id = 1
        loan_id = UUID('12345678-1234-5678-1234-567812345678')

        with self.assertRaises(Exception):
            list_loan_balance(request, loan_id)


class TestViews(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='foo', password='test123')
        self.factory = APIRequestFactory()

    @patch('banking.api.views.create_loan', return_value={'foo': 'foo'})
    def test_create_loan_route_success(self, mock_create_loan):
        """Test successful loan creation"""
        request = self.factory.post('/loan', {
            'amount': 1000.0,
            'bank': 'BankName',
            'interest_rate': 5.0,
            'client_name': 'foo'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_loan_route(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'foo': 'foo'})
        mock_create_loan.assert_called_once()

    def test_create_loan_route_invalid_payload(self):
        """Test loan creation with invalid payload"""
        request = self.factory.post('/loan', {
            'invalid_field': 'value'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_loan_route(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Field required', response.data)

    @patch('banking.api.views.create_loan', side_effect=Exception('unexpected error'))
    def test_create_loan_route_internal_error(self, mock_create_loan):
        """Test internal server error during loan creation"""
        request = self.factory.post('/loan', {
            'amount': 1000.0,
            'bank': 'BankName',
            'interest_rate': 5.0,
            'client_name': 'foo',
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_loan_route(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {'error': 'Error while requesting loan'})
        mock_create_loan.assert_called_once()

    @patch('banking.api.views.list_loans', return_value=[{'foo': 'foo'}])
    def test_list_loans_route_success(self, mock_list_loans):
        """Test successful loan listing"""
        request = self.factory.get('/loans')
        force_authenticate(request, user=self.user)

        response = list_loans_route(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{'foo': 'foo'}])
        mock_list_loans.assert_called_once()

    def test_list_loans_route_invalid_query_params(self):
        """Test loan listing with invalid query params"""
        request = self.factory.get('/loans?invalid_param=bad')
        force_authenticate(request, user=self.user)

        response = list_loans_route(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('extra_forbidden', response.data)

    @patch('banking.api.views.list_loans', side_effect=Exception('unexpected error'))
    def test_list_loans_route_internal_error(self, mock_list_loans):
        """Test internal server error during loan listing"""
        request = self.factory.get('/loans')
        force_authenticate(request, user=self.user)

        response = list_loans_route(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {'error': 'Error fetching user loans'})
        mock_list_loans.assert_called_once()