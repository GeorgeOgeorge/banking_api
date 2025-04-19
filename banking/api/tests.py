from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from parameterized import parameterized
from pydantic import ValidationError
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from banking.api.utils.exceptions import FailedToCreateInstallments, LoanAlreadyPaid, RowNotFound
from banking.api.utils.queries import list_loans_query, list_payments_query
from banking.api.utils.serializers import (
    CreateBankModel,
    CreateBankRequest,
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
    PaginationQueryParamsSerializer,
)
from banking.api.utils.utils import (
    create_bank,
    create_loan,
    get_user_ip_address,
    list_loan_balance,
    list_loans,
    list_payments,
    pay_loan,
)
from banking.api.views import create_bank_route, create_loan_route, create_payment_route

VALID_UUID = uuid4()
VALID_DECIMAL = Decimal("1000.00")
VALID_DATETIME = datetime(2024, 1, 1, 12, 0)
VALID_DATE = date(2024, 1, 1)
VALID_STR = "Bank A"
VALID_INTEREST = Decimal("2.75")


class TestCreateLoanRequest(TestCase):
    @parameterized.expand([
        ("valid", {"amount": VALID_DECIMAL, "interest_rate": Decimal("1.5"), "installments_qt": 12, "bank_id": VALID_UUID}, True),
        ("missing_amount", {"interest_rate": Decimal("1.5"), "installments_qt": 12, "bank_id": VALID_UUID}, False),
        ("invalid_installments", {"amount": VALID_DECIMAL, "interest_rate": Decimal("1.5"), "installments_qt": 0, "bank_id": VALID_UUID}, False),
    ])
    def test_create_loan_request(self, _, data, is_valid):
        serializer = CreateLoanRequest(data=data)
        assert serializer.is_valid() is is_valid


class TestCreatePaymentSerializer(TestCase):
    @parameterized.expand([
        ("valid", {"loan_id": VALID_UUID, "amount": Decimal("50.00")}, True),
        ("invalid_amount", {"loan_id": VALID_UUID, "amount": Decimal("0.00")}, False),
        ("missing_loan_id", {"amount": Decimal("50.00")}, False),
    ])
    def test_create_payment_serializer(self, _, data, is_valid):
        serializer = CreatePaymentSerializer(data=data)
        assert serializer.is_valid() is is_valid


class TestCreateBankRequest(TestCase):
    @parameterized.expand([
        ("valid", {"name": "Bank X", "country": "USA", "max_loan_amount": VALID_DECIMAL}, True),
        ("missing_name", {"country": "USA", "max_loan_amount": VALID_DECIMAL}, False),
        ("too_long_name", {"name": "A" * 101, "country": "USA", "max_loan_amount": VALID_DECIMAL}, False),
    ])
    def test_create_bank_request(self, _, data, is_valid):
        serializer = CreateBankRequest(data=data)
        assert serializer.is_valid() is is_valid


class TestPaginationQueryParamsSerializer(TestCase):
    def test_valid_pagination(self):
        serializer = PaginationQueryParamsSerializer(data={"page": 2, "limit": 20})
        assert serializer.is_valid()
        assert serializer.validated_data["page"] == 2
        assert serializer.validated_data["limit"] == 20


class TestListLoansQueryParamsSerializer(TestCase):
    def test_valid_query_params(self):
        serializer = ListLoansQueryParamsSerializer(data={
            "page": 1,
            "limit": 10,
            "paid": True,
            "interest_rate": "5.00",
            "amount": "5000.00",
            "bank_name": "Test Bank",
            "request_date": "2024-01-01"
        })
        assert serializer.is_valid()
        assert serializer.validated_data["paid"] is True


class TestListPaymentsQueryParamsSerializer(TestCase):
    def test_valid_filters(self):
        serializer = ListPaymentsQueryParamsSerializer(data={
            "page": 1,
            "limit": 5,
            "payment_id": VALID_UUID,
            "loan_id": VALID_UUID,
            "payment_date": "2024-01-01"
        })
        assert serializer.is_valid()


class TestResponseSerializers(TestCase):
    def test_create_loan_response(self):
        data = {
            "id": VALID_UUID,
            "amount": VALID_DECIMAL,
            "interest_rate": Decimal("1.5"),
            "request_date": VALID_DATETIME,
            "bank_name": VALID_STR,
            "loan_installments": [
                {"id": VALID_UUID, "due_date": VALID_DATETIME, "amount": Decimal("500.00")},
            ]
        }
        serializer = CreateLoanResponse(data=data)
        assert serializer.is_valid()

    def test_create_payment_response(self):
        data = {
            "id": VALID_UUID,
            "payment_date": VALID_DATETIME,
            "amount": Decimal("200.00"),
            "change": Decimal("0.00"),
        }
        serializer = CreatePaymentResponse(data=data)
        assert serializer.is_valid()

    def test_list_loans_response(self):
        data = {
            "id": VALID_UUID,
            "amount": Decimal("1000.00"),
            "interest_rate": Decimal("2.5"),
            "bank_name": "Bank Y",
            "request_date": VALID_DATETIME,
            "outstanding_balance": Decimal("800.00"),
            "loan_installments": [
                {"paid_amount": Decimal("100.00"), "status": "pending"},
            ]
        }
        serializer = ListLoansResponse(data=data)
        assert serializer.is_valid()

    def test_list_payments_response(self):
        data = {
            "id": VALID_UUID,
            "payment_date": VALID_DATETIME,
            "amount": Decimal("150.00"),
            "change": Decimal("0.00"),
            "loan_id": VALID_UUID,
            "bank_name": "Bank Z"
        }
        serializer = ListPaymentsResponse(data=data)
        assert serializer.is_valid()

    def test_loan_statistics_response(self):
        data = {
            "id": VALID_UUID,
            "amount": Decimal("1000.00"),
            "interest_rate": Decimal("2.5"),
            "paid": True,
            "bank_name": "Test Bank",
            "installments_count": 12,
            "paid_installments": 12,
            "pending_installments": 0,
            "overdue_installments": 0,
            "total_paid": Decimal("1000.00"),
            "outstanding_balance": Decimal("0.00"),
            "total_pending": Decimal("0.00"),
            "total_overdue": Decimal("0.00"),
        }
        serializer = LoanStatisticsResponse(data=data)
        assert serializer.is_valid()


class TestCreateLoanModel(TestCase):
    @parameterized.expand([
        ("valid_data", {
            "amount": VALID_DECIMAL,
            "interest_rate": VALID_INTEREST,
            "installments_qt": 12,
            "bank_id": VALID_UUID
        }),
    ])
    def test_valid(self, _, data):
        model = CreateLoanModel(**data)
        assert model.amount == VALID_DECIMAL
        assert model.interest_rate == VALID_INTEREST
        assert model.installments_qt == 12
        assert model.bank_id == VALID_UUID

    @parameterized.expand([
        ("missing_field", {
            "interest_rate": VALID_INTEREST,
            "installments_qt": 12,
            "bank_id": VALID_UUID
        }),
        ("invalid_amount", {
            "amount": Decimal("-1"),
            "interest_rate": VALID_INTEREST,
            "installments_qt": 12,
            "bank_id": VALID_UUID
        }),
        ("zero_installments", {
            "amount": VALID_DECIMAL,
            "interest_rate": VALID_INTEREST,
            "installments_qt": 0,
            "bank_id": VALID_UUID
        }),
    ])
    def test_invalid(self, _, data):
        with self.assertRaises(ValidationError):
            CreateLoanModel(**data)


class TestCreatePaymentModel(TestCase):
    @parameterized.expand([
        ("valid", {"loan_id": VALID_UUID, "amount": 50.0}),
    ])
    def test_valid(self, _, data):
        model = CreatePaymentModel(**data)
        assert model.loan_id == data["loan_id"]
        assert model.amount == data["amount"]

    @parameterized.expand([
        ("missing_loan_id", {"amount": 50.0}),
        ("missing_amount", {"loan_id": VALID_UUID}),
    ])
    def test_invalid(self, _, data):
        with self.assertRaises(ValidationError):
            CreatePaymentModel(**data)


class TestCreateBankModel(TestCase):
    @parameterized.expand([
        ("valid_all_fields", {
            "name": "Bank X",
            "bic": "BIC123",
            "country": "Countryland",
            "interest_policy": "Fixed 2%",
            "max_loan_amount": VALID_DECIMAL,
        }),
        ("valid_optional_missing", {
            "name": "Bank Y",
            "country": "Otherland",
            "max_loan_amount": VALID_DECIMAL,
        }),
    ])
    def test_valid(self, _, data):
        model = CreateBankModel(**data)
        assert model.name == data["name"]
        assert model.country == data["country"]
        assert model.max_loan_amount == VALID_DECIMAL

    @parameterized.expand([
        ("missing_name", {"country": "BR", "max_loan_amount": VALID_DECIMAL}),
        ("negative_max_amount", {
            "name": "Bank Z",
            "country": "BR",
            "max_loan_amount": {"foo"}
        }),
    ])
    def test_invalid(self, _, data):
        with self.assertRaises(ValidationError):
            CreateBankModel(**data)


class TestListLoansQueryParams(TestCase):
    def test_valid(self):
        params = ListLoansQueryParams(
            page=1,
            limit=20,
            paid=True,
            interest_rate=2.5,
            amount=1000.0,
            bank_name="Bank A",
            request_date=VALID_DATE
        )
        assert params.offset == 0
        assert params.bank_name == "Bank A"

    def test_invalid_negative_limit(self):
        with self.assertRaises(ValidationError):
            ListLoansQueryParams(page=1, limit=0)


class TestListPaymentsQueryParams(TestCase):
    def test_valid(self):
        params = ListPaymentsQueryParams(
            page=2,
            limit=10,
            payment_id=VALID_UUID,
            loan_id=VALID_UUID,
            payment_date="2024-01-01"
        )
        assert params.offset == 10
        assert params.payment_date == date(2024, 1, 1)

    @parameterized.expand([
        ("invalid_date_format", "01-01-2024"),
        ("invalid_date_non_string", 123456),
    ])
    def test_invalid_date_format(self, _, date_value):
        with self.assertRaises(ValidationError):
            ListPaymentsQueryParams(payment_date=date_value)


class TestGetUserIpAddress(TestCase):

    @patch("banking.api.utils.utils.Request")
    def test_get_user_ip_address(self, MockRequest):
        mock_request = MockRequest()
        mock_request.META = {
            "HTTP_X_FORWARDED_FOR": "192.168.0.1",
            "REMOTE_ADDR": "127.0.0.1",
        }
        ip_address = get_user_ip_address(mock_request)
        self.assertEqual(ip_address, "192.168.0.1")


class TestCreateBank(TestCase):

    @patch("banking.api.utils.utils.Bank")
    @patch("banking.api.utils.utils.Request")
    def test_create_bank(self, MockRequest, MockBank):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        bank_data = CreateBankModel(
            name="Bank A",
            bic="BICA123",
            country="Country",
            interest_policy="policy",
            max_loan_amount=100000
        )

        MockBank.objects.create.return_value = MagicMock(id=uuid4(), name="Bank A", bic="BICA123", country="Country", interest_policy="policy", max_loan_amount=100000)

        response = create_bank(mock_request, bank_data)

        self.assertEqual(response['interest_policy'], "policy")
        self.assertEqual(response['bic'], "BICA123")

    @patch("banking.api.utils.utils.Bank.objects.create")
    @patch("banking.api.utils.utils.Request")
    def test_create_bank_error(self, MockRequest, MockBankCreate):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        bank_data = CreateBankModel(
            name="Bank A",
            bic="BICA123",
            country="Country",
            interest_policy="policy",
            max_loan_amount=100000
        )

        MockBankCreate.side_effect = Exception("Error creating bank")

        with self.assertRaises(Exception):
            create_bank(mock_request, bank_data)


class TestCreateLoan(TestCase):

    @patch("banking.api.utils.utils.Bank")
    @patch("banking.api.utils.utils.Loan")
    @patch("banking.api.utils.utils.get_user_ip_address")
    @patch("banking.api.utils.utils.uuid4")
    @patch("banking.api.utils.utils.Request")
    def test_create_loan(self, MockRequest, MockUUID, MockGetUserIp, MockLoan, MockBank):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        loan_request = CreateLoanModel(
            bank_id=uuid4(),
            amount=50000,
            interest_rate=5.0,
            installments_qt=12
        )

        mock_bank = MagicMock(id=uuid4(), name="Bank A", max_loan_amount=100000)
        MockBank.objects.filter.return_value.first.return_value = mock_bank

        MockUUID.return_value = uuid4()
        MockGetUserIp.return_value = "127.0.0.1"
        MockLoan.objects.create.return_value = MagicMock(
            id=uuid4(),
            client=mock_request.user,
            bank=mock_bank,
            amount=50000,
            interest_rate=5.0,
            installments_qt=12,
            ip_address="127.0.0.1",
            request_date=datetime.now()
        )

        response = create_loan(mock_request, loan_request)
        self.assertIn('id', response)
        self.assertEqual(response['amount'], 50000)

    @patch("banking.api.utils.utils.Bank")
    @patch("banking.api.utils.utils.Loan")
    @patch("banking.api.utils.utils.get_user_ip_address")
    @patch("banking.api.utils.utils.uuid4")
    @patch("banking.api.utils.utils.Request")
    def test_create_loan_error(self, MockRequest, MockUUID, MockGetUserIp, MockLoan, MockBank):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        loan_request = CreateLoanModel(
            bank_id=uuid4(),
            amount=50000,
            interest_rate=5.0,
            installments_qt=12
        )

        MockBank.objects.filter.return_value.first.return_value = None

        with self.assertRaises(RowNotFound):
            create_loan(mock_request, loan_request)


class TestPayLoan(TestCase):

    @patch("banking.api.utils.utils.Loan")
    @patch("banking.api.utils.utils.Request")
    def test_pay_loan(self, MockRequest, MockLoan):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        payment_request = CreatePaymentModel(loan_id=uuid4(), amount=1000)

        mock_loan = MagicMock(id=uuid4(), client=mock_request.user, paid=False)
        MockLoan.objects.filter.return_value.first.return_value = mock_loan

        mock_payment = MagicMock(id=uuid4(), payment_date=datetime.now(), amount=1000)
        mock_loan.pay.return_value = (mock_payment, 0)

        response = pay_loan(mock_request, payment_request)
        self.assertEqual(response["amount"], 1000)

    @patch("banking.api.utils.utils.Loan")
    @patch("banking.api.utils.utils.Request")
    def test_pay_loan_already_paid(self, MockRequest, MockLoan):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        payment_request = CreatePaymentModel(loan_id=uuid4(), amount=1000)

        mock_loan = MagicMock(id=uuid4(), client=mock_request.user, paid=True)
        MockLoan.objects.filter.return_value.first.return_value = mock_loan

        with self.assertRaises(LoanAlreadyPaid):
            pay_loan(mock_request, payment_request)


class TestListLoans(TestCase):

    @patch("banking.api.utils.utils.connection.cursor")
    @patch("banking.api.utils.utils.ListLoansQueryParams")
    @patch("banking.api.utils.utils.Request")
    def test_list_loans(self, MockRequest, MockListLoansQueryParams, MockCursor):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        query_params = ListLoansQueryParams(limit=10, offset=0)

        MockCursor.return_value.__enter__.return_value.__iter__.return_value = iter([
            (uuid4(), 50000, 5.0, False, datetime.now(), "Bank A", 10000, 12)
        ])

        response = list_loans(mock_request, query_params)
        self.assertGreater(len(response), 0)

    @patch("banking.api.utils.utils.connection.cursor")
    @patch("banking.api.utils.utils.ListLoansQueryParams")
    @patch("banking.api.utils.utils.Request")
    def test_list_loans_error(self, MockRequest, MockListLoansQueryParams, MockCursor):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        query_params = ListLoansQueryParams(limit=10, offset=0)

        mock_cursor = MagicMock()
        MockCursor.side_effect = Exception("Error retrieving loans")

        with self.assertRaises(Exception):
            list_loans(mock_request, query_params)


class TestListLoanBalance(TestCase):

    @patch("banking.api.utils.utils.connection.cursor")
    @patch("banking.api.utils.utils.Request")
    def test_list_loan_balance(self, MockRequest, MockCursor):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        loan_id = uuid4()

        mock_cursor = MagicMock()
        MockCursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (
            loan_id,
            50000,
            5.0,
            False,
            "Bank A",
            12,
            6,
            6,
            20000,
            30000,
            10000,
            0,
            0
        )

        response = list_loan_balance(mock_request, loan_id)
        self.assertEqual(response['amount'], 50000)

    @patch("banking.api.utils.utils.connection.cursor")
    @patch("banking.api.utils.utils.Request")
    def test_list_loan_balance_error(self, MockRequest, MockCursor):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        loan_id = uuid4()

        mock_cursor = MagicMock()
        MockCursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = Exception("Error retrieving loan balance")

        with self.assertRaises(Exception):
            list_loan_balance(mock_request, loan_id)


class TestListPayments(TestCase):

    @patch("banking.api.utils.utils.connection.cursor")
    @patch("banking.api.utils.utils.ListPaymentsQueryParams")
    @patch("banking.api.utils.utils.Request")
    def test_list_payments(self, MockRequest, MockListPaymentsQueryParams, MockCursor):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        query_params = ListPaymentsQueryParams(limit=10, offset=0)

        MockCursor.return_value.__enter__.return_value.__iter__.return_value = iter([
            (uuid4(), datetime.now(), 1000, uuid4(), "Bank A")
        ])

        response = list_payments(mock_request, query_params)
        self.assertGreater(len(response), 0)

    @patch("banking.api.utils.utils.connection.cursor")
    @patch("banking.api.utils.utils.ListPaymentsQueryParams")
    @patch("banking.api.utils.utils.Request")
    def test_list_payments_error(self, MockRequest, MockListPaymentsQueryParams, MockCursor):
        mock_request = MockRequest()
        mock_request.user = MagicMock(id=1)
        query_params = ListPaymentsQueryParams(limit=10, offset=0)

        MockCursor.side_effect = Exception("Error retrieving payments")

        with self.assertRaises(Exception):
            list_payments(mock_request, query_params)


class TestListLoansQuery:
    @parameterized.expand([
        (
            ListLoansQueryParams(client_id=1, paid=None, interest_rate=None, amount=None, bank_name=None, request_date=None, limit=10, offset=0),
            ["l.client_id = %(client_id)s", "limit %(limit)s", "offset %(offset)s"]
        ),
        (
            ListLoansQueryParams(client_id=1, paid=True, interest_rate=None, amount=1000, bank_name="Bank A", request_date="2025-01-01", limit=10, offset=0),
            ["l.client_id = %(client_id)s", "l.paid = %(paid)s", "l.amount = %(amount)s", "b.name = %(bank_name)s", "date(l.request_date) = %(request_date)s", "limit %(limit)s", "offset %(offset)s"]
        ),
    ])
    def test_list_loans_query(self, query_params, expected_substrings):
        result = list_loans_query(query_params)
        for substring in expected_substrings:
            assert substring in result


class TestListPaymentsQuery:
    @parameterized.expand([
        (
            ListPaymentsQueryParams(client_id=1, payment_id=None, loan_id=None, payment_date=None, limit=10, offset=0),
            ["al.client_id = %(client_id)s", "limit %(limit)s", "offset %(offset)s"]
        ),
        (
            ListPaymentsQueryParams(client_id=1, payment_id=VALID_UUID, loan_id=VALID_UUID, payment_date="2025-01-01", limit=10, offset=0),
            ["al.client_id = %(client_id)s", "ap.id = %(payment_id)s", "ap.loan_id = %(loan_id)s", "date(ap.payment_date) = %(payment_date)s", "limit %(limit)s", "offset %(offset)s"]
        ),
    ])
    def test_list_payments_query(self, query_params, expected_substrings):
        result = list_payments_query(query_params)
        for substring in expected_substrings:
            assert substring in result


class TestCreateLoanRoute(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username='foo', password='test123')
        self.factory = APIRequestFactory()
        self.bank_id = uuid4()

    @patch('banking.api.views.create_loan', return_value={'foo': 'foo'})
    def test_create_loan_route_success(self, mock_create_loan):
        """Test successful loan creation"""
        request = self.factory.post('/loan', {
            'amount': 1000.0,
            'interest_rate': 5.0,
            'installments_qt': 10,
            'bank_id': str(self.bank_id),
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
        self.assertIn('invalid_field', str(response.data))

    @patch('banking.api.views.create_loan', side_effect=FailedToCreateInstallments('foo'))
    def test_create_loan_route_failed_to_create_installments(self, mock_create_loan):
        """Test loan creation where the loan is already paid"""
        request = self.factory.post('/loan', {
            'amount': 1000.0,
            'bank_id': self.bank_id,
            'interest_rate': 5.0,
            'installments_qt': 10,
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_loan_route(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual({'error': 'Error while creating loan installments'}, response.data)
        mock_create_loan.assert_called_once()

    @patch('banking.api.views.create_loan', side_effect=RowNotFound('Bank not found'))
    def test_create_loan_route_bank_not_found(self, mock_create_loan):
        """Test loan creation where the bank is not found"""
        request = self.factory.post('/loan', {
            'amount': 1000.0,
            'bank_id': str(uuid4()),
            'interest_rate': 5.0,
            'installments_qt': 10,
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_loan_route(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Bank not found', str(response.data))
        mock_create_loan.assert_called_once()

class TestCreateBankRoute(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username='foo', password='test123')
        self.factory = APIRequestFactory()

    @patch('banking.api.views.create_bank', return_value={'name': 'Test Bank'})
    def test_create_bank_route_success(self, mock_create_bank):
        """Test successful bank creation"""
        request = self.factory.post('/bank', {
            'name': 'foo',
            'bic': 'foo',
            'country': 'foo',
            'interest_policy': 'foo',
            'max_loan_amount': 100,
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_bank_route(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'name': 'Test Bank'})
        mock_create_bank.assert_called_once()

    def test_create_bank_route_invalid_payload(self):
        """Test bank creation with invalid payload"""
        request = self.factory.post('/bank', {
            'invalid_field': 'value'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_bank_route(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Field required', response.data)

class TestCreatePaymentRoute(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username='foo', password='test123')
        self.factory = APIRequestFactory()
        self.loan = MagicMock(id=uuid4(), amount=1000.0, paid=True)

    @patch('banking.api.views.pay_loan', return_value={'payment_status': 'success'})
    def test_create_payment_route_success(self, mock_create_payment):
        """Test successful payment creation"""
        request = self.factory.post('/payment', {
            'loan_id': self.loan.id,
            'amount': 500.0
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_payment_route(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'payment_status': 'success'})
        mock_create_payment.assert_called_once()

    def test_create_payment_route_invalid_payload(self):
        """Test payment creation with invalid payload"""
        request = self.factory.post('/payment', {
            'invalid_field': 'value'
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_payment_route(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Field required', response.data)

    @patch('banking.api.views.pay_loan', side_effect=LoanAlreadyPaid('Loan is already paid'))
    def test_create_payment_route_loan_already_paid(self, mock_create_payment):
        """Test payment creation where the loan is already paid"""
        request = self.factory.post('/payment', {
            'loan_id': self.loan.id,
            'amount': 500.0
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_payment_route(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual({'error': 'Loan has already been paid'}, response.data)
        mock_create_payment.assert_called_once()

    @patch('banking.api.views.pay_loan', side_effect=RowNotFound('Loan not found'))
    def test_create_payment_route_loan_not_found(self, mock_create_payment):
        """Test payment creation where the loan is not found"""
        request = self.factory.post('/payment', {
            'loan_id': str(uuid4()),
            'amount': 500.0
        }, format='json')
        force_authenticate(request, user=self.user)

        response = create_payment_route(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Loan not found', str(response.data))
        mock_create_payment.assert_called_once()
