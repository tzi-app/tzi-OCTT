"""
Test case name      CustomData - Receive custom data
Test case Id        TC_P_03_CSMS
Use case Id(s)      N/a
Requirement(s)      N/a
System under test   CSMS

Description         Checks if the CSMS is able to receive custom data.

Purpose             To verify whether the CSMS is able to handle receiving custom data.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a StatusNotificationRequest with
    - customData <customData>
2. The CSMS responds with a StatusNotificationResponse
3. The Test System sends a TransactionEventRequest with
    - customData customData
    - transactionInfo.customData <customData>
4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
