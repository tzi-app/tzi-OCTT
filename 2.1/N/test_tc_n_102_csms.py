"""
Test case name      Retrieve Log Information - Authentication - HTTP
Test case Id        TC_N_102_CSMS
Use case Id(s)      N01
Requirement(s)      N01.FR.26, N01.FR.27, N01.FR.28

Requirement Details:
    N01.FR.26 (2.1): The CSMS SHALL NOT send a log upload URL that points to a server responding with a
                     redirection.
        Precondition: N01.FR.18
    N01.FR.27 (2.1): The CSMS SHALL NOT send a log upload URL containing a fragment component.
        Precondition: N01.FR.18
        Note: The fragment component would not be part of the HTTP request, so it serves no purpose.
    N01.FR.28 (2.1): The CSMS SHALL NOT include a query component that ends with a slash character ("/").
        Precondition: N01.FR.18 AND the CSMS includes a query component in the log upload URL
        Note: This is to simplify processing of the URL string in the Charging Station.
System under test   CSMS

Description         This test case covers the functionality of getting log information from a Charging
                    Station. The CSMS can request a Charging Station to upload a file with log information to
                    a given location (URL). The format of this log file is not prescribed. The Charging
                    Station successfully uploads a log file and gives information about the status of the
                    upload by sending status notifications to the CSMS.

Purpose             To verify if the CSMS is able to successfully request and process a log of logType
                    DiagnosticsLog as described at the OCPP specification.

Prerequisite(s)     - CSMS supports HTTP file transfer protocol.
                    - A diagnostics logging server has been set up for HTTP and accepts specific userinfo
                      credentials .

Configuration State CSMS configured to prevent unauthorised uploading to HTTP log location.

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual action: Trigger CSMS to GetLogRequest with logType DiagnosticsLog and remoteLocation with userinfo for
               HTTP Basic Authentication

1. CSMS sends a GetLogRequest
2. Test System responds with a GetLogResponse with
    - status Accepted
3. The Test System uploads log file to <GetLogRequest.log.remoteLocation of step 1> using HTTP POST
4. The CSMS responds using HTTP
5. The Test System uploads file to <GetLogRequest.log.remoteLocation of step 1> using HTTP POST
6. The CSMS responds using HTTP
7. Test System sends a LogStatusNotificationRequest with
    - status Uploading
    - requestId <GetLogRequest.requestId of step 1>
8. CSMS responds with a LogStatusNotificationResponse
9. Test System sends a LogStatusNotificationRequest with
    - status Uploaded
    - requestId <GetLogRequest.requestId of step 1>
10. CSMS responds with a LogStatusNotificationResponse

Tool validations
* Step 1:
    Message GetLogRequest
    - logType must be DiagnosticsLog
    - log.remoteLocation must
       - contain a valid URL
       - specify scheme HTTP
       - contain userinfo for HTTP Basic Authentication
       - not contain a URL fragment component
       - not contain a URL query components that ends in a slash character ("/")
* Step 4:
    - HTTP status code must be 401 Unauthorized
* Step 6:
    - HTTP status code must be in 2xx-range

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.17. Page 1304-1306 - (2026-02) - TC_N_102_CSMS/TC_N_103_CSMS - added without userinfo
        The first attempt needs to be without to check it is not accepted.

        | Test case Id | TC_N_102_CSMS / TC_N_103_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | 3. The Test System uploads log file to / <GetLogRequest.log.remoteLocation of step 1 without
          userinfo> / using HTTP POST | 4. The CSMS responds using HTTP |
        | … | |
"""
