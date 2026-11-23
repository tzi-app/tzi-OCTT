# Setting up your CSMS for tzi-OCTT

tzi-OCTT plays the Charging Station side of the OCA OCTT test cases against your CSMS: 252 OCPP 2.0.1 test files
(blocks A–P) and 75 OCPP 1.6J test files. This guide takes you from a fresh checkout to a test run against your own
CSMS.

You will:

1. [Install tzi-OCTT](#step-1--install-tzi-octt)
2. [Set up TLS on your CSMS](#step-2--set-up-tls-on-your-csms)
3. [Register the six test charging stations](#step-3--register-the-charging-stations)
4. [Add the ID tokens](#step-4--add-the-id-tokens)
5. [Configure a tariff](#step-5--configure-a-tariff-block-i)
6. [Set up ISO 15118 contract certificates and OCSP](#step-6--set-up-iso-15118-contract-certificates-and-ocsp)
7. [Implement the trigger API](#step-7--implement-the-trigger-api), which most tests depend on
8. [Point tzi-OCTT at your CSMS](#step-8--point-tzi-octt-at-your-csms)
9. [Run the tests](#step-9--run-the-tests)
10. [Reset the stations before a rerun](#step-10--reset-the-stations-before-a-rerun)

Steps 2–7 are changes in your CSMS. Their default values are in `pytest.ini`; if your CSMS needs different values, change
them in step 8.

---

## Step 1 — Install tzi-OCTT

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Run pytest from the repository root, because the certificate paths in `pytest.ini` are relative to it.

## Step 2 — Set up TLS on your CSMS

Every test connects over TLS, security profile 1 included. Your CSMS needs a secure WebSocket endpoint; the default is
`wss://localhost:9000` (`CSMS_ADDRESS`). The certificates are in `certs/`. To make new ones, run
`./generate_certs.sh`, which regenerates all of them.

1. **Server certificates.** Serve **both** of these. Each is for `localhost` and is issued by `certs/ca.pem`:
   - `certs/server.pem` + `certs/server.key` (ECDSA)
   - `certs/server_rsa.pem` + `certs/server_rsa.key` (RSA)

   TC_A_04 and TC_A_07 (and 1.6 TC_086 and TC_087) check all four TLS 1.2 cipher suites of A00.FR.318. Two of them need
   an EC certificate and two an RSA certificate. The tests verify the server certificate against `TLS_CA_CERT` (`certs/ca.pem`) and check that its
   CN is the host name. If you use your own certificates, point `TLS_CA_CERT` at their root.
2. **Client certificates (security profile 3).** Trust `certs/ca.pem` as the issuer of client certificates.
   - The test station presents `certs/client.pem`, with **CN=CP_1**. If your CSMS checks the CN against the station's
     serial number (A00.FR.405, B01.FR.12), take this into account.
   - The CSMS must refuse `certs/invalid_client.pem`, which is self-signed (TC_A_08).
3. **TLS versions.** Accept TLS 1.2 and higher only, and terminate a handshake with a lower version (TC_A_06).

## Step 3 — Register the charging stations

Register these six stations in your CSMS. The login of a Basic Auth station is its station ID with the password
`test1234` (`BASIC_AUTH_CP_PASSWORD`).

| Station ID | Set by variable | OCPP | Security profile | Authenticates with | Used by |
|---|---|---|---|---|---|
| `CP201_SP1` | `CP201_SP1` | 2.0.1 | 1: Basic Auth (over TLS) | `CP201_SP1` / `test1234` | All 2.0.1 blocks (A–P) |
| `CP202_SP2` | `CP201_SP2` | 2.0.1 | 2: TLS + Basic Auth | `CP202_SP2` / `test1234` | Block A |
| `CP202_SP3` | `CP201_SP3` | 2.0.1 | 3: TLS client certificate | `certs/client.pem` | Block A |
| `CP16_SP1` | `CP16_SP1` | 1.6 | 1: Basic Auth (over TLS) | `CP16_SP1` / `test1234` | Most 1.6 tests |
| `CP16_SP2` | `CP16_SP2` | 1.6 | 2: TLS + Basic Auth | `CP16_SP2` / `test1234` | 1.6 TC_083, which upgrades it to profile 3 |
| `CP16_SP3` | `CP16_SP3` | 1.6 | 3: TLS client certificate | `certs/client.pem` | 1.6 TLS / certificate tests |

- **Register the values, not the variable names.** `CP201_SP2` and `CP201_SP3` are variables whose default values are
  `CP202_SP2` and `CP202_SP3`.
- **Accept each station only with its own security profile.** Block A checks that other profiles are refused.
- **The simulated station has one EVSE with one connector:** EVSE 1, connector 1, connector type `cType2`
  (`CONFIGURED_EVSE_ID`, `CONFIGURED_CONNECTOR_ID`, `CONFIGURED_CONNECTOR_TYPE`). If your CSMS needs EVSEs registered in
  advance, register this one.

## Step 4 — Add the ID tokens

| Token | Type | Status in your CSMS | Group | Set by variables | Used by |
|---|---|---|---|---|---|
| `TAG-001` | ISO14443 | Accepted | GROUP001 | `VALID_ID_TOKEN`, `VALID_ID_TOKEN_TYPE` | B, C, E–L, N; 1.6 |
| `100000C01` | Central | Accepted | GROUP001 | `VALID_IDTOKEN_IDTOKEN`, `VALID_IDTOKEN_TYPE` | O |
| `100000C39B` | Central | Accepted | GROUP001 | `VALID_ID_TOKEN_2`, `VALID_ID_TOKEN_TYPE_2` | C |
| `100000C02` | ISO14443 | Invalid (or unknown) | – | `INVALID_ID_TOKEN`, `INVALID_ID_TOKEN_TYPE` | C, E; 1.6 |
| `100000C06` | Central | Blocked | – | `BLOCKED_ID_TOKEN`, `BLOCKED_ID_TOKEN_TYPE` | C; 1.6 |
| `100000C07` | Central | Expired | – | `EXPIRED_ID_TOKEN`, `EXPIRED_ID_TOKEN_TYPE` | C; 1.6 |
| `MASTERC47` | Central | Accepted (master pass) | GROUP001 | `MASTERPASS_ID_TOKEN`, `MASTERPASS_ID_TOKEN_TYPE`, `MASTERPASS_GROUP_ID` | C |
| `GROUP001` | Central | Accepted (the group token) | – | `GROUP_ID` | C, H |
| `EMAID001` | eMAID | Accepted (contract; step 6) | – | `EMAID_ID_TOKEN`, `EMAID_ID_TOKEN_TYPE` | C (TC_C_50–52) |

- **Block D's local-list tokens** (`D001001`, `D001002`) are sent by the tests themselves, inside the SendLocalList
  payload (step 7). You do not need to add them.
- **Some 1.6 tests create** Blocked and Expired tokens at run time through `create-token` (step 7).

## Step 5 — Configure a tariff (block I)

Give `CP201_SP1` an energy-based tariff (a price per kWh), so that your CSMS can tell the cost of its transactions:

- **TC_I_01:** after every periodic meter value, the CSMS reports the running cost, either as `totalCost` in the
  TransactionEventResponse or with a CostUpdatedRequest. The test's transaction carries no `Transaction.Begin` meter
  value, so its first periodic reading is also its first reading.
- **TC_I_02:** the final TransactionEventResponse includes `totalCost`.

## Step 6 — Set up ISO 15118 contract certificates and OCSP

TC_C_50, TC_C_51, TC_C_52 and TC_M_24 use the Test System's (V2G) certificate chain in `certs/`. All its keys are ECDSA:

```text
v2g_root_ca.pem  ->  contract_sub_ca.pem  ->  contract_leaf.pem  (CN = EMAID001)
```

1. **Trust `certs/v2g_root_ca.pem`** in your CSMS as the V2G / MO root for contract certificates. For tzi-csms, set
   `CONTRACT_CERTIFICATE_TRUSTED_CA_PEM_PATH`.
   - Without it, a CSMS that verifies the chain (C07.FR.05) answers `CertChainError` (C07.FR.17).
   - TC_M_24 does not need it: the CSMS passes the OCSP response on to the station.
2. **Know `EMAID001` as a valid eMAID** (step 4). The contract certificate's CN equals it.
3. **Let your CSMS reach the services the tests start on `localhost`.** They speak plain HTTP:

   | Service | Port | Tests | What your CSMS does with it |
   |---|---|---|---|
   | Mock OCSP responder (`mock_ocsp_responder.py`) | 19080 | TC_C_50, TC_M_24 | POSTs RFC 6960 OCSP requests to the `responderURL` it was given |
   | | 19081 | TC_C_51 | |
   | | 19082 | TC_C_52 | Same, at the URL the certificates name in their AIA extension (`http://localhost:19082/ocsp`) |
   | Mock CPS proxy (`mock_cps_proxy.py`) | 19081 | TC_M_26, TC_M_28 | Forwards Get15118EVCertificate: POST JSON `{stationId, chargePointId, request: {action, iso15118SchemaVersion, exiRequest}}`, answer `{status, exiResponse}` |

   - The OCSP responder answers like a CA's responder: about the requested certificate, signed by the CA that issued it.
     A sub-CA answer carries the sub-CA certificate.
   - The CPS proxy interface is the one tzi-csms uses (`CPS_PROXY_URL`). If your CSMS reaches its certificate
     provisioning service differently, TC_M_26 and TC_M_28 need an adapter.
4. **To regenerate the chain**, run `./generate_contract_certs.sh`. `CONTRACT_EMAID` sets the CN and
   `CONTRACT_OCSP_URL` sets the AIA URL.

## Step 7 — Implement the trigger API

**OCTT test cases are interactive.** Many of them test a request that the CSMS sends on its own initiative, such as a
reset, a remote start or a reservation. A CSMS sends such a request only when someone asks it to, so the official test
case documents mark that moment as a **Manual Action**: a person has to make the CSMS send the request before the
scenario can go on.

For example, TC_B_20 (Reset Charging Station - Without ongoing transaction):

1. **Manual Action:** "Request the CSMS to reboot the Charging Station with type OnIdle".
2. The CSMS sends a ResetRequest, and the test station answers Accepted.
3. The test station reboots: it sends a BootNotification and the status of its connectors.

Step 2 can only happen after someone has done step 1. To keep a human out of the loop, tzi-OCTT does step 1 over HTTP.
The test sends:

```http
POST http://localhost:5001/api/octt/2.0.1/CP201_SP1/call/Reset
Content-Type: application/json

{"type": "OnIdle"}
```

Your CSMS then sends the ResetRequest, as if a person had asked for the reboot. **So your CSMS has to provide these
endpoints.** 179 of the 252 2.0.1 test files and 58 of the 75 1.6 test files use them. Without the API, nothing starts
the CSMS side of those exchanges, and the tests fail.

**Conventions:**
- Every endpoint is a `POST` with a JSON body (`Content-Type: application/json`) under `CSMS_TRIGGER_ADDRESS`, whose
  default is `http://localhost:5001`.
- Answer with HTTP 200 and a JSON body. The client parses the body as JSON, but no test inspects it. tzi-csms returns
  the station's response payload.
- The client waits up to 30 seconds. The station is connected to your CSMS when a test calls the endpoint.
- Request bodies use the OCPP message's own camelCase field names unless noted otherwise.

### OCPP 2.0.1: `/api/octt/2.0.1/{stationId}/…`

| Endpoint | Body | What your CSMS does |
|---|---|---|
| `call/{Action}` | The OCPP request payload | Sends a CALL with that action and payload to the station. 165 of the 252 test files use it, for the 36 actions listed below |
| `trigger-message` | TriggerMessageRequest payload | Sends TriggerMessage |
| `update-basic-auth-password` | none | Generates a new Basic Auth password and sets it on the station (SetVariables `SecurityCtrlr.BasicAuthPassword`, A01) |
| `get-variables` | `{"getVariableData": [...]}` | Sends GetVariablesRequest(s), split by the station's ItemsPerMessageGetVariables |
| `set-variables` | `{"setVariableData": [...]}` | Sends SetVariablesRequest(s), split by the station's ItemsPerMessageSetVariables |
| `clear-variable-monitoring` | `{"id": [...]}` | Clears these monitors: sends ClearVariableMonitoringRequest(s), split by the station's ItemsPerMessageClearVariableMonitoring (N06.FR.04). Answer once the station has answered them all. TC_N_18 first has your CSMS read that limit through `get-variables` |
| `set-items-per-message` | `{"get_variables": n, "set_variables": n, "get_report": n}`, any of them | Records the station's ItemsPerMessage limits. No OCPP message |
| `set-pending-boot` | `{"pending": true}` or `false` | The station's next BootNotification is answered Pending (`true`) or Accepted (`false`). No OCPP message |
| `set-security-profile` | `{"security_profile": n}` | Records that the station now uses that profile, as after a completed upgrade, and refuses lower profiles from it. No OCPP message |

The actions sent through `call/{Action}`:

> CancelReservation, ChangeAvailability, ClearCache, ClearChargingProfile, ClearDisplayMessage,
> ClearVariableMonitoring, CustomerInformation, DeleteCertificate, GetBaseReport, GetChargingProfiles,
> GetCompositeSchedule, GetDisplayMessages, GetInstalledCertificateIds, GetLocalListVersion, GetLog,
> GetMonitoringReport, GetReport, GetTransactionStatus, InstallCertificate, PublishFirmware,
> RequestStartTransaction, RequestStopTransaction, ReserveNow, Reset, SendLocalList, SetChargingProfile,
> SetDisplayMessage, SetMonitoringBase, SetMonitoringLevel, SetNetworkProfile, SetVariableMonitoring, SetVariables,
> TriggerMessage, UnlockConnector, UnpublishFirmware, UpdateFirmware

### OCPP 1.6: `/api/octt/1.6/{stationId}/{action}`

The body is the OCPP 1.6 request payload, and your CSMS sends the matching CALL to the station. The actions are in
kebab-case:

> cancel-reservation, certificate-signed, change-availability, change-configuration, clear-cache,
> clear-charging-profile, delete-certificate, extended-trigger-message, get-composite-schedule, get-configuration,
> get-diagnostics, get-installed-certificate-ids, get-local-list-version, get-log, install-certificate,
> remote-start-transaction, remote-stop-transaction, reserve-now, reset, send-local-list, set-charging-profile,
> signed-update-firmware, trigger-message, unlock-connector, update-firmware

### Shared

| Endpoint | Body | What your CSMS does |
|---|---|---|
| `/api/octt/set-basic-auth-password` | `{"station_id": "...", "password": "..."}` | Stores a new Basic Auth password for the station. No OCPP message |
| `/api/octt/create-token` | `{"token_id": "...", "status": "Blocked"}` or `"Expired"` | Creates or updates an ID token with that status |

The reference implementation is tzi-csms (`src/octt/`, built with `--features octt-triggers`).

## Step 8 — Point tzi-OCTT at your CSMS

`pytest.ini` holds every setting as a default (`D:`). A default is only used when the environment variable of the same
name is not set, so you can override any setting from your shell:

```bash
export CSMS_ADDRESS=wss://csms.example.test:9000        # your CSMS's WebSocket endpoint
export CSMS_TRIGGER_ADDRESS=http://csms.example.test:5001
export CP201_SP1=MY_TEST_STATION                         # if you registered other station IDs
```

If the CSMS does not run on `localhost`, it still has to reach the mock services of step 6 on this machine's
`localhost` ports 19080–19082. Its server certificate must also match the host name in `CSMS_ADDRESS`. All settings are
listed in the [reference](#reference-all-settings).

## Step 9 — Run the tests

```bash
.venv/bin/pytest -v -p no:warnings ./2.0.1/A/test_tc_a_01_csms.py   # one test
.venv/bin/pytest -v -p no:warnings ./2.0.1/A                        # one block
.venv/bin/pytest -v -p no:warnings ./2.0.1                          # all of 2.0.1
.venv/bin/pytest -v -p no:warnings ./1.6                            # all of 1.6
```

- **Run the two suites in separate sessions.** They have modules with the same names (`trigger.py`, `conftest.py`), so a
  single session with both fails to import.

- **For a first run, go one test file at a time**, block by block, and fix each failure before moving on. Most early
  failures are setup problems; see [troubleshooting](#troubleshooting).
- **`--log-messages` prints every OCPP message** the test sends and receives. [DEBUGGING.md](DEBUGGING.md) shows how
  to read it, and how to use it without a terminal, for example in CI.

## Step 10 — Reset the stations before a rerun

Some tests change a station's configuration in your CSMS: its Basic Auth password (TC_A_09, TC_A_10, 1.6 TC_073) or its
security profile (TC_A_19; 1.6 TC_083, which leaves `CP16_SP2` at profile 3). Before you rerun, restore the stations of step 3: the password `test1234`, the
original security profiles, and no pending boot. Otherwise a later test inherits the change, typically as a refused
login.

---

## Troubleshooting

For any failure, run the test alone with `--log-messages` and compare the messages with the test description
([DEBUGGING.md](DEBUGGING.md)).

| Symptom | Likely cause |
|---|---|
| Most tests fail to connect (HTTP 401, or the connection closes) | The station is not registered with the ID from step 3, or its password or security profile differs |
| `CERTIFICATE_VERIFY_FAILED` | The server certificate is not issued by `TLS_CA_CERT`, or is not for the host in `CSMS_ADDRESS` (step 2) |
| TC_A_04 / TC_A_07 / 1.6 TC_086 / TC_087: a required TLS 1.2 cipher suite is not supported | The CSMS does not offer both an EC and an RSA server certificate (step 2) |
| A test fails right after "trigger" with connection refused / 404 / timeout | The trigger API endpoint is missing or not running at `CSMS_TRIGGER_ADDRESS` (step 7) |
| TC_C_50–52: `certificateStatus` is `CertChainError` | The CSMS does not trust `certs/v2g_root_ca.pem`, or cannot reach ports 19080–19082 (step 6) |
| A login fails in a test that passed before | The station state changed in an earlier test (step 10) |
| TC_I_01 times out waiting for CostUpdated | The CSMS sends no running cost after a periodic meter value (step 5) |

---

## Reference: all settings

Defaults are from `pytest.ini`. Override any of them with an environment variable of the same name.

### Connection

| Variable | Default | Used by |
|---|---|---|
| `CSMS_ADDRESS` | `wss://localhost:9000` | All tests |
| `CSMS_TRIGGER_ADDRESS` | `http://localhost:5001` | All tests that use the trigger API (step 7) |
| `CSMS_ACTION_TIMEOUT` | `30` | Seconds to wait for a CSMS-initiated action: A–I, K–O; 1.6 |

### Stations and authentication

| Variable | Default | Used by |
|---|---|---|
| `CP201_SP1` | `CP201_SP1` | 2.0.1 A–P (security profile 1) |
| `CP201_SP2` | `CP202_SP2` | 2.0.1 A (security profile 2) |
| `CP201_SP3` | `CP202_SP3` | 2.0.1 A (security profile 3) |
| `CP16_SP1` | `CP16_SP1` | 1.6 (security profile 1) |
| `CP16_SP2` | `CP16_SP2` | 1.6 (security profile 2): TC_083 |
| `CP16_SP3` | `CP16_SP3` | 1.6 (security profile 3) |
| `BASIC_AUTH_CP_PASSWORD` | `test1234` | All Basic Auth stations |

### ID tokens

| Variable | Default | Used by |
|---|---|---|
| `VALID_ID_TOKEN`, `VALID_ID_TOKEN_TYPE` | `TAG-001`, `ISO14443` | B, C, E–L, N; 1.6 |
| `VALID_ID_TOKEN_2`, `VALID_ID_TOKEN_TYPE_2` | `100000C39B`, `Central` | C |
| `VALID_IDTOKEN_IDTOKEN`, `VALID_IDTOKEN_TYPE` | `100000C01`, `Central` | O |
| `INVALID_ID_TOKEN`, `INVALID_ID_TOKEN_TYPE` | `100000C02`, `ISO14443` | C, E; 1.6 |
| `BLOCKED_ID_TOKEN`, `BLOCKED_ID_TOKEN_TYPE` | `100000C06`, `Central` | C; 1.6 |
| `EXPIRED_ID_TOKEN`, `EXPIRED_ID_TOKEN_TYPE` | `100000C07`, `Central` | C; 1.6 |
| `GROUP_ID` | `GROUP001` | C, H |
| `MASTERPASS_ID_TOKEN`, `MASTERPASS_ID_TOKEN_TYPE` | `MASTERC47`, `Central` | C |
| `MASTERPASS_GROUP_ID` | `GROUP001` | C |
| `EMAID_ID_TOKEN`, `EMAID_ID_TOKEN_TYPE` | `EMAID001`, `eMAID` | C |
| `LOCAL_LIST_VERSION` | `1` | D, N |

### Station hardware

| Variable | Default | Used by |
|---|---|---|
| `CONFIGURED_EVSE_ID` | `1` | B, E–L, N–P |
| `CONFIGURED_CONNECTOR_ID` | `1` | B, E–P; 1.6 |
| `CONFIGURED_CONNECTOR_TYPE` | `cType2` | H |
| `CONFIGURED_NUMBER_OF_EVSES` | `1` | H |
| `CONFIGURED_NUMBER_PHASES` | `3` | K |

### Timing and metering

| Variable | Default | Used by |
|---|---|---|
| `TRANSACTION_DURATION` | `5` | E, F, G, H, J, L |
| `SAMPLED_METER_VALUES_INTERVAL` | `1` | I, J |
| `CLOCK_ALIGNED_METER_VALUES_INTERVAL` | `1` | J |
| `TX_ENDED_METER_VALUES_INTERVAL` | `1` | J |

### Network profile (block B) and data transfer (block P)

| Variable | Default | Used by |
|---|---|---|
| `CONFIGURED_CONFIGURATION_SLOT` | `1` | B |
| `CONFIGURED_MESSAGE_TIMEOUT` | `30` | B |
| `CONFIGURED_OCPP_INTERFACE` | `Wired0` | B |
| `CONFIGURED_SECURITY_PROFILE` | `2` | B |
| `CONFIGURED_VENDOR_ID` | `tzi.app` | P |
| `CONFIGURED_MESSAGE_ID` | `TestMessage` | P |

### Certificates (step 2)

| Variable | Default | Used by |
|---|---|---|
| `TLS_CA_CERT` | `certs/ca.pem` | A, 1.6, and every `wss://` connection |
| `TLS_CLIENT_CERT`, `TLS_CLIENT_KEY` | `certs/client.pem`, `certs/client.key` | A, 1.6 (security profile 3) |
| `TLS_INVALID_CLIENT_CERT`, `TLS_INVALID_CLIENT_KEY` | `certs/invalid_client.pem`, `certs/invalid_client.key` | A (TC_A_08) |
