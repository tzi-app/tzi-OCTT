"""
Test case name      Secure Firmware Update - Unable to download/install firmware with ongoing transaction -
                    AllowNewSessionsPendingFirmwareUpdate is false
Test case Id        TC_L_13_CSMS
Use case Id(s)      L01
Requirement(s)      L01.FR.01, L01.FR.11

Requirement Details:
    L01.FR.01: The Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with
               this new status. What reason to use is described in the description of FirmwareStatusEnumType.
        Precondition: Whenever the Charging Station enters a new state in the firmware update process.
    L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate (see Keys used in
               OCPP) in the UpdateFirmwareRequest.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to securely download and install a new
                    firmware by sending an UpdateFirmwareRequest with a signingCertificate.

Purpose             To verify if the CSMS is able to handle a Charging Station setting connectors to
                    Unavailable while preparing a firmware update when there is a transaction ongoing.

Prerequisite(s)     The CSMS is able to request a new firmware update when there is a transaction ongoing on
                    the Charging Station.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a UpdateFirmwareRequest
2. The Test System responds with a UpdateFirmwareResponse
    With status Accepted
3. The Test System sends a FirmwareStatusNotificationRequest.
    With status DownloadScheduled
4. The CSMS responds with a FirmwareStatusNotificationResponse.
5. The Test System notifies the CSMS about the state change of all connectors that don’t have a running
   transaction.
    Message: StatusNotificationRequest
    - connectorStatus Unavailable
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Unavailable"
    - component.name "Connector"
    - variable.name "AvailabilityState"
6. The CSMS responds accordingly.
7. Execute Reusable State StopAuthorized
    Note(s) Wait <configured transaction duration> before executing this step
8. Execute Reusable State EVConnectedPostSession
9. Execute Reusable State EVDisconnected
10. The Test System sends a FirmwareStatusNotificationRequest.
    With status Downloading
    Note(s):
    - This step will be executed after the given retrieveDateTime from step 1 has been reached.
11. The CSMS responds with a FirmwareStatusNotificationResponse.
12. The Test System sends a FirmwareStatusNotificationRequest.
    With status Downloaded
13. The CSMS responds with a FirmwareStatusNotificationResponse.
14. The Test System sends a FirmwareStatusNotificationRequest.
    With status SignatureVerified
15. The CSMS responds with a FirmwareStatusNotificationResponse.
16. The Test System sends a FirmwareStatusNotificationRequest.
    With status Installing
17. The CSMS responds with a FirmwareStatusNotificationResponse.
18. The Test System sends a FirmwareStatusNotificationRequest.
    With status InstallRebooting
19. The CSMS responds with a FirmwareStatusNotificationResponse.
20. The Test System sends a BootNotificationRequest
    With reason FirmwareUpdate
21. The CSMS responds with a BootNotificationResponse
22. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
23. The CSMS responds accordingly.
24. The Test System sends a FirmwareStatusNotificationRequest.
    With status Installed
25. The CSMS responds with a FirmwareStatusNotificationResponse.

Tool validations
* Step 1:
    Message UpdateFirmwareRequest
    - firmware.signingCertificate <configured signingCertificate>
* Step 19:
    Message BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.15. Page 415 - (2026-04) - L01.FR.04 - removed ECSchnorr algorithm option and clarify the signature
        verification the Charging Station must do
        (Part 2 errata - applies to this test via use case L01)
        |  | ID. | Precondition | Requirements | Note |
        | Old | L01.FR.04 | When the Charging Station has successfully downloaded the new firmware | The
          signature SHALL be validated, by calculating the signature over the entire firmware file using the
          RSA-PSS or ECSchnorr algorithm for signing, and the SHA256 algorithm for calculating hash values. |
          |
        | New | L01.FR.04 | When the Charging Station has successfully downloaded the new firmware | The
          charging station SHALL verify the signature from the UpdateFirmwareRequest with the hash over the
          entire received firmware file computed using the signature hash algorithm. | The RSA-PSS or ECDSA
          algorithm is used for signing. Please refer to section [certificate_properties] for more details
          about signature algorithms and computing hash values. |
"""
