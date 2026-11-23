"""
Test case name      Set Variable Monitoring - Get Periodic Event Streams - Goodflow
Test case Id        TC_N_107_CSMS
Use case Id(s)      N12
Requirement(s)      N12.FR.01

Requirement Details:
    N12.FR.01: Charging Station SHALL respond with a GetPeriodicEventStreamResponse with a list of zero or
               more ConstantStreamDataType of all open event streams
        Precondition: Upon receiving a GetPeriodicEventStreamRequest
System under test   CSMS

Description         To get a list of existing event streams

Purpose             To verify if the CSMS can request retrieving a list of periodic event streams.

Prerequisite(s)     - The CSMS supports periodic event streams.

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to retrieve a list of existing event streams from the Charging Station

1. CSMS sends a GetPeriodicEventStreamRequest
2. Test System responds with a GetPeriodicEventStreamResponse with
    - constantStreamData[0].id 2
    - constantStreamData[0].variableMonitoringId 3
    - constantStreamData[0].params.interval 10
    - constantStreamData[0].params.values 30
    - constantStreamData[1].id 3
    - constantStreamData[1].variableMonitoringId 4
    - constantStreamData[1].params.interval 10
    - constantStreamData[1].params.values 30

Tool validations
N/a

Post scenario validations:
    N/a
"""
