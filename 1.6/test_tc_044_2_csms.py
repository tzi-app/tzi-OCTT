"""
Test case name      Firmware Update - Download Failed
Test case Id        TC_044_2_CSMS
Feature profile     FirmwareManagement
Reference           CompliancyTestTool-TestCaseDocument, Section 3.15.2, Table 162, Page 139/176

Description         The firmware of a Charge Point is being updated, but downloading the firmware fails.
Purpose             Check whether Central System can handle messages for a firmware update in case downloading of the
                    firmware fails.

Prerequisite(s)     The Central System supports the Firmware Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1.  The Central System sends a UpdateFirmware.req
        - location: <Firmware Download URL from test data>
    2.  The Charge Point responds with a UpdateFirmware.conf

    [The Charge Point starts downloading the firmware]
    3.  The Charge Point sends a FirmwareStatusNotification.req
        - status: Downloading
    4.  The Central System responds with a FirmwareStatusNotification.conf

    [Downloading the firmware fails]
    5.  The Charge Point sends a FirmwareStatusNotification.req
        - status: DownloadFailed
    6.  The Central System responds with a FirmwareStatusNotification.conf

Tool validations
    * Step 3 (Charge Point):
        (Message: FirmwareStatusNotification.req)
        The status is Downloading.

    * Step 5 (Charge Point):
        (Message: FirmwareStatusNotification.req)
        The status is DownloadFailed.

Expected result(s) / behaviour
    n/a
"""
