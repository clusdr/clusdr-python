"""gRPC channel credentials. Identity is the cluster CA, not the dial hostname."""

from __future__ import annotations

import base64
from pathlib import Path

import grpc

from clusdr._errors import ClusdrError
from clusdr._options import CA_FILE, CERT_FILE, KEY_FILE, Options, env_data_dir, env_insecure, env_server_name

_CN_OID = b"\x06\x03\x55\x04\x03"


def open_channel(opts: Options) -> grpc.Channel:
    if opts.insecure or (not opts.insecure and env_insecure() and not opts.data_dir):
        return grpc.insecure_channel(opts.addr)
    creds, server_name = client_credentials(opts)
    options = (("grpc.ssl_target_name_override", server_name),) if server_name else ()
    return grpc.secure_channel(opts.addr, creds, options=options)


def client_credentials(opts: Options) -> tuple[grpc.ChannelCredentials, str]:
    directory = opts.data_dir or env_data_dir()
    ca, cert, key = _load_files(directory)
    if ca is None:
        raise ClusdrError(
            f"clusdr: TLS enabled but {CA_FILE}/{CERT_FILE}/{KEY_FILE} missing in {directory}; "
            "set CLUSDR_TLS=disabled or pass insecure=True"
        )
    creds = grpc.ssl_channel_credentials(
        root_certificates=ca,
        private_key=key,
        certificate_chain=cert,
    )
    name = opts.server_name or env_server_name() or cn_from_pem(cert or b"")
    if not name:
        raise ClusdrError(
            "clusdr: TLS hostname unknown; set CLUSDR_TLS_SERVER_NAME or server_name= to the peer node id"
        )
    return creds, name


def cn_from_pem(pem: bytes) -> str:
    """Return the last Common Name in a PEM certificate (subject after issuer)."""
    der = _pem_certs(pem)
    last = ""
    for block in der:
        last = _last_cn(block) or last
    return last


def _load_files(directory: str) -> tuple[bytes | None, bytes | None, bytes | None]:
    base = Path(directory)
    paths = (base / CA_FILE, base / CERT_FILE, base / KEY_FILE)
    if not all(p.is_file() for p in paths):
        return None, None, None
    return paths[0].read_bytes(), paths[1].read_bytes(), paths[2].read_bytes()


def _pem_certs(pem: bytes) -> list[bytes]:
    out: list[bytes] = []
    chunks: list[bytes] = []
    inside = False
    for line in pem.splitlines():
        line = line.strip()
        if line.startswith(b"-----BEGIN"):
            inside = True
            chunks = []
            continue
        if line.startswith(b"-----END"):
            if chunks:
                out.append(base64.b64decode(b"".join(chunks)))
            inside = False
            continue
        if inside:
            chunks.append(line)
    return out


def _last_cn(der: bytes) -> str:
    last = ""
    start = 0
    while True:
        i = der.find(_CN_OID, start)
        if i < 0:
            return last
        j = i + len(_CN_OID)
        if j >= len(der):
            return last
        tag = der[j]
        j += 1
        if tag not in (0x0C, 0x13, 0x16):
            start = i + 1
            continue
        length, j = _asn1_length(der, j)
        if length < 0 or j + length > len(der):
            start = i + 1
            continue
        last = der[j : j + length].decode("utf-8", "replace")
        start = j + length


def _asn1_length(data: bytes, i: int) -> tuple[int, int]:
    if i >= len(data):
        return -1, i
    first = data[i]
    i += 1
    if first < 0x80:
        return first, i
    n = first & 0x7F
    if n == 0 or n > 2 or i + n > len(data):
        return -1, i
    return int.from_bytes(data[i : i + n], "big"), i + n
