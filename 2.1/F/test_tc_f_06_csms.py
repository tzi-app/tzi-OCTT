"""
Test case name      Remote unlock Connector - Without ongoing transaction - Accepted
Test case Id        TC_F_06_CSMS
Use case Id(s)      F05
Requirement(s)      n/a
System under test   CSMS

Description         This test case describes how the CSMS can be requested to sent an UnlockConnectorRequest
                    to the charging station. It sometimes happens that a connector of a Charging Station
                    socket does not unlock correctly. This happens most of the time when there is tension on
                    the charging cable. This means the driver cannot unplug his charging cable from the
                    Charging Station. To help a driver, the CSO can send a UnlockConnectorRequest to the
                    Charging Station. The Charging Station will then try to unlock the connector again.

Purpose             To verify if the CSMS is able to perform the remote unlock connector mechanism as
                    described at the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a UnlockConnectorRequest
2. The Test System responds with a UnlockConnectorResponse with status Unlocked

Tool validations
* Step 1:
    Message UnlockConnectorRequest
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>

Post scenario validations:
    - N/a
"""
