from banking.api.utils.serializers import ListPaymentsQueryParams

LIST_LOAN_QUERY = '''
    select
        al.id,
        al.amount,
        al.interest_rate,
        ab.name as bank_name,
        al.request_date
    from
        api_loan al
    join auth_user au on al.client_id = au.id
    join api_bank ab on al.bank_id = ab.id
    where au.id = %(client_id)s
    order by request_date desc
    limit %(limit)s offset %(offset)s;
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
