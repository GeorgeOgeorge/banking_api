from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID

from django.test import TestCase
from banking.api.utils.serializers import (
    CreateLoanRequestModel,
    CreatePaymentRequestModel,
    ListLoansQueryParams,
    LoanBalanceResponse,
    ListPaymentsQueryParams,
    CreateLoanRequestSerializer,
    CreatePaymentRequestSerializer,
    CreateLoanResponseSerializer,
    PaymentResponseSerializer,
    CreatePaymentResponse
)

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


class TestCreateLoan(TestCase):
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
