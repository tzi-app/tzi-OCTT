"""
Test case name      Show EV Driver running total cost during charging - costUpdatedRequest
Test case Id        TC_I_01_CSMS
Use case Id(s)      I02
Requirement(s)      I02.FR.01

Requirement Details:
    I02.FR.01: The CSMS SHALL send either a CostUpdatedRequest at a relevant interval/moment or return the
               running cost in a TransactionEventResponse. This might depend on the charging speed, running
               cost, etc.
System under test   CSMS

Description         While a transaction is ongoing, the driver wants to know how much the running total cost
                    is, updated at a relevant interval.

Purpose             To verify if the CSMS is able to correctly send the running total cost as described in the
                    OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - eventType Updated
4. The CSMS responds with a TransactionEventResponse
5. Execute Reusable State EVConnectedPreSession
6. Execute Reusable State EnergyTransferStarted
7. The Test System sends a TransactionEventRequest With
    - triggerReason is MeterValuePeriodic
    - eventType is Updated
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured sampled Meter Values interval>.
    - sampledValue.context is Sample.Periodic
    Note(s):
    _- This step will be executed every _<Configured sampled Meter Values interval>
    - The Test System will end the testcase after two MeterValues.
8. The CSMS responds with a TransactionEventResponse
9. The CSMS sends a CostUpdatedRequest
    Note(s):
    - This step will be executed after every TransactionEventResponse, if the message did not contain a
      totalCost.
10. The Test System responds with a CostUpdatedResponse

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - totalCost <Optional>
* Step 7:
    Message (Optional) CostUpdatedRequest
    - transactionId <Generated TransactionId>

Post scenario validations:
    - N/a

Remarks
Transcription note (not printed in the document): the tool validation for the CostUpdatedRequest is printed
under "Step 7", although the CSMS sends that message in step 9; it is kept as printed. In the scenario table,
step 10 (Charging Station column) is printed in the same row as step 9 (CSMS column); the two are listed here
in numerical order.
"""
