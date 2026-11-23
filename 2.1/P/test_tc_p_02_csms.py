"""
Test case name      Data Transfer to the CSMS - Rejected / Unknown VendorId / Unknown MessageId
Test case Id        TC_P_02_CSMS
Use case Id(s)      P02
Requirement(s)      P02.FR.06, P02.FR.07

Requirement Details:
    P02.FR.06: The recipient SHALL return a status UnknownVendor.
        Precondition: If the recipient of the request has no implementation for the specific vendorId.
    P02.FR.07: The recipient SHALL return status UnknownMessageId.
        Precondition: Upon receipt of DataTransferRequest and in case of a messageId mismatch (if used).
System under test   CSMS

Description         The DataTransfer message to send information for functions that are not supported by OCPP.

Purpose             To verify whether the CSMS is able to handle receiving a DataTransferRequest, even if it
                    does not support any vendor-specific implementations.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a DataTransferRequest with
    - vendorId <Configured vendorId>
    - messageId <Configured messageId>
2. The CSMS responds with a DataTransferResponse

Tool validations
* Step 2:
    Message: DataTransferResponse
    - status must be UnknownVendorId OR UnknownMessageId OR Rejected (Rejected will also be allowed, because
      there are implementers that like to just reject the message when the Charging Station does not support
      any vendor-specific features.

Post scenario validations:
    N/a
"""
