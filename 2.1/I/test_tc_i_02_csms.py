"""
Test case name      Show EV Driver Final Total Cost After Charging
Test case Id        TC_I_02_CSMS
Use case Id(s)      I03
Requirement(s)      I03.FR.02

Requirement Details:
    I03.FR.02: The CSMS SHALL send the total cost of the transaction in the totalCost field of the
               TransactionEventResponse message.
        Precondition: I03.FR.01 AND When Total Cost is known to the CSMS.
System under test   CSMS

Description         While a transaction is ongoing, the driver wants to know how much the running total cost
                    is, updated at a relevant interval.

Purpose             To verify if the CSMS is able to correctly send the total cost as described in the OCPP
                    specification.

Prerequisite(s)     - N/a

Configuration State N/a

Memory State        - CSMS is configured with a tariff which is based on energy consumed.

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State EVConnectedPreSession
    - The TransactionEventRequest contains the MeterValue field.
    - sampledValue[0].value 1000
    - sampledValue[0].context Transaction.Begin
2. Execute Reusable State Authorized
3. Execute Reusable State EnergyTransferStarted
4. Execute Reusable State StopAuthorized
5. Execute Reusable State EVConnectedPostSession
6. The Test System notifies the CSMS about the current state of the configured connector.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
7. The CSMS responds accordingly.
8. The Test System sends a TransactionEventRequest with
    - triggerReason EVCommunicationLost
    - eventType Ended
    - transactionInfo.chargingState Idle
    - transactionInfo.stoppedReason EVDisconnected
    - meterValue[0].sampledValue[0].value 6000
    - meterValue[0].sampledValue[0].context Transaction.End
9. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 9:
    Message TransactionEventResponse
    - totalCost <Not omitted>

Post scenario validations:
    - N/a
"""
