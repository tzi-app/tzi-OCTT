"""
Test case name      Retrieve Log Information - DataCollectorLog - Success
Test case Id        TC_N_100_CSMS
Use case Id(s)      N01
Requirement(s)      …
System under test   Charging Station

Description         This test case covers the functionality of getting log information from a Charging
                    Station. The CSMS can request a Charging Station to upload a file with log information to
                    a given location (URL). The format of this log file is not prescribed. The Charging
                    Station successfully uploads a log file and gives information about the status of the
                    upload by sending status notifications to the CSMS.

Purpose             To verify if the CSMS is able to successfully retrieve a log of logType DataCollectorLog
                    as described at the OCPP specification.

Prerequisite(s)     - CSMS supports DataCollectorLog.
                    - A diagnostics logging server has been setup supporting one of the file transfer
                      protocols supported by the Charging Station (This is configured at the configuration
                      variable FileTransferProtocols).
                    - Charging station supports DataCollector (Component DataCollector available).

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to retrieve the DataCollectorLog

1. The CSMS sends a GetLogRequest
2. The Test System responds with a GetLogResponse
3. The Test System sends a LogStatusNotificationRequest with
    - status Uploading
    - requestId <GetLogRequest.requestId of step 1>
4. The CSMS responds with a LogStatusNotificationResponse .
5. The Test System sends a LogStatusNotificationRequest with
    - status Uploaded
    - requestId <GetLogRequest.requestId of step 1>
6. The CSMS responds with a LogStatusNotificationResponse .

Tool validations
* Step 1:
    Message GetLogRequest
    - logType DataCollectorLog

Post scenario validations:
    N/a
"""
