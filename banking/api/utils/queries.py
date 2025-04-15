CREATE_LOAN_QUERY = """
    INSERT INTO api_loan (id, client_id, amount, interest_rate, bank, client_name, ip_address, request_date)
    VALUES (
        gen_random_uuid(),
        %(client_id)s,
        %(amount)s,
        %(interest_rate)s,
        %(bank)s,
        %(client_name)s,
        %(ip_address)s,
        NOW()
    )
    RETURNING id, client_id, amount, interest_rate, bank, client_name, ip_address, request_date
"""