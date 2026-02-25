"""
Test case name      Update Charge Point Password for HTTP Basic Authentication
Test case Id        TC_073_CSMS
Section             3.21.1. Secure connection setup
System under test   Central System
Document ref        Table 184, page 158/176 (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)

Description         The Central System can configure a new password for HTTP Basic Authentication, the Central System can
                    send a new value for the BasicAuthPassword Configuration key.

Purpose             To check if the Central System is able to change the Basic Authentication password.

Prerequisite(s)     The Central System supports Security profile 1 and/or 2.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Manual Action: Update the basic authentication password.

    1. The Central System sends a ChangeConfiguration.req
    2. The Charge Point responds with a ChangeConfiguration.conf

    3. The Charge Point disconnects its current connection and reconnects to the Central System
       using the provided password from step 1.

Tool Validations
    * Step 1:
        (Message: ChangeConfiguration.req)
        key is AuthorizationKey
        value contains the hex encoded representation of the basic authentication password
        the Charge Point needs to use when connecting to the Central System.
        Because it is advised to use a randomly generated binary to get maximal entropy,
        the tool only validates if the new password adheres to the OCPP password requirements:
        - The hexadecimal representation of the password has a maximum of 40 characters.
        - The length of the password must be between 16 and 20 bytes.

    * Step 2:
        (Message: ChangeConfiguration.conf)
        status is Accepted

Expected result(s) / behaviour: n/a
"""
