"""
Test case name      ISO 15118-20 Dynamic Control Mode - Adjusting charging schedule
Test case Id        TC_K_117_CSMS
Use case Id(s)      K20
Requirement(s)      K20.FR.03

Requirement Details:
    K20.FR.03: CSMS calculates a new charging profile and sends a SetChargingProfileRequest to Charging
               Station
        Precondition: K20.FR.01 AND EV and Charging Station use ISO 15118-20 "Dynamic Control Mode"
System under test   CSMS

Description         The EV signals the Charging Station that it wants to renegotiate and it provides new
                    charging needs, which the Charging Station sends to the CSMS. Based on this and other
                    parameters, the CSMS calculates a new charging schedule and sends it via
                    SetChargingProfileRequest to Charging Station, which communicates it to the EV.

Purpose             To verify if the CSMS is able to provide a new charging profile when EV provides a changed
                    departure time or target energy amount.

Prerequisite(s)     CSMS supports ISO15118-20

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized
                    State is EVConnectedPreSession
                    State is ISO15118SmartCharging (iso15118-20)

Test Scenario
1. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - maxScheduleTuples 3
    - chargingNeeds.requestedEnergyTransfer AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.departureTime <Current DateTime + 2 hours>
    - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 1000
    - chargingNeeds.v2xChargingParameters.maxChargePower 5000
    - chargingNeeds.v2xChargingParameters.maxDischargePower 5000
2. The CSMS responds with a NotifyEVChargingNeedsResponse.
3. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
5. The Test System sends a NotifyEVChargingScheduleRequest with
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 3>
6. The CSMS responds with a NotifyEVChargingScheduleResponse.
7. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - maxScheduleTuples 3
    - chargingNeeds.requestedEnergyTransfer AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.departureTime <Current DateTime + 3 hours>
    - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 1000
    - chargingNeeds.v2xChargingParameters.maxChargePower 5000
    - chargingNeeds.v2xChargingParameters.maxDischargePower 5000
8. The CSMS responds with a NotifyEVChargingNeedsResponse.
9. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
10. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
11. The Test System sends a NotifyEVChargingScheduleRequest with
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 5>
12. The CSMS responds with a NotifyEVChargingScheduleResponse.
13. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - maxScheduleTuples 3
    - chargingNeeds.requestedEnergyTransfer AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.departureTime <Current DateTime + 3 hours>
    - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 3000
    - chargingNeeds.v2xChargingParameters.maxChargePower 5000
    - chargingNeeds.v2xChargingParameters.maxDischargePower 5000
14. The CSMS responds with a NotifyEVChargingNeedsResponse.
15. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
16. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
17. The Test System sends a NotifyEVChargingScheduleRequest with
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 5>
18. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 2:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 3:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfilePurpose must be TxProfile
    - transactionId must be <Provided transactionId from before>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpoint must be <Not omitted>
* Step 6:
    Message: NotifyEVChargingScheduleResponse
    - status must be Accepted
* Step 8:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 9:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfilePurpose must be TxProfile
    - transactionId must be <Provided transactionId from before>
* Step 12:
    Message: NotifyEVChargingScheduleResponse
    - status must be Accepted
* Step 14:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 15:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfilePurpose must be TxProfile
    - transactionId must be <Provided transactionId from before>
* Step 18:
    Message: NotifyEVChargingScheduleResponse
    - status must be Accepted

Post scenario validations:
    N/a
"""
