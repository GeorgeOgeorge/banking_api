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

LIST_LOAN_QUERY = """
    select
        al.id,
        al.amount,
        al.interest_rate,
        al.request_date,
        al.bank
    from
        api_loan al
    join auth_user au on al.client_id = au.id
    where au.id = %(client_id)s
    order by request_date desc
    limit %(limit)s offset %(offset)s;
"""
