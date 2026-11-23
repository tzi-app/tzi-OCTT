"""
Test case name      Authorization with prepaid card - success
Test case Id        TC_C_103_CSMS
Use case Id(s)      C17
Requirement(s)      C17.FR.01, C17.FR.03

Requirement Details:
    C17.FR.01: CSMS SHALL respond with an AuthorizeResponse with idTokenInfo with status = Accepted and
               cacheExpiryDateTime set to current date/time.
        Precondition: CSMS receives an AuthorizeRequest for an idToken that is valid and associated with a
                      prepaid account that has a positive balance
        Note: Prepaid token is not allowed to remain in the local authorization cache.
    C17.FR.03: CSMS SHALL include (only one time) the field transactionLimit.maxCost, set to the maximum
               amount that may be spent, in the TransactionEventResponse
        Precondition: CSMS receives an TransactionEventRequest with an idToken that is valid and associated
                      with a prepaid account that has a positive balance
        Note: See also E16 - Transactions with fixed cost, energy, SoC or time.
System under test   CSMS

Description         This test case verifies if the CSMS is able to authorize a prepaid card for a transaction.

Purpose             To verify if the CSMS is able to authorize a prepaid card for a transaction.

Prerequisite(s)     - CSMS supports prepaid cards.
                    - Prepaid card with positive amount is available.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a AuthorizeRequest with
    - idToken.idToken <prepaid card id>
    - idToken.type = <prepaid card id type>
2. The CSMS responds a AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Started
    - idToken.idToken <prepaid card id>
    - idToken.type = <prepaid card id type>
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.cacheExpiryDateTime <current date/time>
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.cacheExpiryDateTime <cacheExpiryDateTime from step 2>
    - transactionLimit.maxCost = <not omitted>

Post scenario validations:
    N/a
"""
