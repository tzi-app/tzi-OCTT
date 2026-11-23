"""
Test case name      Get Charging Station Certificate status - Success
Test case Id        TC_M_24_CSMS
Use case Id(s)      M06
Requirement(s)      M06.FR.01, M06.FR.02, M06.FR.03, M06.FR.08, M06.FR.09

Requirement Details:
    M06.FR.01: The CSMS SHALL respond with a GetCertificateStatusResponse.
        Precondition: After receiving a GetCertificateStatusRequest
    M06.FR.02: The CSMS SHALL indicate success by setting status to Accepted in the
               GetCertificateStatusResponse.
        Precondition: M06.FR.01 AND The CSMS was successful in retrieving the OCSP certificate status
    M06.FR.03: The CSMS SHALL include the OCSP response data in the OCSPResult field in the
               GetCertificateStatusResponse.
        Precondition: M06.FR.02
    M06.FR.08: The CSMS SHALL format the response data according to OCSPResponse as defined in IETF RFC 6960,
               formatted according to ASN.1 [X.680].
    M06.FR.09: The OCSPResponse data SHALL be DER encoded.
System under test   CSMS

Description         The Charging Station is able to request the CSMS to get the status of a (V2G) Charging
                    Station certificate.

Purpose             To verify if the CSMS is able to provide the status of a requested (V2G) Charging Station
                    certificate.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends one or more subsequent GetCertificateStatusRequests
    With ocspRequestData contains <hashes from configured (V2G) certificate chain SubCA’s>
2. The CSMS responds with a GetCertificateStatusResponse

Tool validations
* Step 2:
    Message: GetCertificateStatusResponse
    - status Accepted
    - ocspResult <OCSPResponse class as defined in IETF RFC 6960. DER encoded (as defined in IETF RFC 6960),
      and then base64 encoded.>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.34. Page 783 - (2026-09) - New variable ISO15118Ctrlr.DisableOCSPPrefetching [1362] - 2.34.2. Updated
        M06 requirements accordingly
        (Part 2 errata - applies to this test via use case M06)
        Changed requirements

        |  | ID | Precondition | Requirement definition |
        | Old | M06.FR.06 |  | The Charging Station SHALL request and cache the OCSP status for its V2G
          certificates. |
        | New | M06.FR.06 | When an EV request the OCSP status for a V2G certificate | The Charging Station
          SHALL check for its OCSP status in the cache first, and if no OCSP status is found or it is too old,
          Charging Station SHALL request and cache the OCSP status for its V2G certificates. |
        | Old | M06.FR.07 |  | After the Charging Station Certificate has been updated, The Charging Station
          SHALL refresh the cached OCSP data by sending a GetCertificateStatusRequest for the new certificate,
          and also for the intermediate certificates. |
        | New | M06.FR.07 | When the Charging Station’s V2G certifcate has been updated AND
          ISO15118Ctrlr.DisableOCSPrefetching is absent or false | [removed: After the Charging Station
          Certificate has been updated,] The Charging Station SHALL refresh the cached OCSP data by sending a
          GetCertificateStatusRequest for the new certificate, and also for the intermediate certificates. |
        | Old | M06.FR.10 |  | The Charging Station SHALL refresh the cached OCSP data at least once a week. |
        | New | M06.FR.10 | If ISO15118Ctrlr.DisableOSCPPrefetching is absent or false | The Charging Station
          SHALL refresh the cached OCSP data at least once a week. |
"""
