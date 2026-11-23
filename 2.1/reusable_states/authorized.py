"""
State               Authorized
System under test   CSMS
Description         This state will simulate that the EV Driver is locally authorizing to start a transaction
                    on the simulated Charging Station.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

1. The Test System sends an AuthorizeRequest With idToken.idToken <Configured valid_idtoken_idtoken>
   idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest With triggerReason is Authorized
   idToken.idToken <Configured valid_idtoken_idtoken>
   idToken.type <Configured valid_idtoken_type>

If State is EVConnectedPreSession then
    eventType is Updated
else
    eventType is Started

4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2: Message: AuthorizeResponse - idTokenInfo.status must be Accepted
* Step 4: Message: TransactionEventResponse - idTokenInfo.status must be Accepted
Post condition      State is Authorized
"""
