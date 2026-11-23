"""
State               CertificateInstalled
System under test   CSMS
Description         A pre configured certificate of the specified certificateType will be installed.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Trigger the CSMS to send an InstallCertificateRequest with certificateType <Specified
               certificateType>

1. The CSMS sends a InstallCertificateRequest
2. The Test System responds with a InstallCertificateResponse With status is Accepted

Tool validations
* Step 1: Message: InstallCertificateRequest
  - certificateType must be <Specified certificateType>
  - certificate must be <The configured certificate of the specified certificateType.>
Post condition      Certificate of the specified certificateType is stored at the Charging Station.
"""
