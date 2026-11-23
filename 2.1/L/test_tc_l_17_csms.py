"""
Test case name      Publish Firmware - Published
Test case Id        TC_L_17_CSMS
Use case Id(s)      L03
Requirement(s)      N/a
System under test   CSMS

Description         The Local Controller downloads and publishes a firmware update at the specified URL. This
                    allows the CSMS to send UpdateFirmwareRequests with the URI pointing to the Local
                    Controller, to any Charging Station connected to the Local Controller. This allows the
                    site to save bandwidth and data on the WAN interface.

Purpose             To verify if the CSMS is able to publish a firmware on the local controller as described
                    at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a PublishFirmwareRequest
2. The Test System responds with a PublishFirmwareResponse with
    - status Accepted
3. The Test System sends a PublishFirmwareStatusNotificationRequest with
    - status Downloading
4. The CSMS responds with a PublishFirmwareStatusNotificationResponse
5. The Test System sends a PublishFirmwareStatusNotificationRequest with
    - status Downloaded
6. The CSMS responds with a PublishFirmwareStatusNotificationResponse
7. The Test System sends a PublishFirmwareStatusNotificationRequest with
    - status ChecksumVerified
8. The CSMS responds with a PublishFirmwareStatusNotificationResponse
9. The Test System sends a PublishFirmwareStatusNotificationRequest with
    - status Published AND
    - location <Configured firmware_location>
10. The CSMS responds with a PublishFirmwareStatusNotificationResponse

Tool validations
* Step 1:
    Message PublishFirmwareRequest
    - location <Configured firmware_location>

Post scenario validations:
    - N/a
"""
