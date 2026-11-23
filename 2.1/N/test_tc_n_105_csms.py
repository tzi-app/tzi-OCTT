"""
Test case name      Set Variable Monitoring - Set Frequent Periodic Variable Monitoring - Periodic
Test case Id        TC_N_105_CSMS
Use case Id(s)      N11, N14, N15
Requirement(s)      N11.FR.06, N11.FR.08, N14.FR.01, N15.FR.02

Requirement Details:
    N11.FR.06: CSMS SHALL respond with a OpenPeriodicEventStreamResponse with status = Accepted.
        Precondition: When CSMS accepts the periodic event stream
    N11.FR.08: CSMS SHALL associate the following data, that is normally present as required fields in a
               NotifyEventRequest, with the periodic event stream. (This data is available from the monitor):
               • variableMonitoringId,
               • trigger (= Periodic),
               • eventNotificationType,
               • severity,
               • component,
               • variable.
    N14.FR.01: CSMS SHALL send a AdjustPeriodicEventStreamRequest message with the id of the event stream and
               a params object with new interval and/or values fields
        Precondition: When CSMS wants to change the rate of sending data for a periodic event stream
    N15.FR.02: CSMS SHALL NOT confirm the message upon receipt with "CALLRESULT" or "CALLERROR".
        Precondition: When receiving a message of RPC message type "SEND"
System under test   CSMS

Description         To give the CSMS the ability to request efficient frequent periodic monitoring of
                    variables.

Purpose             To verify if the CSMS can accept and receive periodic event streams.

Prerequisite(s)     - The CSMS supports periodic event streams.

Configuration State CSMS must be configured to accept opening the periodic event stream.

Memory State        N/a

Reusable State      N/a

Test Scenario
1. Test System sends a OpenPeriodicEventStreamRequest with
    - constantStreamData.id 2
    - constantStreamData.variableMonitoringId 3
    - constantStreamData.params.interval 10
    - constantStreamData.params.values 30
2. CSMS responds with a OpenPeriodicEventStreamResponse

Manual Action: Request the CSMS to reconfigure the periodic event stream to an interval of 15s and values 45

3. CSMS sends a AdjustPeriodicEventStreamRequest
4. Test System responds with a AdjustPeriodicEventStreamResponse with
    - status Accepted
5. Charging Station sends a NotifyPeriodicEventStream using RFC framework SEND
6. Test System sends a ClosePeriodicEventStreamRequest with
    - constantStreamData.id 2
7. CSMS responds with a OpenPeriodicEventStreamResponse

Note: The Test System waits 10 seconds, before ending the testcase.

Tool validations
* Step 2:
    Message OpenPeriodicEventStreamResponse
    - status must be Accepted
* Step 3:
    Message AdjustPeriodicEventStreamRequest
    - id must be 2
    - params.interval must be 15
    - params.values must be 45

Post scenario validations:
    - CSMS does not respond with any message when receiving message NotifyPeriodicEventStream of step 5.

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.19. Page 1309 - (2026-02) - TC_N_105_CSMS - Install usable monitor and send a
        NotifyPeriodicEventStream
        | Test case name | Set Variable Monitoring - Set Frequent Periodic Variable Monitoring - Periodic |
        | Test case Id | TC_N_105_CSMS |
        | … | |

        | Before (Preparations) |
        | Configuration State: / [removed: CSMS must be configured to accept opening the periodic event
          stream.] / N/a |
        | Memory State: / N/a |
        | Reusable State: / N/a |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | Manual Action : Request CSMS to install a monitor on: / component.name EVSE / EVSE.id <Configured
          evseId> / variable.name Power / type Periodic / severity 8 / value 5 / periodicEventStream.interval
          5 / periodicEventStream.values 10 | |
        | 2. Test System responds with: / Message: SetVariableMonitoringResponse with /
          setMonitoringResult[0].status = Accepted | 1. CSMS sends a SetVariableMonitoringRequest |

        | Main (Test scenario) | |
        | [removed: 1.] 3. Test System sends a OpenPeriodicEventStreamRequest with / constantStreamData.id 2 /
          constantStreamData.variableMonitoringId [removed: 3] <monitor id from step 1> /
          constantStreamData.params.interval [removed: 10] 5 / constantStreamData.params.values [removed: 30]
          10 | [removed: 2.] 4. CSMS responds with a OpenPeriodicEventStreamResponse |
        | Note : The Test System waits 5 seconds. | |
        | 5. Test System sends a NotifyPeriodicEventStream using RFC framework SEND | |
        | Manual Action: Request the CSMS to reconfigure the periodic event stream to an interval of 15s and
          values 45 | |
        | [removed: 4.] 7. Test System responds with a AdjustPeriodicEventStreamResponse with / status
          Accepted | [removed: 3.] 6. CSMS sends a AdjustPeriodicEventStreamRequest |
        | Note : The Test System waits 10 seconds. | |
        | [removed: 5.] 8. Test System sends a NotifyPeriodicEventStream using RFC framework SEND | |
        | [removed: 6.] 9. Test System sends a ClosePeriodicEventStreamRequest with / constantStreamData.id 2
          | [removed: 7.] 10. CSMS responds with a ClosePeriodicEventStreamResponse |
        | Note: [removed: The Test System waits 10 seconds, before ending the testcase.] | |

        | Tool validations |
        | \\* Step 1: / Message SetVariableMonitoringRequest with: / - setMonitoringData[0].type = Periodic, /
          - setMonitoringData[0].severity = 8, / - setMonitoringData[0].component.name = "EVSE" / -
          setMonitoringData[0].component.evse.id = <Configured evseId> / - setMonitoringData[0].variable.name
          = Power / - setMonitoringData[0].value = 5 / - setMonitoringData[0].periodicEventStream.interval 5 /
          - setMonitoringData[0].periodicEventStream.values 10 / \\* [removed: Step 2:] Step 4: / Message
          OpenPeriodicEventStreamResponse / - status must be Accepted / \\* [removed: Step 3:] Step 6: /
          Message AdjustPeriodicEventStreamRequest / id must be 2 / params.interval must be [removed: 15] 10 /
          params.values must be [removed: 45] 20 |
"""
