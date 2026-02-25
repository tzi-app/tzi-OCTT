"""
Test case name      Firmware Update - Installation Failed
Test case Id        TC_044_3_CSMS
Feature profile     FirmwareManagement
Reference           CompliancyTestTool-TestCaseDocument, Section 3.15.3, Table 163, Page 140

Description         The firmware of a Charge Point is being updated, but the installation fails.
Purpose             Check whether Central System can handle messages for an update of the firmware of a Charge Point in
                    case the installation fails.

Prerequisite(s)     The Central System supports the Firmware Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1.  The Central System sends a UpdateFirmware.req
        - location: <Firmware Download URL from test data>
        NOTE: 'location' field is not explicitly listed in the CSMS test scenario;
              inferred from context. Test data source for firmware URL is unspecified (to be fixed later).
    2.  The Charge Point responds with a UpdateFirmware.conf

    [The Charge Point starts downloading the firmware]
    3.  The Charge Point sends a FirmwareStatusNotification.req
        - status: Downloading
    4.  The Central System responds with a FirmwareStatusNotification.conf

    [The Charge Point has finished downloading the firmware]
    5.  The Charge Point sends a FirmwareStatusNotification.req
        - status: Downloaded
    6.  The Central System responds with a FirmwareStatusNotification.conf

    [The Charge Point reports the status of all connectors]
    7.  The Charge Point sends a StatusNotification.req
        - status: Unavailable
    8.  The Central System responds with a StatusNotification.conf

    [The Charge Point starts installing the firmware]
    9.  The Charge Point sends a FirmwareStatusNotification.req
        - status: Installing
    10. The Central System responds with a FirmwareStatusNotification.conf

    11. The Charge Point reboots and sends a BootNotification.req
    12. The Central System responds with a BootNotification.conf

    [The Charge Point reports the status of all connectors]
    13. The Charge Point sends a StatusNotification.req
        - status: Available
    14. The Central System responds with a StatusNotification.conf

    15. The Charge Point sends a FirmwareStatusNotification.req
        - status: InstallationFailed
    16. The Central System responds with a FirmwareStatusNotification.conf

Tool validations
    Charge Point (Tool):
    * Step 3:
        (Message: FirmwareStatusNotification.req)
        The status is Downloading.

    * Step 5:
        (Message: FirmwareStatusNotification.req)
        The status is Downloaded.

    * Step 7:
        (Message: StatusNotification.req)
        The status is Unavailable.

    * Step 9:
        (Message: FirmwareStatusNotification.req)
        The status is Installing.

    * Step 13:
        (Message: StatusNotification.req)
        The status is Available.

    * Step 15:
        (Message: FirmwareStatusNotification.req)
        The status is InstallationFailed.

    Central System (SUT): n/a

Expected result(s) / behaviour: n/a
"""
