# OCPP 1.6J CSMS Compliance Test Suite

Test suite for validating CSMS compliance against the OCPP 1.6J specification.
Based on the TZI CompliancyTestTool-TestCaseDocument (2025-11).

## Prerequisites

- Python 3.10+
- TLS certificates in `certs/`

Install dependencies:

```bash
pip install -r requirements.txt
```

### CSMS WebSocket Endpoint

The CSMS under test must expose a WebSocket (WSS) endpoint that accepts OCPP 1.6J
connections with subprotocol `ocpp1.6`.

The endpoint address is configured via the `CSMS_ADDRESS` environment variable.
The default is `wss://localhost:9000` (set in `pytest.ini`). To point at a different CSMS:

```bash
export CSMS_ADDRESS=wss://my-csms.example.com:443
pytest -v -p no:warnings ./1.6
```

All environment variables in `pytest.ini` use the `D:` (default) prefix, meaning they are
only applied when not already set in the shell. This lets you override any value without
editing `pytest.ini`.

### Trigger Server

Many test scenarios require the CSMS to initiate an action toward the charge point
(e.g., RemoteStartTransaction, Reset, SetChargingProfile). Since the test tool acts as
the charge point, it cannot make the CSMS send these messages on its own.

The **trigger server** solves this by exposing an HTTP REST API that instructs the CSMS
to send a specific OCPP CALL to a connected charge point. This enables fully automated
test runs with no manual operator intervention.

You can choose not to implement the trigger server. In that case, you’ll need to manually perform the required CSMS actions as the tests progress.

For example, when a test starts, the CP will remain idle until you initiate a RemoteStartTransaction from the CSMS.

The trigger endpoint is configured via `CSMS_TRIGGER_ADDRESS` (default: `http://localhost:5001`).

**Trigger API endpoints:**

| Endpoint | Method | Description |
|---|---|---|
| `/api/octt/1.6/{station_id}/{action}` | POST | Send an OCPP CALL to the CP |
| `/api/octt/set-basic-auth-password` | POST | Update a CP's BasicAuth password |
| `/api/octt/create-token` | POST | Create/update an authorization token |

The `{action}` parameter uses kebab-case names corresponding to OCPP actions:

| Action | OCPP Message |
|---|---|
| `remote-start-transaction` | RemoteStartTransaction.req |
| `remote-stop-transaction` | RemoteStopTransaction.req |
| `reset` | Reset.req |
| `unlock-connector` | UnlockConnector.req |
| `get-configuration` | GetConfiguration.req |
| `change-configuration` | ChangeConfiguration.req |
| `change-availability` | ChangeAvailability.req |
| `reserve-now` | ReserveNow.req |
| `cancel-reservation` | CancelReservation.req |
| `trigger-message` | TriggerMessage.req |
| `extended-trigger-message` | ExtendedTriggerMessage.req |
| `set-charging-profile` | SetChargingProfile.req |
| `clear-charging-profile` | ClearChargingProfile.req |
| `get-composite-schedule` | GetCompositeSchedule.req |
| `update-firmware` | UpdateFirmware.req |
| `signed-update-firmware` | SignedUpdateFirmware.req |
| `get-diagnostics` | GetDiagnostics.req |
| `get-log` | GetLog.req |
| `clear-cache` | ClearCache.req |
| `send-local-list` | SendLocalList.req |
| `get-local-list-version` | GetLocalListVersion.req |
| `install-certificate` | InstallCertificate.req |
| `get-installed-certificate-ids` | GetInstalledCertificateIds.req |
| `delete-certificate` | DeleteCertificate.req |
| `certificate-signed` | CertificateSigned.req |

The JSON body of each POST is forwarded as the OCPP CALL payload. For example:

```bash
curl -X POST http://localhost:5001/api/octt/1.6/CP16_SP1/reset \
  -H 'Content-Type: application/json' \
  -d '{"type": "Hard"}'
```

Tests that do **not** require the trigger server (27 of 77) only exercise CP-initiated
messages (BootNotification, Authorize, StartTransaction, etc.) and can run without it.

## Running Tests

Start the CSMS under test and its trigger server, then:

```bash
# Run all 1.6 tests
pytest -v -p no:warnings ./1.6

# Run a specific test
pytest -v -p no:warnings ./1.6/test_tc_010_csms.py

# Enable OCPP message tracing
pytest -v -p no:warnings ./1.6/test_tc_010_csms.py --log-messages
```

## Charge Point Configuration

The CSMS must be configured with the following charge points before running tests.

### Required Charge Points

| CP Identity | Env Variable | Security Profile | Purpose |
|---|---|---|---|
| `CP16_SP1` | `BASIC_AUTH_CP` | SP1 (Basic Auth) | Primary CP for most tests (75 tests) |
| `CP16_SP3` | `SECURITY_PROFILE_3_CP` | SP3 (mTLS) | Client certificate tests (TC_074, TC_087) |

### Authentication

- **SP1 (Basic Auth)**: `CP16_SP1` must accept username=`CP16_SP1`, password=`test1234`
- **SP3 (mTLS)**: `CP16_SP3` connects with client certificate, no BasicAuth header

### Authorization Tokens

The CSMS must recognize these tokens:

| Token | Env Variable | Expected Status |
|---|---|---|
| `TAG-001` | `VALID_ID_TOKEN` | Accepted |
| `100000C01` | `VALID_IDTOKEN_IDTOKEN` | Accepted |
| `100000C39B` | `VALID_ID_TOKEN_2` | Accepted |
| `100000C02` | `INVALID_ID_TOKEN` | Invalid |
| `100000C06` | `BLOCKED_ID_TOKEN` | Blocked |
| `100000C07` | `EXPIRED_ID_TOKEN` | Expired |
| `MASTERC47` | `MASTERPASS_ID_TOKEN` | Accepted (group=GROUP001) |

### Local Authorization List Tokens

| Token | Env Variable |
|---|---|
| `D001001` | `LOCAL_AUTH_LIST_ID_TOKEN` |
| `D001002` | `LOCAL_AUTH_LIST_ID_TOKEN_2` |

## Environment Variables

All variables are configured in `pytest.ini` with the `D:` prefix (defaults, overridable from shell).

### Connection

| Variable | Default | Description |
|---|---|---|
| `CSMS_ADDRESS` | `wss://localhost:9000` | CSMS WebSocket endpoint |
| `CSMS_TRIGGER_ADDRESS` | `http://localhost:5001` | CSMS trigger REST API |
| `CSMS_ACTION_TIMEOUT` | `30` | Timeout (seconds) for CSMS-initiated actions |

### Charge Point Identity

| Variable | Default | Description |
|---|---|---|
| `BASIC_AUTH_CP` | `CP16_SP1` | Primary CP identity (SP1) |
| `BASIC_AUTH_CP_PASSWORD` | `test1234` | BasicAuth password |
| `SECURITY_PROFILE_3_CP` | `CP16_SP3` | SP3 CP identity (mTLS) |
| `NEW_BASIC_AUTH_PASSWORD` | `new_password_12345678` | New password for TC_073 |

### TLS Certificates

| Variable | Description |
|---|---|
| `TLS_CA_CERT` | CA certificate for verifying CSMS server cert |
| `TLS_CLIENT_CERT` | Valid client certificate (SP3) |
| `TLS_CLIENT_KEY` | Valid client private key (SP3) |
| `TLS_INVALID_CLIENT_CERT` | Invalid client certificate (negative tests) |
| `TLS_INVALID_CLIENT_KEY` | Invalid client private key (negative tests) |

### Charge Point Properties

| Variable | Default | Description |
|---|---|---|
| `CONFIGURED_CP_VENDOR` | `tzi.app` | BootNotification vendor name |
| `CONFIGURED_CP_MODEL` | `CP Model 1.0` | BootNotification model name |
| `CONFIGURED_CONNECTOR_ID` | `1` | Physical connector ID |
| `CONFIGURED_EVSE_ID` | `1` | EVSE ID |
| `CONFIGURED_NUMBER_PHASES` | `3` | Number of electrical phases |
| `CONFIGURED_NUMBER_OF_EVSES` | `1` | Number of EVSEs |
| `CONFIGURED_CONNECTOR_TYPE` | `cType2` | Connector type |

### Transaction & Metering

| Variable | Default | Description |
|---|---|---|
| `TRANSACTION_DURATION` | `5` | Simulated transaction duration (seconds) |
| `SAMPLED_METER_VALUES_INTERVAL` | `1` | Interval for sampled meter values |
| `CLOCK_ALIGNED_METER_VALUES_INTERVAL` | `1` | Interval for clock-aligned meter values |
| `TX_ENDED_METER_VALUES_INTERVAL` | `1` | Interval for post-transaction meter values |

## Project Structure

```
1.6/
  conftest.py            # WebSocket connection fixture, SSL context builder
  charge_point.py        # TziChargePoint16 -- test CP with event-based CSMS handlers
  trigger.py             # HTTP helpers: trigger_v16(), set_basic_auth_password(), create_token()
  reusable_states.py     # Shared test states: booted(), authorized(), charging()
  test_tc_*.py           # Individual test cases
../utils.py              # Shared utilities (SSL, CSR, BasicAuth headers, etc.)
../pytest.ini            # Environment variable defaults
../certs/                # TLS certificates
```

## Test Catalog

76 test files, 77 test functions.

### Cold Boot (Section 3.1)

| Test | Description |
|---|---|
| TC_001 | Cold Boot Charge Point |

### Charging Sessions (Section 3.2)

| Test | Description |
|---|---|
| TC_003 | Regular Charging Session -- Plugin First |
| TC_004_1 | Regular Charging Session -- Identification First |
| TC_004_2 | Regular Charging Session -- Identification First -- ConnectionTimeOut |
| TC_005_1 | EV Side Disconnected |

### Cache (Section 3.3)

| Test | Description |
|---|---|
| TC_007 | Regular Start Charging Session -- Cached Id |
| TC_061 | Clear Authorization Data in Authorization Cache |

### Remote Actions (Section 3.4)

| Test | Description |
|---|---|
| TC_010 | Remote Start -- Cable Plugged in First |
| TC_011_1 | Remote Start -- Remote Start First |
| TC_011_2 | Remote Start -- Time Out |
| TC_012 | Remote Stop Charging Session |

### Reset (Section 3.5)

| Test | Description |
|---|---|
| TC_013 | Hard Reset |
| TC_014 | Soft Reset |

### Unlock Connector (Section 3.6)

| Test | Description |
|---|---|
| TC_017_1 | Unlock -- No Charging Session (Not Fixed Cable) |
| TC_017_2 | Unlock -- No Charging Session (Fixed Cable) |
| TC_018_1 | Unlock -- With Charging Session (Not Fixed Cable) |

### Configuration (Section 3.7)

| Test | Description |
|---|---|
| TC_019_1 | Retrieve All Configuration Keys |
| TC_019_2 | Retrieve Specific Configuration Key |
| TC_021 | Change/Set Configuration |

### Authorization Non-Happy (Section 3.8)

| Test | Description |
|---|---|
| TC_023_1 | Start Charging -- Authorize Invalid |
| TC_023_2 | Start Charging -- Authorize Expired |
| TC_023_3 | Start Charging -- Authorize Blocked |
| TC_024 | Start Charging -- Lock Failure |

### Remote Actions Non-Happy (Section 3.9)

| Test | Description |
|---|---|
| TC_026 | Remote Start -- Rejected |
| TC_028 | Remote Stop -- Rejected |

### Unlock Non-Happy (Section 3.10)

| Test | Description |
|---|---|
| TC_030 | Unlock Connector -- Unlock Failure |
| TC_031 | Unlock Connector -- Unknown Connector |

### Power Failure (Section 3.11)

| Test | Description |
|---|---|
| TC_032_1 | Power Failure Boot -- Stop Transaction(s) |

### Offline Behavior (Section 3.12)

| Test | Description |
|---|---|
| TC_037_1 | Offline Start Transaction -- Valid IdTag |
| TC_037_3 | Offline Start Transaction -- Invalid IdTag |
| TC_039 | Offline Transaction (start + stop while offline) |

### Configuration Keys Non-Happy (Section 3.13)

| Test | Description |
|---|---|
| TC_040_1 | Configuration Keys -- NotSupported |
| TC_040_2 | Configuration Keys -- Invalid Value |

### Local Auth List (Section 3.14)

| Test | Description |
|---|---|
| TC_042_1 | Get Local List Version (Not Supported) |
| TC_042_2 | Get Local List Version (Empty) |
| TC_043_1 | Send Local Authorization List -- NotSupported |
| TC_043_3 | Send Local Authorization List -- Failed |
| TC_043_4 | Send Local Authorization List -- Full |
| TC_043_5 | Send Local Authorization List -- Differential |

### Firmware Management (Section 3.15)

| Test | Description |
|---|---|
| TC_044_1 | Firmware Update -- Download and Install |
| TC_044_2 | Firmware Update -- Download Failed |
| TC_044_3 | Firmware Update -- Installation Failed |

### Diagnostics (Section 3.16)

| Test | Description |
|---|---|
| TC_045_1 | Get Diagnostics |

### Reservation (Section 3.17)

| Test | Description |
|---|---|
| TC_046 | Reservation -- Transaction |
| TC_047 | Reservation -- Expire |
| TC_048_1 | Reservation -- Faulted |
| TC_048_2 | Reservation -- Occupied |
| TC_048_3 | Reservation -- Unavailable |
| TC_048_4 | Reservation -- Rejected |
| TC_049 | Reservation of Charge Point (connectorId=0) |
| TC_051 | Cancel Reservation |
| TC_052 | Cancel Reservation -- Rejected |

### Remote Trigger (Section 3.18)

| Test | Description |
|---|---|
| TC_054 | Trigger Message (MeterValues, Heartbeat, StatusNotification, etc.) |
| TC_055 | Trigger Message -- Rejected |

### Smart Charging (Section 3.19)

| Test | Description |
|---|---|
| TC_056 | Central Smart Charging -- TxDefaultProfile |
| TC_057 | Central Smart Charging -- TxProfile |
| TC_059 | Remote Start with Charging Profile |
| TC_066 | Get Composite Schedule |
| TC_067 | Clear Charging Profile |

### Data Transfer (Section 3.20)

| Test | Description |
|---|---|
| TC_064 | Data Transfer to Central System |

### Security (Section 3.21)

| Test | Description | CP |
|---|---|---|
| TC_073 | Update CP Password for Basic Auth | CP16_SP1 |
| TC_074 | Update CP Certificate by CS Request | CP16_SP3 (SP3) |
| TC_075_1 | Install Certificate -- ManufacturerRoot | CP16_SP1 |
| TC_075_2 | Install Certificate -- CentralSystemRoot | CP16_SP1 |
| TC_076 | Delete Certificate (SHA256/384/512) | CP16_SP1 |
| TC_077 | Invalid ChargePointCertificate Security Event | CP16_SP1 |
| TC_078 | Invalid CentralSystemCertificate Security Event | CP16_SP1 |
| TC_079 | Get Security Log | CP16_SP1 |
| TC_080 | Secure Firmware Update | CP16_SP1 |
| TC_081 | Secure Firmware Update -- Invalid Signature | CP16_SP1 |
| TC_083 | Upgrade Security Profile -- Accepted | CP16_SP1 |
| TC_085 | Basic Authentication Validation | CP16_SP1 |
| TC_086 | TLS Server Certificate Validation (SP2) | CP16_SP1 |
| TC_087 | TLS Client Certificate Validation (SP3 mTLS) | CP16_SP3 (SP3) |
| TC_088 | WebSocket Subprotocol Negotiation | CP16_SP1 |

## Architecture

### Connection Fixture

Most tests use the `connection` fixture (via `@pytest.mark.parametrize("connection", [...], indirect=True)`).
It connects to `{CSMS_ADDRESS}/{cp_name}` with BasicAuth headers and `ocpp1.6` subprotocol.
If the CSMS rejects the connection, a `MockConnection(open=False, status_code=...)` is yielded instead.

Security tests (TC_074, TC_086, TC_087, TC_088) connect directly using `websockets.connect()` with custom SSL contexts.

### Trigger API

Tests that validate CSMS-initiated messages use `trigger_v16(station_id, action, body)`.
This sends an HTTP POST to `{CSMS_TRIGGER_ADDRESS}/api/octt/1.6/{station_id}/{action}`
to instruct the CSMS to send the corresponding OCPP CALL to the connected CP.

The test then awaits the matching `asyncio.Event` on the `TziChargePoint16` instance
(e.g., `cp._received_remote_start.wait()`).

### Reusable States

Shared setup sequences to bring the CP into a known state:

- **`booted(cp)`** -- BootNotification + StatusNotification(Available) for connectors 0 and 1
- **`authorized(cp, id_tag)`** -- Authorize.req, assert Accepted
- **`charging(cp, id_tag, connector_id)`** -- Preparing + StartTransaction + Charging; returns `(start_response, transaction_id)`

### TziChargePoint16

Extends `ocpp.v16.ChargePoint` with:

- `suppress=False` override on `call()` so CALLERROR responses raise `OCPPError` exceptions
- Event-based handlers for all CSMS-initiated actions (RemoteStart, Reset, SetChargingProfile, etc.)
- Optional message logging (`--log-messages`) that writes to `/dev/tty` to bypass pytest capture
