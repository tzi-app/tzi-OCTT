# Certificates for tzi-OCTT Test Runs

This directory contains the **test certificates and keys** (and related test fixtures) used by both tzi-OCTT suites,
OCPP 2.0.1 and OCPP 1.6J, and by the bundled simulator `2.0.1/csms.py`.

> **The private keys are public.** Every key in this folder is committed to the repository, so anyone can create a
> client certificate signed by `ca.pem`, or a contract certificate under `v2g_root_ca.pem`. A CSMS that trusts these
> roots, as the [setup guide](../CSMS_SETUP.md) asks, must stay a local test instance. Never trust them on a CSMS that
> others can reach, or in production.

## Validity

| Files | Valid until | Lifetime when generated |
|---|---|---|
| `server.pem`, `server_rsa.pem`, `client.pem`, `invalid_client.pem` | **2027-02-14** | 365 days |
| `contract_leaf.pem` | 2028-11-22 | 2 years |
| `contract_sub_ca.pem` | 2031-11-22 | 5 years |
| `ca.pem` | 2036-02-12 | 10 years |
| `v2g_root_ca.pem` | 2036-11-20 | 10 years |

Once the server and client certificates have expired, every TLS connection fails certificate verification, and almost
every test fails. Renew them before then: see [Generation](#generation).

## Generation

Run `./generate_certs.sh` from the repository root (it writes to `certs/`). It creates every TLS certificate and key in
this folder:
- a new local CA, `ca.pem` / `ca.key`;
- the server certificates for `localhost`, `server.pem` (ECDSA) and `server_rsa.pem` (RSA). `SERVER_CN` in the script
  sets the host;
- the station's client certificate, `client.pem` (CN=CP_1);
- the self-signed `invalid_client.pem`.

At the end it runs `./generate_contract_certs.sh`, which can also be run on its own. That script creates the ISO 15118
(V2G) certificate chain of the Test System for TC_C_50, TC_C_51, TC_C_52 and TC_M_24: `v2g_root_ca` ->
`contract_sub_ca` -> `contract_leaf`.

**Each run also replaces the roots.** `generate_certs.sh` creates a new CA and a new V2G root every time, so afterwards
your CSMS has to:
1. serve the new `server.pem` / `server.key` and `server_rsa.pem` / `server_rsa.key`;
2. trust the new `ca.pem` as the issuer of client certificates;
3. trust the new `v2g_root_ca.pem` for contract certificates (for tzi-csms:
   `CONTRACT_CERTIFICATE_TRUSTED_CA_PEM_PATH=../tzi-OCTT/certs/v2g_root_ca.pem`).

The tests load the files from this folder (`TLS_CA_CERT`, `TLS_CLIENT_CERT`, … in `pytest.ini`), so they need no
change.

## When to generate your own

The committed certificates work as they are for a local run, and the setup guide uses them. Generate new ones when:
- they are about to expire (see [Validity](#validity));
- your CSMS is not at `localhost`. Set `SERVER_CN` in `generate_certs.sh` to its host: the certificate's CN must be
  the host in `CSMS_ADDRESS`, which TC_A_04 and 1.6 TC_086 check;
- your test CSMS can be reached by others, because the committed keys are public.

The client certificate's CN is `CP_1`. If your CSMS checks the CN against the station's serial number (A00.FR.405,
B01.FR.12), take this into account.

## File Types and Purpose

| File | Type | Purpose |
|---|---|---|
| `ca.pem` / `.key` | Root CA (ECDSA P-256) | Local CA, "Test CSMS Root CA". Issues the server and client certificates. The tests verify the CSMS's server certificate against it (`TLS_CA_CERT`), and the CSMS trusts it as the issuer of client certificates. The simulator `2.0.1/csms.py` signs stations' certificate requests with its key. |
| `ca.srl` | OpenSSL serial file | Serial counter used by OpenSSL when issuing certificates with `-CAcreateserial`. |
| `server.pem` / `.key` | Server certificate (ECDSA P-256) | CSMS server certificate for `localhost` (SAN `localhost`, `127.0.0.1`), for the ECDHE_ECDSA cipher suites. |
| `server_rsa.pem` / `.key` | Server certificate (RSA 2048) | The same for the TLS_RSA cipher suites, which TC_A_04, TC_A_07 and 1.6 TC_086, TC_087 check. |
| `client.pem` / `.key` | Client certificate (ECDSA P-256) | The station's certificate (CN=CP_1) for security profile 3. |
| `invalid_client.pem` / `.key` | Client certificate (self-signed, ECDSA P-256) | Not issued by `ca.pem`. The CSMS must refuse it (TC_A_08). |
| `v2g_root_ca.pem` / `.key` | Root CA (ECDSA P-256) | Root of the Test System's (V2G) certificate chain. The CSMS is configured to trust it. `mock_ocsp_responder.py` signs answers about the sub-CA with its key. |
| `contract_sub_ca.pem` / `.key` | Sub-CA (ECDSA P-256) | Issued by `v2g_root_ca`, with an OCSP URL (AIA). TC_M_24 asks about this certificate. `mock_ocsp_responder.py` signs answers about the contract certificate with its key. |
| `contract_leaf.pem` / `.key` | Contract certificate (ECDSA P-256) | Issued by `contract_sub_ca`, with CN = the configured eMAID (`EMAID001`) and an OCSP URL (AIA). Used by TC_C_50/51/52 (`contract_pki.py`). |
| `iso15118_revoked_cert_hash_data.json` | JSON fixture | Serial numbers that the simulator `2.0.1/csms.py` treats as revoked (`2.0.1/config.json`). No test uses it. |
| `contract_cert.pem` | Contract certificate (self-signed) | Legacy sample. Not referenced by any test, script or configuration; see `contract_leaf.pem`. |
| `iso15118_cert_hash_data.json` | JSON fixture | Legacy sample certificate hash data. Not referenced anywhere; `contract_pki.py` computes this data from the chain. |

## Production Use

For production systems, certificates should be issued and managed using a proper PKI process, not this local test script.

At minimum, production certificate handling should use:

1. CA-issued certificates from trusted infrastructure.
2. Protected private keys (HSM or secure key management).
3. Rotation, revocation, and lifecycle management policies.
4. Environment-specific identities and strict trust-chain validation.
