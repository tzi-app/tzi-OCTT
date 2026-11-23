"""
Test case name      Retrieve Log Information - Second Request
Test case Id        TC_N_36_CSMS
Use case Id(s)      N01
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers the functionality of getting log information from a Charging
                    Station. The CSMS can request a Charging Station to upload a file with log information to
                    a given location (URL). The format of this log file is not prescribed. The Charging
                    Station successfully uploads a log file and gives information about the status of the
                    upload by sending status notifications to the CSMS.

Purpose             To verify if the CSMS is able to request a second request while the charging station is
                    uploading a log as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        Charging Station has log information available.

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetLogRequest
2. The Test System responds with a GetLogResponse with status Accepted
3. The Test System sends a LogStatusNotificationRequest with
    - status Uploading
    - requestId Same Id as the GetLogRequest from Step 1
4. The CSMS responds with a LogStatusNotificationResponse.
5. The CSMS sends a GetLogRequest
6. The Test System responds with a GetLogResponse with status AcceptedCanceled
7. The Test System sends a LogStatusNotificationRequest with
    - status AcceptedCanceled
    - requestId Same Id as the GetLogRequest from Step 1
8. The CSMS responds with a LogStatusNotificationResponse.
9. The Test System sends a LogStatusNotificationRequest with
    - status Uploading
    - requestId Same Id as the GetLogRequest from Step 5
10. The CSMS responds with a LogStatusNotificationResponse.
11. The Test System sends a LogStatusNotificationRequest with
    - status Uploaded
    - requestId Same Id as the GetLogRequest from Step 5
12. The CSMS responds with a LogStatusNotificationResponse.

Tool validations
N/a

Post scenario validations:
    - N/a
"""
