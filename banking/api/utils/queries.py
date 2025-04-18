from banking.api.utils.serializers import ListPaymentsQueryParams

CREATE_LOAN_QUERY = '''
    INSERT INTO api_loan (id, client_id, amount, interest_rate, bank_id, client_name, ip_address, request_date)
    VALUES (
        gen_random_uuid(),
        %(client_id)s,
        %(amount)s,
        %(interest_rate)s,
        %(bank_id)s,
        %(client_name)s,
        %(ip_address)s,
        NOW()
    )
    RETURNING id, client_id, amount, interest_rate, bank_id, client_name, ip_address, request_date
'''

LIST_LOAN_QUERY = '''
    select
        al.id,
        al.amount,
        al.interest_rate,
        al.request_date,
        ab.name as bank_name
    from
        api_loan al
    join auth_user au on al.client_id = au.id
    join api_bank ab on al.bank_id = ab.id
    where au.id = %(client_id)s
    order by request_date desc
    limit %(limit)s offset %(offset)s;
'''

USER_OWNS_LOAN = '''
    select
        al.id
    from
        api_loan al
    join auth_user au on
        al.client_id = au.id
    where
        au.id = %(client_id)s
        and al.id = %(loan_id)s
    limit 1;
'''

CREATE_PAYMENT_QUERY = '''
    insert into api_payment (id, payment_date, amount, loan_id)
    values(
        gen_random_uuid(),
        now(),
        %(amount)s,
        %(loan_id)s
    )
    returning id, payment_date, amount, loan_id;
'''

LIST_LOAN_BALANCE_QUERY = '''
    select
        al.id,
        ab.name as bank_name,
        al.amount,
        al.interest_rate,
        al.request_date,
        coalesce(sum(p.amount), 0) total_paid,
        round(
            (
                al.amount +
                (al.amount * al.interest_rate * greatest(date_part('month', current_date - al.request_date), 0))
                - coalesce(sum(p.amount), 0)
            )::numeric,
            2
        ) as remaining_debt
    from api_loan al
    join api_bank ab on al.bank_id = ab.id
    left join api_payment p on p.loan_id = al.id
    where al.client_id = %(client_id)s
        and al.id = %(loan_id)s
    group by al.id, ab.name
    limit 1;
'''

CREATE_BANK_QUERY = '''
    insert into api_bank (id, name, bic, country, interest_policy, max_loan_amount, created_at, created_by_id)
    values (
        gen_random_uuid(),
        %(name)s,
        %(bic)s,
        %(country)s,
        %(interest_policy)s,
        %(max_loan_amount)s,
        now(),
        %(created_by)s,
    )
    returning id, name, bic, country, interest_policy, max_loan_amount;
'''


def list_payments_query(query_params: ListPaymentsQueryParams) -> str:
    query = '''
        select
            ap.id,
            ap.payment_date,
            ap.amount,
            ap.loan_id
        from
            api_payment ap
        join api_loan al on
            al.id = ap.loan_id
        where
            al.client_id = %(client_id)s
    '''

    if query_params.payment_id:
        query += ' and ap.id = %(payment_id)s'
    if query_params.loan_id:
        query += ' and ap.loan_id = %(loan_id)s'
    if query_params.payment_date:
        query += ' and date(ap.payment_date) = %(payment_date)s'

    query += '''
        order by ap.payment_date desc
        limit %(limit)s offset %(offset)s;
    '''

    return query
