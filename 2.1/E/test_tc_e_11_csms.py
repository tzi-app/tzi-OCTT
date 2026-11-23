"""
Test case name      Start transaction options - DataSigned
Test case Id        TC_E_11_CSMS
Use case Id(s)      E01(S4)
Requirement(s)      E01.FR.04

Requirement Details:
    E01.FR.04: The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType =
               Started) to the CSMS.
        Precondition: TxStartPoint contains: DataSigned AND The Charging Station has a meter that can sign
                      measured values AND Configuration Variable: SampledDataSignReadings set to true. AND The
                      Charging Station has retrieved a signed meter value AND No transaction has started yet
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that starts a transaction when
                    the signed meter values are received.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest
    With idToken.idToken <Configured valid_idtoken_idtoken>
    idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System notifies the CSMS about the status change of the connector.
    Message: StatusNotificationRequest
    - connectorStatus is Occupied
    Message: NotifyEventRequest
    - trigger is Delta
    - actualValue is Occupied
    - component.name is Connector
    - variable.name is AvailabilityState
4. The CSMS responds accordingly.
5. The Test System sends a TransactionEventRequest
    With eventType is Started
    triggerReason is SignedDataReceived
    idToken.idToken <Configured valid_idtoken_idtoken>
    idToken.type <Configured valid_idtoken_type>
    evse.id is <Configured evseId>
    evse.connectorId is <Configured connectorId>
    meterValue is provided with the following values:
    sampledValue.value is 0.0
    sampledValue.context is Transaction.Begin
    sampledValue.signedMeterValue is <Generated SignedMeterValueType>
6. The CSMS responds with a TransactionEventResponse
7. The Test System sends a TransactionEventRequest
    With eventType is Updated
    triggerReason is ChargingStateChanged
    transactionInfo.chargingState is Charging
8. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status must be Accepted
* Step 6:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted

Post scenario validations:
    N/a
"""
