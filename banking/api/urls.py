from django.urls import path

from banking.api.views import (
    create_loan_request,
    list_loans_route
)

urlpatterns = [
    path('loans/create', create_loan_request, name='create_loans'),
    path('loans/', list_loans_route, name='list_loans'),
]
