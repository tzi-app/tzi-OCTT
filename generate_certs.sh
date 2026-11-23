#!/usr/bin/env bash
set -e

OUTPUT_DIR="certs"
SERVER_CN="localhost"

mkdir -p "$OUTPUT_DIR"

echo "Generating ECDSA certificates (prime256v1)..."
echo

############################################
# 1️⃣ Root CA (ECDSA, self-signed)
############################################

openssl ecparam -genkey -name prime256v1 -out $OUTPUT_DIR/ca.key

openssl req -x509 -new \
  -key $OUTPUT_DIR/ca.key \
  -sha256 -days 3650 \
  -out $OUTPUT_DIR/ca.pem \
  -subj "/CN=Test CSMS Root CA/O=TZI Test"

echo "  CA cert:             $OUTPUT_DIR/ca.pem"


############################################
# 2️⃣ Server Certificate (signed by CA)
############################################

openssl ecparam -genkey -name prime256v1 -out $OUTPUT_DIR/server.key

openssl req -new \
  -key $OUTPUT_DIR/server.key \
  -out $OUTPUT_DIR/server.csr \
  -subj "/CN=$SERVER_CN"

cat > $OUTPUT_DIR/server.ext <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=@alt_names

[alt_names]
DNS.1=$SERVER_CN
IP.1=127.0.0.1
EOF

openssl x509 -req \
  -in $OUTPUT_DIR/server.csr \
  -CA $OUTPUT_DIR/ca.pem \
  -CAkey $OUTPUT_DIR/ca.key \
  -CAcreateserial \
  -out $OUTPUT_DIR/server.pem \
  -days 365 \
  -sha256 \
  -extfile $OUTPUT_DIR/server.ext

rm $OUTPUT_DIR/server.csr $OUTPUT_DIR/server.ext

echo "  Server cert (ECDSA): $OUTPUT_DIR/server.pem (CN=$SERVER_CN)"


############################################
# 2b️⃣ Server Certificate (RSA, signed by CA)
#     Required for TLS_RSA_WITH_AES_* ciphers
#     per OCPP 2.0.1 A00.FR.318
############################################

openssl genrsa -out $OUTPUT_DIR/server_rsa.key 2048

openssl req -new \
  -key $OUTPUT_DIR/server_rsa.key \
  -out $OUTPUT_DIR/server_rsa.csr \
  -subj "/CN=$SERVER_CN"

cat > $OUTPUT_DIR/server_rsa.ext <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=@alt_names

[alt_names]
DNS.1=$SERVER_CN
IP.1=127.0.0.1
EOF

openssl x509 -req \
  -in $OUTPUT_DIR/server_rsa.csr \
  -CA $OUTPUT_DIR/ca.pem \
  -CAkey $OUTPUT_DIR/ca.key \
  -CAcreateserial \
  -out $OUTPUT_DIR/server_rsa.pem \
  -days 365 \
  -sha256 \
  -extfile $OUTPUT_DIR/server_rsa.ext

rm $OUTPUT_DIR/server_rsa.csr $OUTPUT_DIR/server_rsa.ext

echo "  Server cert (RSA):   $OUTPUT_DIR/server_rsa.pem (CN=$SERVER_CN)"


############################################
# 3️⃣ Valid Client Certificate (signed by CA)
############################################

openssl ecparam -genkey -name prime256v1 -out $OUTPUT_DIR/client.key

openssl req -new \
  -key $OUTPUT_DIR/client.key \
  -out $OUTPUT_DIR/client.csr \
  -subj "/CN=CP_1"

cat > $OUTPUT_DIR/client.ext <<EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature
extendedKeyUsage=clientAuth
EOF

openssl x509 -req \
  -in $OUTPUT_DIR/client.csr \
  -CA $OUTPUT_DIR/ca.pem \
  -CAkey $OUTPUT_DIR/ca.key \
  -CAcreateserial \
  -out $OUTPUT_DIR/client.pem \
  -days 365 \
  -sha256 \
  -extfile $OUTPUT_DIR/client.ext

rm $OUTPUT_DIR/client.csr $OUTPUT_DIR/client.ext

echo "  Client cert:         $OUTPUT_DIR/client.pem (CN=CP_1)"


############################################
# 4️⃣ Invalid Client (self-signed, wrong CA)
############################################

openssl ecparam -genkey -name prime256v1 -out $OUTPUT_DIR/invalid_client.key

openssl req -x509 -new \
  -key $OUTPUT_DIR/invalid_client.key \
  -sha256 -days 365 \
  -out $OUTPUT_DIR/invalid_client.pem \
  -subj "/CN=InvalidClient"

echo "  Invalid client cert: $OUTPUT_DIR/invalid_client.pem (self-signed)"


############################################
# 5️⃣ ISO 15118 (V2G) certificate chain for
#     TC_C_50/51/52 and TC_M_24
############################################

echo
OUTPUT_DIR="$OUTPUT_DIR" "$(dirname "$0")/generate_contract_certs.sh"

echo
echo "All certificates generated successfully!"
