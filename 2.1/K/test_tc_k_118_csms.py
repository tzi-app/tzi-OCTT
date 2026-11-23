"""
Test case name      Priority Charging - Requesting priority charging remotely
Test case Id        TC_K_118_CSMS
Use case Id(s)      K21
Requirement(s)      K21.FR.09, K21.FR.10

Requirement Details:
    K21.FR.09: CSMS SHALL respond with NotifyPriorityChargingResponse.
        Precondition: K21.FR.05 OR K21.FR.08
    K21.FR.10: CSMS SHALL support sending a UsePriorityChargingRequest
        Note: A Charging Station reports support for this in SmartChargingCtrlr.SupportedAdditionalPurposes.
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify the CSMS supports priority charging initiated from CSMS.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to use priority charging for the transaction

1. The CSMS sends a UsePriorityChargingRequest
2. The Test System responds with a UsePriorityChargingResponse with
    - status Accepted
3. The Test System sends a NotifyPriorityChargingRequest with
    - transactionId <transactionId>
    - activated true
4. The CSMS responds with a NotifyPriorityChargingResponse

Tool validations
* Step 1:
    Message: UsePriorityChargingRequest
    - transactionId must be <transactionId>
    - activate true

Post scenario validations:
    N/a
"""
