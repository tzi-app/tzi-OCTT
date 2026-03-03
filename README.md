# OCPP CSMS Test Suite

Python (`pytest`) implementation of OCTT scenarios for CSMS (Central System Management System) verification against OCPP 2.0.1 and OCPP 1.6J.

Based on:
- `OCPP 2.0.1 Specification, Edition 4 (2025-12-03)`
- `OCPP 1.6J Specification, (2025-11)`

## Project Structure

```
├── 2.0.1/                 # OCPP 2.0.1 test suite
│   ├── A/ … P/            # Test blocks (Sections A through P)
│   ├── reusable_states/   # Shared preconditions and reusable scenario states
│   ├── schema/            # JSON schema assets used by tests
│   ├── conftest.py        # Pytest fixtures and shared setup
│   ├── csms.py            # Minimal in-memory CSMS for local validation
│   ├── config.json        # Runtime configuration for csms.py
│   └── trigger.py         # CSMS trigger utility
├── 1.6/                   # OCPP 1.6J test suite
│   ├── test_tc_*.py       # Test cases (TC_001 – TC_088)
│   ├── charge_point.py    # Mock charge point for 1.6J tests
│   ├── conftest.py        # Pytest fixtures and shared setup
│   ├── reusable_state*.py # Reusable scenario states
│   └── trigger.py         # CSMS trigger utility
├── certs/                 # TLS certificates for security profile tests
├── tzi_charge_point.py    # Mock charge point (2.0.1)
├── utils.py               # Shared helpers (auth, ids, timestamps, etc.)
├── pytest.ini             # Default environment and pytest settings
└── requirements.txt       # Python dependencies
```

## Implemented Coverage

### OCPP 2.0.1

- `A` Security: 14
- `B` Provisioning: 22
- `C` Authorization: 16
- `D` Local Authorization List Management: 6
- `E` Transactions: 27
- `F` Remote Control: 15
- `G` Availability: 10
- `H` Reservation: 9
- `I` Tariff and Cost: 2
- `J` Meter Values: 9
- `K` Smart Charging: 32
- `L` Firmware Management: 19
- `M` Certificate Management: 18
- `N` Diagnostics: 30
- `O` Display Message: 21
- `P` Data Transfer: 2

**OCPP 2.0.1 total: 252 tests**

### OCPP 1.6J

75 test cases covering core charging station operations, authorization, transactions, smart charging, firmware management, and certificate handling.

**OCPP 1.6J total: 75 tests**

**Combined total: 327 tests**

## Test Artifacts

- OCPP 2.0.1 test files follow `test_tc_<section>_<id>_csms.py` naming (e.g., `test_tc_k_01_csms.py`).
- OCPP 1.6J test files follow `test_tc_<number>_csms.py` naming (e.g., `test_tc_001_csms.py`).
- Mermaid sequence diagrams are included for all tests.
- Reusable states are in `reusable_states/` (2.0.1) and `reusable_state*.py` (1.6J) to keep setup consistent.

## CSMS Trigger Server

Many OCTT test scenarios require CSMS-initiated actions (e.g., RemoteStartTransaction, Reset, SetChargingProfile). In a manual OCTT run, a human operator would trigger these flows through the CSMS UI. To automate this, the test suite uses a **trigger server** — an HTTP API exposed by the CSMS that lets tests programmatically instruct the CSMS to send OCPP CALL messages to a connected charging point.

Tests call the trigger server via helper modules:

- `2.0.1/trigger.py` — triggers for OCPP 2.0.1 tests (`trigger_v201()`, `send_call()`, `reset()`, `get_variables()`, etc.)
- `1.6/trigger.py` — triggers for OCPP 1.6J tests (`trigger_v16()`, `create_token()`, etc.)

Both modules share a common pattern: send an HTTP POST to the trigger server, which translates it into an OCPP CALL to the target charging point.

### API Convention

```
POST {CSMS_TRIGGER_ADDRESS}/api/octt/{version}/{station_id}/{action}
Content-Type: application/json

{ ...OCPP payload... }
```

Where:
- `{version}` is `2.0.1` or `1.6`
- `{station_id}` is the charging point ID (e.g., `CP201_SP1`)
- `{action}` is a kebab-case action name (e.g., `remote-start-transaction`, `set-variables`)

### Shared Endpoints

These endpoints are version-agnostic:

| Endpoint | Description |
|---|---|
| `POST /api/octt/set-basic-auth-password` | Update a station's Basic Auth password |
| `POST /api/octt/create-token` | Create or update an ID token with a given status (Blocked, Expired, etc.) |

### Configuration

Set `CSMS_TRIGGER_ADDRESS` in `pytest.ini` (default: `http://localhost:5001`). Your CSMS must implement the trigger API endpoints for automated tests to work.

## Charge Points Configuration

To run the full test suite, register **5 charging points** in your CSMS:

### OCPP 2.0.1

| # | Env Variable | Default | Security Profile | Transport | Used By |
|---|---|---|---|-----------|---|
| 1 | `CP201_SP1` | `CP201_SP1` | 1 (Basic Auth) | WSS       | All 2.0.1 test blocks (A–P) |
| 2 | `CP201_SP2` | `CP202_SP2` | 2 (TLS + Basic Auth) | WSS       | Block A only |
| 3 | `CP201_SP3` | `CP202_SP3` | 3 (mTLS) | WSS       | Block A only |

### OCPP 1.6J

| # | Env Variable | Default | Security Profile | Transport | Used By |
|---|---|---|---|-----------|---|
| 4 | `CP16_SP1` | `CP16_SP1` | 1 (Basic Auth) | WSS       | All 1.6J tests |
| 5 | `CP16_SP3` | `CP16_SP3` | 3 (mTLS) | WSS       | 1.6J TLS/certificate tests |

### CSMS Setup

1. **Register charging points** with the IDs, security profiles, and passwords listed above.
2. **Configure EVSE topology** on `CP201_SP1`: EVSE 1 with Connector 1 (type `cType2`), and EVSE 2 with Connector 1 for Master Pass tests (TC_C_47, TC_C_49).
3. **Configure ID tokens** in your CSMS:
   - `VALID_ID_TOKEN` (default `TAG-001`, type `ISO14443`) - status: **Accepted**
   - `INVALID_ID_TOKEN` (default `100000C02`, type `Cash`) - status: **Invalid/Unknown**
   - `BLOCKED_ID_TOKEN` (default `100000C06`) - status: **Blocked** (for Block C and 1.6J)
   - `EXPIRED_ID_TOKEN` (default `100000C07`) - status: **Expired** (for Block C and 1.6J)
   - `MASTERPASS_ID_TOKEN` - status: **Accepted**, with `MASTERPASS_GROUP_ID` (for Block C)
4. **Configure TLS** (for Block A and 1.6J SP3 tests): valid server-side TLS certificates, client certificate validation for SP3, TLS 1.2+.
5. **Configure tariff** (for Block I): energy-based tariff with running cost updates during charging.
6. **Configure HTTP trigger API** (for 1.6J): CSMS must expose a REST API at `CSMS_TRIGGER_ADDRESS` for CSMS-initiated actions.

### Minimal Test Environment Variables

```bash
# Connection
export CSMS_ADDRESS="wss://localhost:9000"
export CSMS_TRIGGER_ADDRESS="http://localhost:5001"  # OCTT trigger service

# Charging Points
export CP201_SP1="CP201_SP1"
export CP201_SP2="CP202_SP2"
export CP201_SP3="CP202_SP3"
export CP16_SP1="CP16_SP1"
export CP16_SP3="CP16_SP3"
export BASIC_AUTH_CP_PASSWORD="test1234"

# Hardware
export CONFIGURED_EVSE_ID="1"
export CONFIGURED_CONNECTOR_ID="1"

# ID Tokens
export VALID_ID_TOKEN="TAG-001"
export VALID_ID_TOKEN_TYPE="ISO14443"

# Timeouts
export CSMS_ACTION_TIMEOUT="30"
export TRANSACTION_DURATION="5"
```

These variables are set in `pytest.ini` and consumed by tests. The 2.0.1 `csms.py` reads its own configuration from `2.0.1/config.json`.

## Installation
```bash
# Install dependencies into your virtual environment
pip install -r requirements.txt
```

## Running Tests

### OCPP 2.0.1

Run one or more blocks:

```bash
pytest -v -p no:warnings ./2.0.1/A ./2.0.1/B ./2.0.1/C
```

Run a specific test:

```bash
pytest -v -p no:warnings ./2.0.1/K/test_tc_k_01_csms.py
```

Run a specific test, logging OCPP bidirectional messages:

```bash
pytest -v -p no:warnings ./2.0.1/K/test_tc_k_01_csms.py --log-messages
```

Run full 2.0.1 suite:

```bash
pytest -v -p no:warnings ./2.0.1
```

### OCPP 1.6J

Run the 1.6J suite:

```bash
pytest -v -p no:warnings ./1.6
```

Run a specific 1.6J test:

```bash
pytest -v -p no:warnings ./1.6/test_tc_001_csms.py
```

### All Tests

Run everything:

```bash
pytest -v -p no:warnings ./2.0.1 ./1.6
```

Collect-only (fast sanity check):

```bash
pytest --collect-only -q
```


## CSMS Simulator

[csms.py](2.0.1/csms.py) provides a minimal in-memory CSMS for validating test behavior locally. It is not intended for production use.

It loads runtime configuration from `2.0.1/config.json` at startup:

- Edit `2.0.1/config.json` to match your setup (ports, CP IDs, connector type, token values, TLS paths, etc.).
- Running `python 2.0.1/csms.py <test_mode>` accepts an optional CLI test-mode override, which takes precedence over the `CSMS_TEST_MODE` value in `config.json`.

Key fields in `config.json`:

- `CSMS_WS_PORT`, `CSMS_WSS_PORT`
- `BASIC_AUTH_CP`, `BASIC_AUTH_CP_F`, `BASIC_AUTH_CP_PASSWORD`
- `CONFIGURED_EVSE_ID`, `CONFIGURED_CONNECTOR_ID`, `CONFIGURED_CONNECTOR_TYPE`, `CONFIGURED_NUMBER_OF_EVSES`
- `VALID_ID_TOKEN`, `VALID_ID_TOKEN_TYPE`, `GROUP_ID`, `MASTERPASS_GROUP_ID`
- `CSMS_SERVER_CERT`, `CSMS_SERVER_KEY`, `CSMS_CA_CERT`, `CSMS_CA_KEY`
- `CSMS_CP_ACTIONS`, `CSMS_TEST_MODE`

For test-runner (`pytest`) environment variables and full per-block requirements, see:

- `pytest.ini`
- [`ChargingPointsConfig.md`](ChargingPointsConfig.md)


## Contributing

Contributions are welcome via pull requests.

## Authors

[tzi.app](https://www.tzi.app)

## License

[MIT](https://choosealicense.com/licenses/mit/)
