"""
Test case name      WebSocket Subprotocol negotiation
Test case Id        TC_088_CSMS
OCPP version        1.6J
System under test   Central System (SUT)
Document ref        CompliancyTestTool-TestCaseDocument, Table 198, p.172-173

Description         OCPP-J imposes extra constraints on the WebSocket subprotocol

Purpose             To verify whether the Central System is able to select OCPP 1.6 as a supported
                    version, when also a different unsupported version is supported by the Charge
                    Point and relays this selection via the Sec-Websocket-Protocol header.

Prerequisite(s)     N/a

Before (Preparations):
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): N/a

Test Scenario
1. The Charge Point disconnects the WebSocket connection and reconnects by sending a HTTP
   upgrade request with the header;
   Sec-WebSocket-Protocol: ocpp0.1
2. The Central System rejects the connection attempt and does NOT upgrade the connection to
   a WebSocket connection.
3. The Charge Point disconnects the WebSocket connection and reconnects by sending a HTTP
   upgrade request with the header;
   Sec-WebSocket-Protocol: ocpp0.1,ocpp1.6
4. The Central System accepts the connection attempt and upgrades the connection to a
   WebSocket connection.

Tool validations:
    * Step 4:
        - The authorization header of the HTTP upgrade response must contain the header
          Sec-Websocket-Protocol, and it must comply to the following:
        - The header is formatted as follows; Sec-WebSocket-Protocol: ocpp1.6

Post scenario validations:
    N/a

NOTE: The official doc only validates Step 4. Step 2 rejection of unsupported-only subprotocol
      is implied by the scenario but has no explicit tool validation entry in the document.
"""
