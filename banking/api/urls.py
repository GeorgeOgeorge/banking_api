from django.urls import path

from banking.api.views import (
    create_loan_route,
    create_payment_route,
    list_loan_balance_route,
    list_loans_route,
    list_payments_route
)

urlpatterns = [
    path('loans/create/', create_loan_route, name='create_loans'),
    path('loans/', list_loans_route, name='list_loans'),
    path('loans/<uuid:loan_id>/balance/', list_loan_balance_route, name='list_loan_balance'),

    path('payments/create/', create_payment_route, name='create_payment'),
    path('payments/', list_payments_route, name='list_payments_by_loan'),
]
