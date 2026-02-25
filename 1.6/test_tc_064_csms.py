"""
Test case name      Data Transfer to a Central System
Test case Id        TC_064_CSMS
Feature profile     Core  # NOTE: not explicitly in the test case document table (inferred from OCPP 1.6 spec — to be verified)

Reference           CompliancyTestTool-TestCaseDocument, Table 183, Section 3.20.1, p.157-158/176

Description         The Charge Point sends a vendor specific message to the Central System.

Purpose             To check whether the Central System can reject vendor specific messages.

Prerequisite(s)     The Central System does not support DataTransfer for a specific vendorId.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
1. The Charge Point (OCTT) sends a DataTransfer.req message with a specific vendorId
   to the Central System.
        NOTE: The official doc (p.157) says "to the Charge Point" — likely a typo.

2. The Central System responds with a DataTransfer.conf message.

Tool validations
* Step 2:
    (Message: DataTransfer.conf)
    - The status is Rejected OR UnknownMessageId OR UnknownVendorId

    Note: The status Accepted is allowed, but the vendor should be warned
    about this behaviour.

Expected result(s) / behaviour
    The Central System does not accept the DataTransfer.req.

Message Schemas (OCPP 1.6J):
    DataTransfer.req:
        - vendorId (required, string, maxLength 255): Identifies the vendor-specific implementation
        - messageId (optional, string, maxLength 50): Additional identification field
        - data (optional, string): Data without specified format

    DataTransfer.conf:
        - status (required, enum): Accepted | Rejected | UnknownMessageId | UnknownVendorId
        - data (optional, string): Data without specified format
"""
