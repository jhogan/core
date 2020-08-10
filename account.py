# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related to the tracking of
accounting and budgeting data.

These entity objects are based on the "Accounting and Budgetting"
chapter of "The Data Model Resource Book".

Examples:
    See test.py for examples. 

Todo:
"""

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import orm
import party
import product
import invoice

class accounts(orm.entities): pass
class types(orm.entities): pass
class account_organizations(orm.associations): pass
class periods(orm.entities): pass
class periodtypes(orm.entities): pass
class transactions(orm.entities): pass
class details(orm.entities): pass
class transactiontypes(orm.entities): pass
class internals(transactions): pass
class depreciations(internals): pass
class capitalizations(internals): pass
class amortizations(internals): pass
class variances(internals): pass
class others(internals): pass
class externals(transactions): pass
class obligations(externals): pass
class notes(obligations): pass
class taxes(obligations): pass
class otherobligations(obligations): pass
class memos(obligations): pass
class creditlines(obligations): pass
class sales(obligations): pass
class creditlines(obligations): pass
class payments(externals): pass
class receipts(payments): pass
class disbursements(payments): pass

class account(orm.entity):
    """ Represents a type of financial reporting bucket to which
    transactions are posted, for example a "cash" account or a
    "supplies expense" account".

    Each general ledger (GL) account may be categorized by one and only one
    general ledger account type (``type``) to specify the account.

    Each internal organization (``party.organization``) may be
    using many GL ``accounts``, and ech GL ``account`` may be associated
    with more than one internal organization. The
    ``account_organization`` resolves this many-to-many relationship.

    Note that this entity was originally called GENERAL LEDGER ACCOUNT in
    "The Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('description', None)

    # The key to a GL account is the ``number`` attribute. It is filled
    # with a *non-meaningful* unique number.
    number = str

    # The name of the account that will be used for reporting purposes
    # in financial statements
    name = str

    # Provides a definition behind the account to ensure that it is
    # understood properly
    description = text

class type(orm.entity):
    """ Each general ledger ``account`` may be categorized by one and only one
    general ledger account type (``type``) to specify the
    ``account``. Valid classifications include:  "asset", "liability",
    "owners equity", "revenue", and "expense".

    This information provides a mechanism to group information on
    financial statements. The "asset", "liability", and "owners equity"
    categories, along with the associated GL ``accounts``, are generally
    used for the organization's balance sheet. The "revenue" and
    "expense" categories are generally used for the income statement.

    Note that this entity was originally called GENERAL LEDGER ACCOUNT
    TYPE in "The Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    # All the accounts that are categorized by this object
    accounts = accounts

class account_organization(orm.association):
    """ Each internal organization (``party.organization``) may
    be using many GL ``accounts``, and ech GL ``account`` may be
    associated with more than one internal organization. This
    association resolves this many-to-many relationship.

    ``account_organization`` is a very significant entity because it
    represents the instance of a general ledger for a particular
    internal organization. For instance, accounting transactions will be
    related to this association, thus allowing maintenance of all the
    transactions for a particular balance sheet or income statement
    account.

    Note that this entity was originally called ORGANIZATION GL ACCOUNT
    in "The Data Model Resource Book".
    """

    # The general ledger ``account`` side of this association
    account = account

    # NOTE The book says ``organization`` should be a
    # ``party.internalorganization``. However, that is a party role, and
    # the book seems to want this to refer to actual organizations like
    # companies.

    # The organization side of this association.
    organization = party.organization

    # Indicates when general ledger accounts were added to an internal
    # organization's chart of accounts and for what period of time they
    # were valid.
    span = timespan

class period(orm.entity):
    """ Represents an accounting period, i.e., the periods of time that
    the organization uses for its financial reporting. This may be to
    define a fiscal year, fiscal quarter, fiscal month, calendar year,
    calendar month, or any other time period that is available in the
    ``periodtype``. 
    
    Each internal organization (``party.organization``) needs to
    establish the accounting ``period`` for which it reports its
    business activities. 
    
    Each accounting period is of a ``periodtype`` such as "fiscal year",
    "calendar year", "fiscal quarter", and so on.

    Note that this entity was originally called ACCOUNTING PERIOD in
    "The Data Model Resource Book".
    """

    # Identifies the relative number of the accounting period. For
    # instance, if there are 13 accounting periouds in a year, the
    # ``number`` would vary form 1 to 13 for this type of period.
    number = int

    # A datespan to defines the time period for each instance
    span = datespan

    # Each accounting ``period`` may be within one and only one
    # accounting ``period``, thus a recursive relationship is provided.
    # This allows monthly periods to be rolled up to quarters, which can
    # be rolled up to years.
    periods = periods

    # The organization using the accounting ``period`` for its financial
    # reporting.
    organization = party.organization

class periodtype(orm.entity):
    """ Each accounting period is of a ``periodtype`` such as "fiscal year",
    "calendar year", "fiscal quarter", and so on.

    Note that this entity was originally called PERIOD TYPE in "The Data
    Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    periods = periods

''' Transactions '''

class transaction(orm.entity):
    """ A supertype that encompasses all the transactions that affect the
    financial statmentes of an enterprise.

    There are two main types of transactions: ``internal`` and
    ``external``. ``internal`` transactions are adjustment transactions
    that affect only the books of the internal organization being
    affected. ``external`` involve are those that involve transactions
    with a party (``party.party``) that is external to the enterprise
    for whom the books are kept.

    Each ``transaction`` must be composed of one or more transaction
    ``detail`` objects. 

    Note that this entity was originally called ACCOUTING TRANSACTION in
    "The Data Model Resource Book".
    """

    # TODO Write validation rule to ensure that each transaction has
    # at least one debit and one credit `detail`. 

    # Note that there is no ``amount`` attribute because the transaction
    # amounts are maintained in the transaction ``detail`` class.

    # Describes the details behind the transaction.
    description = text

    # The date on which the entry was made into the system. (The book
    # calls this the **entry date**.) NOTE This may be redundant with
    # ``createdat``.
    entered = datetime

    # The date on which the transaction occurred. (The book calls this
    # the **transaction date**.)
    transacted = datetime

class detail(orm.entity):
    """ Transaction ``detail``s represents the debit and credit entries
    for a given transaction. each debit or credit entry will affect one
    of the ``internalorganization``'s accounts and therefore is related to
    the ``account_organization`` association, which is the bucket for a
    general ledger ``account`` for an ``internalorganization``.
    
    Each ``transaction`` must be composed of one or more transaction
    ``detail`` objects. Transaction ``details`` show how ecah part of
    the transaction affects a specific ``account_organization`` (aka
    ORGANIZATION GL ACCOUNT) association. A ``detail`` instance
    corresponds to a "journal entry line item" in accounting terms.

    The ``detail`` class facilities the principles of double-entry
    accounting; that each transaction has at least two ``detail``
    records, a debit and a credit.

    Note that this entity was originally called TRANSACTION DETAIL In
    "The Data Model Resource Book".
    """

    # TODO Write iscredit and isdebit properties


    # The currency (e.g., dollar) amount of the transaction ``detail``.
    # If the ``amount`` is negative, the detail is considered a *debit*,
    # otherwise it's considered a *credit*.
    amount = dec

class transactiontype(orm.entity):
    """ Provides a specific low-level categorization of each
    transaction. ``transactiontypes`` may include further breakdowns of
    the subentities such as "Payment Recept for Asset Sale" or "Payment
    Disbursement for Purchase Order".

    Note that this entity was originally called ACCOUNTING TRANSACTION
    TYPE In "The Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    transactions = transactions

class internal(transaction):
    """ ``internal`` transactions identify transactions that serve as
    adjustments to the books of an internal organization
    (party.internal). Because there is only one organization
    involved in the transaction (namely, the internal organization whose
    books are being adjusted), there is a single relationship to an
    ``internalorganization``.

    Note that this entity was originally called ITERNAL ACCTG TRANS in
    "The Data Model Resource Book".
    """

    internal = party.internal

class depreciation(internal):
    """
    Note that this entity was originally called DEPRECIATION in
    "The Data Model Resource Book".
    """

class capitalization(internal):
    """
    Note that this entity was originally called CAPITALIZATION in
    "The Data Model Resource Book".
    """

class amortization(internal):
    """
    Note that this entity was originally called CAPITALIZATION in
    "The Data Model Resource Book".
    """

class variance(internal):
    """
    Note that this entity was originally called ITEM VARIANCE ACCTG
    TRANS in "The Data Model Resource Book".
    """

    # The product.variance from which this entity originated.
    variance = product.variance

class other(internal):
    """ Documents adjustments to the internal organization's financial
    position.

    Note that this entity was originally called OTHER INTERNAL ACCTG
    TRANS in "The Data Model Resource Book".
    """

class external(other):
    """ ``external`` models accounting transactions that affect two
    parties. An ``external`` transaction may be either an
    ``obligation`` transaction or a ``payment`` transaction. An
    ``obligation`` transaction represents a transaction where one party
    has recognized that it owes moneys to another party. Therefore, the
    ``sender`` and ``receiver`` identify the parties involved on both
    sides of a transaction. A ``payment`` transaction represents a
    transaction where one party is paying another party; therefore it
    also relates to two parties.
    
    Note that this entity was originally called EXTERNAL ACCTG TRANS in
    "The Data Model Resource Book".
    """

    sender = party.party
    receiver = party.party

class obligation(external):
    """ A type of ``external`` ``transaction`` that represents different
    forms of a party owing moneys to another party (``party.party``). 

    Note that this entity was originally called OBLIGATION ACCTG TRANS
    in "The Data Model Resource Book".
    """

class note(obligation):
    """ Represents either a note payable, where the internal
    organization owes money, or a note receivable, where the
    organization is due money.
    """

class tax(obligation):
    """ An ``obligation`` to pay taxes to government agencies.
    """
    entities = taxes

class otherobligation(obligation):
    pass

class memo(obligation):
    """ A credit ``memo`` is a transaction where credit is given from
    one party (``party.party``) to another party.
    Note that this entity was originally called CREDIT MEMO in
    "The Data Model Resource Book".
    """

class creditline(obligation):
    """ Represents money actually borrowed from a line of credit
    extended from a financial institute to another party
    (``party.party``).
    """

class sale(obligation):
    """ Represent the obligation to pay for products sold.

    Note that this entity was originally called SALES ACCTG TRANS in
    "The Data Model Resource Book".
    """

    # The invoice from which the ``sale``s account transaction
    # originated.
    invoice = invoice.invoice

class payment(external):
    """ A type of ``external`` ``transaction`` that represents
    collections of moneys received by an ``internalorganization`` (in
    the case of a ``receipt`` transaction) or payments of moneys sent by
    an internal organization (in the case of a ``disbursement``
    transaction). A payment made from one ``internalorganization`` to
    another ``internalorganization`` results in two ``payment``
    instances; one ``internalorganization`` will record a ``receipt``,
    and the other ``internalorganization`` will record a
    ``disbursement``.

    Note that this entity was originally called PAYMENT ACCTG TRANS in
    "The Data Model Resource Book".
    """

    # The ``payment`` for which this entity originated.
    payment = invoice.payment

class receipt(payment):
    """ Represents moneys coming in.

    Note that this entity was originally called RECEIPT ACCTG TRANS in
    "The Data Model Resource Book".
    """

class disbursement(payment):
    """ Represents moneys going out.

    Note that this entity was originally called DISBURSMENT ACCTG TRANS in
    "The Data Model Resource Book".
    """
