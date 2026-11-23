"""
Test case name      Get a Specific Display Message - Id
Test case Id        TC_O_07_CSMS
Use case Id(s)      O04
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can request specific installed DisplayMessages
                    configured via OCPP in a Charging Station. The Charging Station can remove messages when
                    they are out-dated, or transactions have ended. It can be very useful for a CSO to be able
                    to view to current list of messages, so the CSO knows which messages are (still)
                    configured.

Purpose             To verify if the CSMS is able to request a specific id message from the charging station
                    according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        A display message is configured.

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetDisplayMessagesRequest
2. The Test System responds with a GetDisplayMessagesResponse with status Accepted
3. The Test System sends a NotifyDisplayMessagesRequest
4. The CSMS responds with a NotifyDisplayMessagesResponse.

Tool validations
* Step 1:
    Message GetDisplayMessagesRequest
    - id <Configured_Id>
    - priority <Omitted>
    - state <Omitted>
    - requestId <Generated Id>

Post scenario validations:
    - N/a
"""
