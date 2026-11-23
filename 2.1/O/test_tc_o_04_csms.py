"""
Test case name      Clear Display Message - Success
Test case Id        TC_O_04_CSMS
Use case Id(s)      O05
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can remove a specific message, configured via OCPP in a
                    Charging Station.

Purpose             To verify if the CSMS is able to request the Charging Station to clear a message according
                    to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        A display message is configured.

Reusable State      N/a

Test Scenario
Note: As a help method, a GetDisplayMessagesRequest is requested first for CSMS’s that implemented their
      ClearDisplayMessage as a combined feature.

1. The CSMS sends a ClearDisplayMessageRequest
2. The Test System responds with a ClearDisplayMessageResponse with status Accepted

Tool validations
* Step 1:
    Message ClearDisplayMessageRequest
    - id <Generated Id from set display message>

Post scenario validations:
    - N/a
"""
