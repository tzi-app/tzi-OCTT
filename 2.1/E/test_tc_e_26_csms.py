"""
Test case name      Disconnect cable on EV-side - Suspend transaction
Test case Id        TC_E_26_CSMS
Use case Id(s)      E10
Requirement(s)      E10.FR.01

Requirement Details:
    E10.FR.01: The Connector SHALL remain locked at the Charging Station until the EV Driver presents the
               IdToken.
        Precondition: If StopTxOnEVSideDisconnect = false AND Cable not permanently attached
System under test   CSMS

Description         The Charging Station can behave in several different ways when the cable is disconnected
                    at the EV side, based on its configuration. This test case tests one of the possible
                    configuration settings.

Purpose             To verify if the CSMS can handle a Charging Station that suspends the transaction when the
                    EV and EVSE are disconnected at the EV side AND is able restart the energy transfer after
                    reconnecting the EV and EVSE.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferSuspended

Test Scenario
1. The Test System sends a TransactionEventRequest
    With triggerReason is EVCommunicationLost
    transactionInfo.chargingState is Idle
    eventType is Updated
2. The CSMS responds with a TransactionEventResponse
3. The Test System notifies the CSMS about the current state of the connector.
    Message: StatusNotificationRequest
    - connectorStatus Available
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - component.evse.id <Configured evseId>
    - component.evse.connectorid <Configured connectorId>
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.
5. The Test System sends a TransactionEventRequest
    With triggerReason is CablePluggedIn
    transactionInfo.chargingState is EVConnected
    eventType is Updated
6. The CSMS responds with a TransactionEventResponse
7. The Test System sends a TransactionEventRequest
    With triggerReason is ChargingStateChanged
    transactionInfo.chargingState is Charging
    eventType is Updated
8. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
