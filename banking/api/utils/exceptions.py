class RowNotFound(Exception):
    '''Raised when the specified fetch is not found.'''
    pass


class FailedToCreateInstallments(Exception):
    '''Raised when an error occours while creating loan installments.'''
    pass


class LoanAlreadyPaid(Exception):
    '''Raised when trying to pay already paid loan.'''
    pass
