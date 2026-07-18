#!/usr/bin/env python3
"""Capture a real packet path and bake it into index.html.

Usage:  python3 trace.py example.com [another.host ...]

Runs traceroute, geolocates every public hop (ip-api.com), and injects the
result into the TRACEDATA block of index.html. The page does the rest
(speed-of-light checks, submarine-cable matching, animation).
"""
import ipaddress
import json
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

HTML = Path(__file__).parent / "index.html"
GEO_FIELDS = "status,country,countryCode,city,lat,lon,isp,org,as,query"


def geolocate(ips):
    ips = [ip for ip in ips if ip]
    out = {}
    for i in range(0, len(ips), 100):
        req = urllib.request.Request(
            "http://ip-api.com/batch?fields=" + GEO_FIELDS,
            data=json.dumps([{"query": ip} for ip in ips[i:i + 100]]).encode(),
            headers={"Content-Type": "application/json"})
        for r in json.load(urllib.request.urlopen(req, timeout=30)):
            if r.get("status") == "success":
                out[r["query"]] = {"lat": round(r["lat"], 3), "lon": round(r["lon"], 3),
                                   "city": r.get("city", ""), "cc": r.get("countryCode", ""),
                                   "as": r.get("as", ""), "org": r.get("org") or r.get("isp", "")}
    return out


def run_trace(host):
    print(f"traceroute {host} (30 hops max, ~1 min worst case)...")
    p = subprocess.run(["traceroute", "-n", "-q", "1", "-w", "2", "-m", "30", host],
                       capture_output=True, text=True)
    txt = p.stdout + p.stderr
    m = re.search(r"traceroute to (\S+) \(([0-9.]+)\)", txt)
    if not m:
        sys.exit(f"could not resolve {host}:\n{txt}")
    tgt_host, tgt_ip = m.group(1), m.group(2)
    hops, reached = [], False
    for line in txt.splitlines():
        hm = re.match(r"\s*(\d+)\s+(\*|[0-9.]+)(?:\s+([0-9.]+) ms)?", line)
        if not hm:
            continue
        n, ip = int(hm.group(1)), hm.group(2)
        if ip == "*":
            hops.append({"n": n, "kind": "silent"})
            continue
        priv = not ipaddress.ip_address(ip).is_global
        h = {"n": n, "ip": ip, "rtt": float(hm.group(3)) if hm.group(3) else None,
             "kind": "private" if priv else "public"}
        hops.append(h)
        if ip == tgt_ip:
            reached = True
    while hops and hops[-1]["kind"] == "silent":
        hops.pop()
    dedup = []
    for h in hops:
        if dedup and h["kind"] != "silent" and dedup[-1].get("ip") == h.get("ip"):
            continue
        dedup.append(h)
    return {"host": tgt_host, "ip": tgt_ip, "hops": dedup, "reached": reached}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    html = HTML.read_text()
    m = re.search(r"/\*__TRACES_START__\*/\nconst TRACEDATA=(.*?);\n/\*__TRACES_END__\*/", html, re.S)
    if not m:
        sys.exit("TRACEDATA markers not found in index.html")
    data = json.loads(m.group(1))

    my_ip = urllib.request.urlopen("https://api.ipify.org", timeout=10).read().decode()
    raws = [run_trace(h) for h in sys.argv[1:]]
    all_ips = {my_ip}
    for r in raws:
        all_ips.add(r["ip"])
        all_ips.update(h["ip"] for h in r["hops"] if h["kind"] == "public")
    print(f"geolocating {len(all_ips)} IPs...")
    geo = geolocate(sorted(all_ips))
    if my_ip in geo:
        data["origin"] = {"ip": my_ip, "geo": geo[my_ip]}
    data["captured"] = date.today().isoformat()

    for r in raws:
        for h in r["hops"]:
            if h["kind"] == "public":
                h["geo"] = geo.get(h["ip"])
        tr = {"id": r["host"], "title": r["host"], "region": "· " + date.today().isoformat(),
              "host": r["host"], "dst": {"ip": r["ip"], "geo": geo.get(r["ip"])},
              "reached": r["reached"], "hops": r["hops"]}
        data["traces"] = [t for t in data["traces"] if t["id"] != tr["id"]]
        data["traces"].insert(0, tr)
        n_public = sum(1 for h in r["hops"] if h["kind"] == "public")
        print(f"  {r['host']}: {len(r['hops'])} hops ({n_public} public), reached={r['reached']}")

    packed = json.dumps(data, separators=(",", ":"))
    html = html[:m.start()] + "/*__TRACES_START__*/\nconst TRACEDATA=" + packed + ";\n/*__TRACES_END__*/" + html[m.end():]
    HTML.write_text(html)
    print(f"baked into {HTML} — open it, your trace is the first tab")


if __name__ == "__main__":
    main()
