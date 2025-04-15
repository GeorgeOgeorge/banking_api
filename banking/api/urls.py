from django.urls import path

from banking.api.views import create_loan_request

urlpatterns = [
    path('loans/', create_loan_request, name='create_loan'),
]
