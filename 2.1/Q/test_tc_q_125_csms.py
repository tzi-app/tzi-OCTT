"""
Test case name      Idle operationMode - Idle, minimizing energy consumption - Idle with EvseSleep
Test case Id        TC_Q_125_CSMS
Use case Id(s)      Q10
Requirement(s)      Q10.FR.01

Requirement Details:
    Q10.FR.01: The fields limit, dischargeLimit, setpoint and setpointReactive SHALL be absent
        Precondition: When a chargingSchedulePeriod has operationMode = Idle
        Note: This also applies to the L2/L3 variants of these fields.
System under test   CSMS

Description         To request the EV to not perform any charging or discharging. Preconditioning of the
                    vehicle is allowed.

Purpose             To verify that the CSMS is able to send a Charging Profile which Minimizes the energy
                    consumption.

Prerequisite(s)     - CSMS supports ISO15118-20
                    - CS supports V2XChargingCtrlr.V2XSupportedOperationModes containing Idle
                    - CS supports SmartChargingCtrlr.SupportsFeature[EvseSleep] = true

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State ISO15118-20 transaction started in V2X AC_BPT energy transfer mode

Without EVSE sleeping

Manual Action: trigger CSMS to set a TxProfile Charging Profile with chargingSchedulePeriod with operationMode
               Idle and evseSleep false

2. The CSMS the sends a SetChargingProfileRequest
3. The Test System responds with a SetChargingProfileResponse with
    - status must be Accepted
4. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason OperationModeChanged
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.operationMode Idle
    - evseSleep false
5. The CSMS responds with a TransactionEventResponse

With EVSE sleeping

Manual Action: trigger CSMS to set a TxProfile Charging Profile with chargingSchedulePeriod with operationMode
               Idle and evseSleep true

6. The CSMS the sends a SetChargingProfileRequest
7. The Test System responds with a SetChargingProfileResponse
8. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason MeterValuePeriodic
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.operationMode Idle
    - evseSleep true
9. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose must be TxProfile
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.operationMode must be Idle
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.evseSleep must be false
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.dischargingLimit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpoint must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpointReactive must be <omitted>
* Step 6:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose must be TxProfile
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.operationMode must be Idle
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.evseSleep must be true
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.dischargingLimit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpoint must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpointReactive must be <omitted>

Post scenario validations:
    N/a

Remarks
The section heading for this test is printed as "TC_Q_125_CSMS: Idle operationMode - Idle, minimizing energy
consumption - Idle with EvseSleep", while the Test case Id row of the table is printed as "TC_Q_150_CS". The
test_case_id field holds the cell text as printed.
"""
