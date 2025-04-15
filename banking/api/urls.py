from django.urls import path

from banking.api.views import (create_loan_route, create_payment_route, list_loans_route)

urlpatterns = [
    path('loans/create', create_loan_route, name='create_loans'),
    path('loans/', list_loans_route, name='list_loans'),

    path('payments/create', create_payment_route, name='create_payment'),
]
