"""
Test case name      Receive Driver Tariff - Goodflow
Test case Id        TC_I_109_CSMS
Use case Id(s)      I08
Requirement(s)      I08.FR.01

Requirement Details:
    I08.FR.01: CSMS SHALL respond with an AuthorizeResponse with a tariff field and any other relevant fields
               (like idTokenInfo).
        Precondition: When CSMS receives an AuthorizeRequest for an idToken that is accepted for charging and
                      for which a driver-specific tariff exists
        Note: The details of the authorization process are described in chapter C. Authorization.
System under test   CSMS

Description         To support receiving the driver-specific tariff to enable local cost calculation based on
                    a tariff for this driver.

Purpose             To verify if the CSMS supports driver tariffs.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0

Configuration State CSMS is configured to provide a driver specific tariff for <Configured
                    valid_idtoken_idtoken> that specifies:
                    - currency: <not omitted>
                    - energy price: 0.25 per kWh (ex VAT), vat 20%
                    - idle price: 0.10 per minute (ex VAT), vat 20%
                    - fixed fee: 0.50 (ex VAT), vat 20%

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken_idtoken>
2. The CSMS responds with AuthorizeResponse

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status must be Accepted
    - tariff.tariffId must be <not omitted>
    - tariff.currency must be <not omitted>
    - tariff.energy.prices[0].priceKwh must be 0.25
    - tariff.energy.taxRates[0].tax must be 20
    - tariff.energy.taxRates[0].type must be VAT
    - tariff.idleTime.prices[0].priceMinute must be 0.10
    - tariff.idleTime.taxRates[0].tax must be 20
    - tariff.idleTime.taxRates[0].type must be VAT
    - tariff.fixedFee.prices[0].priceFixed must be 0.50
    - tariff.fixedFee.taxRates[0].tax must be 20
    - tariff.fixedFee.taxRates[0].type must be VAT

Post scenario validations:
    N/a
"""
