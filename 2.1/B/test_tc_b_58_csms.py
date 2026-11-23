"""
Test case name      WebSocket Subprotocol validation
Test case Id        TC_B_58_CSMS
Use case Id(s)      Part 4 - JSON over WebSockets implementation guide
Requirement(s)      Section 3.1.2. OCPP version
System under test   CSMS

Description         OCPP-J imposes extra constraints on the WebSocket subprotocol, detailed in the following
                    section 3.1.2.

Purpose             To verify whether the CSMS is able to select a supported OCPP version, when also a
                    different unsupported version is supported by the Charging Station and relays this
                    selection via the Sec-Websocket-Protocol header.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System disconnects the WebSocket connection and reconnects by sending a HTTP upgrade request with
   the header; Sec-WebSocket-Protocol: ocpp0.1
2. The CSMS rejects the connection attempt and does NOT upgrade the connection to a WebSocket connection.
3. The Test System disconnects the WebSocket connection and reconnects by sending a HTTP upgrade request with
   the header; Sec-WebSocket-Protocol: ocpp0.1,ocpp<Selected OCPP version>
4. The CSMS accepts the connection attempt and upgrades the connection to a WebSocket connection.

Tool validations
* Step 4:
    The authorization header of the HTTP upgrade response must contain the header Sec-Websocket-Protocol, and
    it must comply to the following:
    - The header is formatted as follows; Sec-WebSocket-Protocol: ocpp<Selected OCPP version>

Post scenario validations:
    N/a

Remarks
Section heading printed above the table: TC_B_58_CSMS: WebSocket Subprotocol negotiation
"""
