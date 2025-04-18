from banking.api.utils.serializers import ListLoansQueryParams, ListPaymentsQueryParams

LOAN_STATISTICS_QUERY = """
    select
        l.id,
        l.amount,
        l.interest_rate,
        l.paid,
        b.name as bank_name,
        count(li.id) as installments_count,
        count(*) filter (where li.status = 'paid') as paid_installments,
        count(*) filter (where li.status = 'pending') as pending_installments,
        count(*) filter (where li.status = 'overdue') as overdue_installments,
        coalesce(sum(li.paid_ammount), 0) as total_paid,
        coalesce(sum(li.amount - li.paid_ammount), 0) as outstanding_balance,
        coalesce(sum(case when li.status = 'pending' then li.amount - li.paid_ammount else 0 end), 0) as total_pending,
        coalesce(sum(case when li.status = 'overdue' then li.amount - li.paid_ammount else 0 end), 0) as total_overdue
    from api_loan l
    join api_bank b on l.bank_id = b.id
    left join api_loaninstallment li on li.loan_id = l.id
    where l.id = %(loan_id)s
        and l.client_id = %(client_id)s
    group by l.id, l.amount, l.interest_rate, l.paid, b.name;
"""


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


def list_loans_query(query_params: ListLoansQueryParams) -> str:
    query = """
        select
            l.id,
            l.amount,
            l.interest_rate,
            l.paid,
            l.request_date,
            b.name as bank_name,
            coalesce(sum(li.amount - li.paid_ammount), 0) as outstanding_balance,
            json_agg(json_build_object(
                'id', li.id,
                'due_date', li.due_date,
                'amount', li.amount,
                'paid_ammount', li.paid_ammount,
                'status', li.status
            ) order by li.due_date) as loan_installments
        from api_loan l
        join api_bank b on l.bank_id = b.id
        left join api_loaninstallment li on li.loan_id = l.id
        where l.client_id = %(client_id)s
    """

    if query_params.paid is not None:
        query += ' and l.paid = %(paid)s'
    if query_params.interest_rate is not None:
        query += ' and l.interest_rate = %(interest_rate)s'
    if query_params.amount is not None:
        query += ' and l.amount = %(amount)s'
    if query_params.bank_name:
        query += ' and b.name = %(bank_name)s'
    if query_params.request_date:
        query += ' and date(l.request_date) = %(request_date)s'

    query += '''
        group by
            l.id, l.amount, l.interest_rate, l.paid, l.request_date, b.name
        order by l.request_date desc
        limit %(limit)s offset %(offset)s;
    '''

    return query
