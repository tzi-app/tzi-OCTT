"""
Test case name      EMS Control - Reset / release external charging limit - With ongoing transaction
Test case Id        TC_K_51_CSMS
Use case Id(s)      K13
Requirement(s)      N/a
System under test   CSMS

Description         A charging schedule or charging limit can be removed by an external system on the Charging
                    Station. An external control system sends a signal to release a previously imposed
                    charging limit to a Charging Station. The Charging Station notifies the CSMS about this.

Purpose             To verify if the CSMS is able to receive the notify from a charging station and respond
                    correctly as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System sends a ClearedChargingLimitRequest with
    - chargingLimitSource EMS
2. The CSMS responds with a ClearedChargingLimitResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason ChargingRateChanged
4. The CSMS responds with a TransactionEventResponse

Tool validations
- N/a

Post scenario validations:
    - N/a
"""
