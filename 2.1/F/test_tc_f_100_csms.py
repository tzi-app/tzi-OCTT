"""
Test case name      Trigger message - CustomTrigger
Test case Id        TC_F_100_CSMS
Use case Id(s)      F06
Requirement(s)      …
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger messages using a CustomTrigger.

Prerequisite(s)     The Test System reports support for the following:
                    component.name CustomizationCtrlr
                    variable.name CustomTriggers
                    variableAttribute.value [Custom1, Custom2, Custom3]

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Use CSMS to trigger custom trigger Custom2 for <Configured evseId>

1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with
    - status Accepted

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage CustomTrigger
    - customTrigger Custom2
    - evse.id <Configured evseId>

Post scenario validations:
    N/a
"""
