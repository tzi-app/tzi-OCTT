"""
Test case name      Secure Firmware Update - Invalid Signature
Test case Id        TC_081_CSMS
Document Reference  Table 193, page 166/176 (CompliancyTestTool-TestCaseDocument, 2025-11)
Section             3.21.3 Secure firmware update
System under test   Central System  [NOTE: not an explicit field in the test case document, inferred from CSMS suffix - to be verified]

Description         The Charge Point validates the Signature and deems it invalid.

Purpose             To check whether the Central System is able to handle messages from a Charge Point when it reports that
                    the signature is invalid.

Prerequisite(s)     - The Central System supports the Firmware Management feature profile AND
                    - The Central System supports a security profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a SignedUpdateFirmware.req
    2. The Charge Point sends a SignedUpdateFirmware.conf

    [The Charge Point starts downloading the firmware]
    3. The Charge Point sends a SignedFirmwareStatusNotification.req (status: Downloading)
    4. The Central System responds with a SignedFirmwareStatusNotification.conf

    [The Charge Point has finished downloading the firmware]
    5. The Charge Point sends a SignedFirmwareStatusNotification.req (status: Downloaded)
    6. The Central System responds with a SignedFirmwareStatusNotification.conf

    [The Charge Point verifies the signature and deems it invalid]
    7. The Charge Point sends a SignedFirmwareStatusNotification.req (status: InvalidSignature)
    8. The Central System responds with a SignedFirmwareStatusNotification.conf

Tool Validations
    * Step 1:
        (Message: SignedUpdateFirmware.req)
        The firmware.location is <Firmware Download URL from test data>
        The firmware.signature is <An invalid signature.>

    * Step 3:
        (Message: SignedFirmwareStatusNotification.req)
        The status is Downloading

    * Step 5:
        (Message: SignedFirmwareStatusNotification.req)
        The status is Downloaded

    * Step 7:
        (Message: SignedFirmwareStatusNotification.req)
        The status is InvalidSignature

Expected result(s) / behaviour:
    Charge Point: The Charge Point rejects the firmware, because of an invalid signature.
    Central System: The Central System receives and responds to the FirmwareStatusNotification messages.
"""
