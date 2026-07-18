# tracka·packet

**Where does a packet actually go?** Not a metaphor, not a fake animation — real
traceroutes from my machine in Thiruvananthapuram, drawn over the real geometry of
the world's submarine cable network.

**Live: https://vaibhavgit9210.github.io/tracka-packet/**

Pick a destination and watch the packet leave the house: through the home router and
Jio's carrier-grade NAT maze, out of the country at a real cable landing station,
along the actual seabed path of SeaMeWe-4 or AAE-1 or WACS, and back up on another
continent — every hop annotated with who owns it, where it is, and how long it took.

## What makes it real

- **Real traceroutes** — captured with `traceroute -n -q 1`, one UDP probe per hop.
  Seven destinations across six continents, baked into the page.
- **Real cable geometry** — 717 submarine cables + 1,918 landing stations from
  TeleGeography's [submarinecablemap.com](https://www.submarinecablemap.com) data;
  ocean crossings snap to the nearest real cable and name it (best-fit guess).
- **Speed-of-light lie detector** — IP geolocation databases report *registry*
  addresses, not physical ones (Google's Mumbai edge claims Mountain View). Every
  hop is checked against physics: light in fiber covers ~102 km per RTT-millisecond,
  so a hop whose claimed location is unreachable in its measured RTT gets flagged
  red (`✕ REG:`) instead of drawn — and absurd geographic detours implied by
  registry data get skipped, with an explanation in the story log.
- **Honest gaps** — silent routers, unconfirmed final legs (dashed), and CDN
  anycast (mit.edu and google.com never leave Asia — that's the real answer).
- **Satellites: 0** — unless you're on Starlink, intercontinental traffic goes by
  sea. Paste a Starlink trace and it will tell you.

## Trace your own packet

Browsers can't send traceroute probes (no raw sockets), so:

- **On the live page**: `+ TRACE YOUR OWN` → run `traceroute -n -q 1 host` in a
  terminal, paste the output. Geolocation happens in your browser (ipwho.is).
- **Baked into the page**: `python3 trace.py example.com` runs the traceroute,
  geolocates every hop, and injects the trace into `index.html` permanently.

## House style

Single file, no build step, no CDN, no frameworks. All map, cable, and trace data
is inline (~420 KB); the deployed page works offline and under a strict CSP.
Everything — projection, great-circle math, cable matching, the animation — is
plain canvas + vanilla JS.

Data credits: [TeleGeography](https://www.submarinecablemap.com) (cables, CC BY-NC-SA),
[Natural Earth](https://www.naturalearthdata.com) (coastlines, public domain),
[ip-api.com](https://ip-api.com) / [ipwho.is](https://ipwho.is) (geolocation).
