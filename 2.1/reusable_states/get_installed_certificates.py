"""
State               GetInstalledCertificates
System under test   CSMS
Description         The hashData from installed certificates of the specified type will be retrieved from the
                    Charging Station
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest with certificateType _<Specified
               certificateType>

1. The CSMS sends a GetInstalledCertificateIdsRequest
2. The Test System responds with a GetInstalledCertificateIdsResponse With status is Accepted
   certificateHashDataChain contains an entry with following values:
   certificateHashDataChain[0].certificateType is <Specified certificateType>
   certificateHashDataChain[0].certificateHashData contains <HashData from the configured certificate of the
   specified certificateType>

Tool validations
* Step 1: Message: GetInstalledCertificateIdsRequest - certificateType must be <Specified certificateType>
Post condition      Certificate of the specified certificateType is retrieved from the Charging Station.
"""
