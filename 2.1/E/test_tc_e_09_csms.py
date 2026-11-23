"""
Test case name      Start transaction options - EVConnected
Test case Id        TC_E_09_CSMS
Use case Id(s)      E01(S2)
Requirement(s)      E01.FR.02

Requirement Details:
    E01.FR.02: The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType =
               Started) to the CSMS.
        Precondition: TxStartPoint contains: EVConnected AND The Charging Station has a connection with the EV
                      AND No transaction has started yet on this EVSE
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that starts a transaction when
                    the EV and EVSE are connected.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System notifies the CSMS about the status change of the connector.
    Message: StatusNotificationRequest
    - connectorStatus is Occupied
    Message: NotifyEventRequest
    - trigger is Delta
    - actualValue is Occupied
    - component.name is Connector
    - variable.name is AvailabilityState
2. The CSMS responds accordingly.
3. The Test System sends a TransactionEventRequest With
    - eventType is Started
    - triggerReason is CablePluggedIn
    - evse.id is <Configured evseId>
    - evse.connectorId is <Configured connectorId>
    - transactionInfo.chargingState is EVConnected
4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
