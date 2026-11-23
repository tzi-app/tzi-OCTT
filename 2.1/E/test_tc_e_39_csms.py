"""
Test case name      Stop transaction options - Deauthorized - timeout
Test case Id        TC_E_39_CSMS
Use case Id(s)      E03, E06
Requirement(s)      E03.FR.04, E03.FR.05, E06.FR.04

Requirement Details:
    E03.FR.04: (not found in OCPP 2.1 Part 2)
    E03.FR.05: The Charging Station SHOULD end the transaction and send a TransactionEventRequest (eventType =
               Ended, stoppedReason = Timeout, triggerReason = EVConnectionTimeout) to the CSMS.
        Precondition: When the EV Driver does not plug-in the charging cable before the timeout set by the
                      Configuration Variable: EVConnectionTimeOut AND TxStopPoint does not contain
                      ParkingBayOccupancy
        Note: This requirement is an additional safety measure to make sure the transaction is ended when the
              EVConnectionTimeOut is triggered. However it is up to the CSMS to make sure that sensible
              TxStartPoint / TxStopPoint combinations are configured. E.g. if Authorized is used as
              TxStartPoint, it should also be used as TxStopPoint.
    E06.FR.04: See use case E05 - Start Transaction - Id not Accepted,
        Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a
                      TransactionEventResponse
System under test   CSMS

Description         OCPP 2.x.x allows an EV driver to either first connect the EV and EVSE OR present a form
                    of identification. Both sequences will result in being able to charge.

Purpose             To verify if the CSMS is able to handle a Charging Station that deauthorizes the
                    transaction after the EVConnectionTimeout has expired.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized

Test Scenario
1. The Test System sends a TransactionEventRequest
    - With triggerReason is EVConnectTimeout
    - transactionInfo.stoppedReason is Timeout
    - eventType is Ended
    Note(s):
    - This step will be executed after the _<Configured EV connection timeout> expires._
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
