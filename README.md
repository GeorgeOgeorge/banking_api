# Banking Loan API

This project provides a simple API for managing bank loans using Django and Django Rest Framework. It supports operations such as creating a loan, retrieving loan details, and calculating the total loan amount with interest.

## Features

- Create a loan
- Retrieve loan details by loan ID
- Calculate total amount to be paid with interest
- Admin authentication using Django's superuser
- Full test coverage for all routes

## Technologies Used

- Python 3.12
- Django 5.0
- Django Rest Framework
- PostgreSQL
- Pytest and unittest for testing

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/banking-loan-api.git
   cd banking-loan-api
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:

   ```bash
   python manage.py migrate
   ```

5. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

6. Run the server:

   ```bash
   python manage.py runserver
   ```

## Running Tests

```bash
pytest
```

or using Django test runner:

```bash
python manage.py test
```

## Project Structure

```
banking/
├── api/               # Application code
│   ├── views.py       # API views
│   ├── services.py    # Business logic
│   ├── models.py      # Database models
│   └── tests/         # Unit tests
├── settings.py        # Django project settings
├── urls.py            # URL routing
└── manage.py
```
