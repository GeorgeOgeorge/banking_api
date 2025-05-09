from django.urls import path

from banking.api.views import (
    create_bank_route,
    create_loan_route,
    create_payment_route,
    list_loans_route,
    list_payments_route,
    loan_statistics_route,
)

urlpatterns = [
    path('bank/create/', create_bank_route, name='create_bank'),

    path('loan/create/', create_loan_route, name='create_loan'),
    path('loan/', list_loans_route, name='list_loan'),
    path('loan/<uuid:loan_id>/statistics/', loan_statistics_route, name='loan_statistics'),

    path('payment/create/', create_payment_route, name='create_payment'),
    path('payment/', list_payments_route, name='list_payments_by_loan'),
]
