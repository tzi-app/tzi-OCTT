"""
Test case name      Authorization with prepaid card - no credit
Test case Id        TC_C_104_CSMS
Use case Id(s)      C17
Requirement(s)      C17.FR.02

Requirement Details:
    C17.FR.02: CSMS SHALL respond with an AuthorizeResponse with idTokenInfo that has status = NoCredit and
               cacheExpiryDateTime set to current date/time.
        Precondition: CSMS receives an AuthorizeRequest for an idToken that is valid and associated with a
                      prepaid account that does not have a positive balance
        Note: Prepaid token is not allowed to remain in the local authorization cache.
System under test   CSMS

Description         This test case verifies if the CSMS is able to authorize a prepaid card for a transaction.

Purpose             To verify if the CSMS is able to reject a prepaid card for a transaction.

Prerequisite(s)     - CSMS supports prepaid cards.
                    - Prepaid card with an amount of "0" is available.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a AuthorizeRequest with
    - idToken.idToken <prepaid card no credit id>
    - idToken.type = <prepaid card no credit id type>
2. The CSMS responds a AuthorizeResponse

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status NoCredit
    - idTokenInfo.cacheExpiryDateTime <current date/time>

Post scenario validations:
    N/a
"""
