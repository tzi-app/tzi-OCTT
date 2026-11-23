#!/usr/bin/env bash
# Test PKI for the ISO 15118 certificate tests TC_C_50, TC_C_51, TC_C_52 and TC_M_24: the
# "configured (V2G) certificate chain" of the Test System. Like ISO 15118, all keys are ECDSA
# prime256v1.
#
#   v2g_root_ca      Root CA. The CSMS has to trust it; in tzi-csms set
#                    CONTRACT_CERTIFICATE_TRUSTED_CA_PEM_PATH=../tzi-OCTT/certs/v2g_root_ca.pem
#   contract_sub_ca  Sub-CA, issued by the root.
#   contract_leaf    Contract certificate, issued by the sub-CA. Its CN is the configured eMAID.
#
# The sub-CA and the contract certificate name the OCSP service of the Test System
# (mock_ocsp_responder.py) in their Authority Information Access extension. contract_pki.py
# loads the chain; mock_ocsp_responder.py signs its answers with these keys.
#
# Usage, from the repository root: ./generate_contract_certs.sh
#   CONTRACT_EMAID     CN of the contract certificate (default EMAID001, pytest.ini EMAID_ID_TOKEN)
#   CONTRACT_OCSP_URL  OCSP responder URL in the certificates
#                      (default http://localhost:19082/ocsp, the port TC_C_52 listens on)
set -e

OUTPUT_DIR="${OUTPUT_DIR:-certs}"
CONTRACT_EMAID="${CONTRACT_EMAID:-EMAID001}"
CONTRACT_OCSP_URL="${CONTRACT_OCSP_URL:-http://localhost:19082/ocsp}"

mkdir -p "$OUTPUT_DIR"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

random_serial() { echo "0x$(openssl rand -hex 16)"; }

echo "Generating the ISO 15118 certificate chain (prime256v1)..."
echo

############################################
# Root CA (self-signed)
############################################

openssl ecparam -genkey -name prime256v1 -noout -out "$OUTPUT_DIR/v2g_root_ca.key"
openssl req -new -key "$OUTPUT_DIR/v2g_root_ca.key" \
  -subj "/CN=TZI Test V2G Root CA/O=TZI Test" -out "$work/root.csr"
cat > "$work/root.ext" <<EOF
basicConstraints=critical,CA:TRUE
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
EOF
openssl x509 -req -in "$work/root.csr" -signkey "$OUTPUT_DIR/v2g_root_ca.key" \
  -set_serial "$(random_serial)" -days 3650 -sha256 \
  -extfile "$work/root.ext" -out "$OUTPUT_DIR/v2g_root_ca.pem"

echo "  Root CA:              $OUTPUT_DIR/v2g_root_ca.pem"

############################################
# Sub-CA (issued by the root)
############################################

openssl ecparam -genkey -name prime256v1 -noout -out "$OUTPUT_DIR/contract_sub_ca.key"
openssl req -new -key "$OUTPUT_DIR/contract_sub_ca.key" \
  -subj "/CN=TZI Test MO Sub-CA/O=TZI Test" -out "$work/sub_ca.csr"
cat > "$work/sub_ca.ext" <<EOF
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
authorityInfoAccess=OCSP;URI:$CONTRACT_OCSP_URL
EOF
openssl x509 -req -in "$work/sub_ca.csr" \
  -CA "$OUTPUT_DIR/v2g_root_ca.pem" -CAkey "$OUTPUT_DIR/v2g_root_ca.key" \
  -set_serial "$(random_serial)" -days 1825 -sha256 \
  -extfile "$work/sub_ca.ext" -out "$OUTPUT_DIR/contract_sub_ca.pem"

echo "  Sub-CA:               $OUTPUT_DIR/contract_sub_ca.pem"

############################################
# Contract certificate (issued by the sub-CA)
############################################

openssl ecparam -genkey -name prime256v1 -noout -out "$OUTPUT_DIR/contract_leaf.key"
openssl req -new -key "$OUTPUT_DIR/contract_leaf.key" \
  -subj "/CN=$CONTRACT_EMAID/O=TZI Test" -out "$work/leaf.csr"
cat > "$work/leaf.ext" <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyAgreement
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
authorityInfoAccess=OCSP;URI:$CONTRACT_OCSP_URL
EOF
openssl x509 -req -in "$work/leaf.csr" \
  -CA "$OUTPUT_DIR/contract_sub_ca.pem" -CAkey "$OUTPUT_DIR/contract_sub_ca.key" \
  -set_serial "$(random_serial)" -days 730 -sha256 \
  -extfile "$work/leaf.ext" -out "$OUTPUT_DIR/contract_leaf.pem"

echo "  Contract certificate: $OUTPUT_DIR/contract_leaf.pem (CN=$CONTRACT_EMAID, OCSP $CONTRACT_OCSP_URL)"
