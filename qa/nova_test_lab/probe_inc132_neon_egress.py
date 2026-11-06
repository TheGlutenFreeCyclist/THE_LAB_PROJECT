"""INC132: print ONLY safe diagnostics for GitHub runner -> authorized Neon LAB.

No passwords/URI/host IPs in logs. Never queries data or makes writes.
Expected endpoint is read from verified Neon branch metadata (2026-11-06).
"""
import json
import os
import socket
from psycopg2.extensions import parse_dsn

NEON_TEST_HOST = "ep-blue-lab-bbadr0t9.c-15.us-east-1.aws.neon.tech"
NEON_TEST_ROLE = "nova_r139_qa_reader"
NEON_TEST_DB = "nova_lab"

def connectivity(host, port):
    try:
        addresses=socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)
    except (socket.gaierror,UnicodeError,TypeError,ValueError):
        return "DNS_FAILED"
    if not addresses:
        return "DNS_NO_ADDRESSES"
    outcomes=set()
    for family,socktype,proto,_,sockaddr in addresses[:6]:
        try:
            with socket.socket(family,socktype,proto) as sock:
                sock.settimeout(2.0)
                sock.connect(sockaddr)
                return "TCP_CONNECTED"
        except socket.timeout:
            outcomes.add("TIMEOUT")
        except OSError as e:
            if e.errno in (101, 113): outcomes.add("UNREACHABLE")
            elif e.errno in (111, 61): outcomes.add("REFUSED")
            else: outcomes.add("OTHER_NETWORK_ERROR")
    return "TCP_"+"_OR_".join(sorted(outcomes))

def run():
    ds=os.environ.get("NOVA_TEST_LAB_DATABASE_URL","")
    if not ds:
        print(json.dumps({"suite":"INC132_NEON_EGRESS",
            "status":"BLOCKED_SECRET_MISSING"}))
        return 2
    try:
        conn=parse_dsn(ds)
        secret_host=conn.get("host","")
        secret_port=int(conn.get("port","5432"))
        safe_host=secret_host==NEON_TEST_HOST or (
            secret_host==NEON_TEST_HOST.replace(".c-15.","-pooler.c-15."))
        role_ok=conn.get("user")==NEON_TEST_ROLE
        db_ok=conn.get("dbname")==NEON_TEST_DB
        if not isinstance(secret_host,str) or not secret_host.endswith(".neon.tech"):
            raise ValueError("SECRET_HOST_NOT_NEON")
        if not role_ok or not db_ok or not 1<=secret_port<=65535:
            raise ValueError("SECRET_ROLE_DB_OR_PORT_INVALID")
    except (ValueError,TypeError,OverflowError):
        print(json.dumps({"suite":"INC132_NEON_EGRESS",
            "status":"BLOCKED_SECRET_SCHEMA_INVALID"}))
        return 2
    print(json.dumps({"suite":"INC132_NEON_EGRESS","status":"DIAGNOSTIC_ONLY",
       "expected_endpoint_tcp":connectivity(NEON_TEST_HOST,5432),
       "secret_endpoint_tcp":connectivity(secret_host,secret_port),
       "secret_host_matches_neon_test":safe_host,
       "port_5432":secret_port==5432,
       "role_and_database_correct":role_ok and db_ok,
       "production":"UNTOUCHED",
       "read_only_replay":"SEPARATE_GATE"},sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(run())
