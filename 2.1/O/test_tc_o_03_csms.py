"""
Test case name      Get all Display Messages - No DisplayMessages configured
Test case Id        TC_O_03_CSMS
Use case Id(s)      O03
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can request all the installed DisplayMessages
                    configured via OCPP in a Charging Station. The Charging Station can remove messages when
                    they are out-dated, or transactions have ended. It can be very useful for a CSO to be able
                    to view to current list of messages, so the CSO knows which messages are (still)
                    configured.

Purpose             To verify if the CSMS can request to get all display messages according to the
                    DisplayMessage mechanism as described in the OCPP specification when no messages are
                    configured.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetDisplayMessagesRequest
2. The Test System responds with a GetDisplayMessagesResponse with status Unknown

Tool validations
* Step 1:
    Message GetDisplayMessagesRequest
    - requestId <Generated request id>

Post scenario validations:
    - N/a
"""
