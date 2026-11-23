"""
Test case name      Local start transaction - Authorization Expired
Test case Id        TC_C_07_CSMS
Use case Id(s)      C01
Requirement(s)      C01.FR.07

Requirement Details:
    C01.FR.07: AuthorizeResponse SHALL include an authorization status value indicating acceptance or a reason
               for rejection.
        Note: See AuthorizationStatusEnumType for the possible reasons of rejection.
System under test   CSMS

Description         When a Charging Station needs to charge an EV, it needs to authorize the EV Driver first
                    at the CSMS before the charging can be started or stopped.

Purpose             To verify whether the CSMS is able to report that an idToken is Expired.

Prerequisite(s)     N/a

Configuration State The IdToken configured as Expired at the Test System, must be set as Expired at the CSMS.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured expired_idtoken_idtoken>
    - idToken.type <Configured expired_idtoken_type>
2. The CSMS responds with an AuthorizeResponse

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status Expired or Invalid

Post scenario validations:
    N/a
"""
