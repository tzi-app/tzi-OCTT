"""
Test case name      Charging with load leveling based on High Level Communication - EV charging profile
                    exceeds limits
Test case Id        TC_K_55_CSMS
Use case Id(s)      K15,K16,K17
Requirement(s)      K15.FR.12, K15.FR.13, K16.FR.07, K16.FR.08, K17.FR.12, K17.FR.13

Requirement Details:
    K15.FR.12: CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging Station.
        Precondition: K15.FR.10 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
    K15.FR.13: CSMS starts new renegotiation as per use case K16.
        Precondition: K15.FR.12
    K16.FR.07: CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging Station.
        Precondition: K16.FR.05 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
    K16.FR.08: CSMS starts new renegotiation as per use case K16.
        Precondition: K16.FR.07
    K17.FR.12 (2.1): CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging
                     Station.
        Precondition: K17.FR.10 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
        Note: Not applicable in dynamic control mode.
    K17.FR.13: CSMS starts new renegotiation as per use case K16.
        Precondition: K17.FR.12
System under test   CSMS

Description         ISO15118-1 E1 AC Charging with load leveling based on High Level Communication, and E4 DC
                    charging with load leveling based on High Level Communication.

Purpose             To verify if the CSMS is able to renegotiate when it receives the EV charging schedule
                    which exceeds the profile limits.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized
                    State is EVConnectedPreSession

Test Scenario
1. The Test System sends a NotifyEVChargingNeedsRequest.
    - evseId <Configured evseId>
    - maxScheduleTuples & chargingNeeds <Configured values from mock EV>
2. The CSMS responds with a NotifyEVChargingNeedsResponse.
3. The CSMS sends a SetChargingProfileRequest
4. The Test System responds with a SetChargingProfileResponse
    - status Accepted
5. The Test System sends a NotifyEVChargingScheduleRequest.
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule that exceeds the limits of the chargingSchedule provided at step 3.>
6. The CSMS responds with a NotifyEVChargingScheduleResponse.
7. The Test System sends a TransactionEventRequest.
    - triggerReason ChargingStateChanged
    - transactionInfo.chargingState Charging
8. The CSMS responds with a TransactionEventResponse.
9. The CSMS sends a SetChargingProfileRequest
10. The Test System responds with a SetChargingProfileResponse
    - status Accepted
11. The Test System sends a NotifyEVChargingScheduleRequest.
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 9>
12. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 2:
    Message NotifyEVChargingNeedsResponse
    - status Accepted
* Step 3:
    Message SetChargingProfileRequest
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 6:
    Message NotifyEVChargingScheduleResponse
    - status Rejected
* Step 9:
    Message SetChargingProfileRequest
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 12:
    Message NotifyEVChargingScheduleResponse
    - status Accepted

Post scenario validations:
    N/a
"""
