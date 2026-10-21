# LSVIndustry hosting from this Windows PC

The existing Flask application runs under Waitress, with Cloudflare Tunnel providing public HTTPS.

## Current addresses

- Local: http://localhost:5000
- Network: http://192.168.0.116:5000
- Public at setup: https://jesse-spoke-asn-pressing.trycloudflare.com

The public address belongs to this running quick tunnel. A new tunnel gets a new address. The current address is saved in .runtime/hosting.json and printed by the start script. Your LAN address can also change after reconnecting to the network.

## Start again in PowerShell

~~~powershell
Set-Location 'C:\Word\weblsv'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-LSVIndustry.ps1
~~~

This starts both processes in the background, verifies the homepages, and prints the addresses. Running it again reuses its existing processes. You can close the PowerShell window afterward.

Keep the PC powered on, awake, and connected to the internet. The processes do not automatically start after a reboot or sign-out, and this setup does not restart crashed processes. Run the command again after those events. Cloudflare reconnects interrupted tunnel connections while its process remains alive.

To use another available port, stop first, then run the start script with -Port 8080.

## Stop intentionally

~~~powershell
Set-Location 'C:\Word\weblsv'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Stop-LSVIndustry.ps1
~~~

The stop script checks process IDs and creation times so it only stops the processes recorded by this setup.

## LAN access

The Windows firewall rule LSVIndustry-HTTP-5000-PrivateLAN permits TCP 5000 for the Python executable, only from LocalSubnet on the Private profile. Public internet access uses the outbound Cloudflare connection; router port forwarding is unnecessary.

The PC's LAN URL was verified from the PC itself. A second physical device was not available for testing. Devices must share the LAN, and router client isolation can prevent access.

To recreate the rule, run this in an Administrator PowerShell window:

~~~powershell
Set-Location 'C:\Word\weblsv'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Enable-LSVIndustry-LAN.ps1
~~~

Pass the same -Port value to both scripts if changing ports. If you switch Python installations, update the firewall program path accordingly.

## Runtime and maintenance

- run_lsvindustry.py starts the existing app with debugging and traceback exposure disabled.
- Only loopback is trusted for the tunnel's forwarded HTTPS scheme. Session and remember-me cookies receive Secure on HTTPS; local HTTP sessions continue to work.
- The Flask static folder is the public asset root. No project-root file server is started.
- Hidden URL path components are denied, including static/uploads/.gitkeep.
- .env and the existing database stay in their original locations.
- .runtime holds process IDs and local logs; it is ignored by Git and is not served.

The required packages were already installed. If dependencies must be restored, run:

~~~powershell
Set-Location 'C:\Word\weblsv'
python -m pip install -r .\requirements-hosting.txt
~~~

The start script prefers .venv\Scripts\python.exe when present, otherwise python on PATH. If using that virtual environment, install with .\.venv\Scripts\python.exe -m pip install -r .\requirements-hosting.txt instead.

Inspect errors locally in .runtime/server.err.log and .runtime/tunnel.err.log. Do not publish those logs or private configuration.

## Connect a custom domain later

No domain or authenticated Cloudflare account was supplied, so the active setup uses a temporary quick tunnel.

1. Add a domain you own to Cloudflare and complete its nameserver setup.
2. In PowerShell, authenticate and create a named tunnel:

~~~powershell
cloudflared tunnel login
cloudflared tunnel create lsvindustry
~~~

3. Write a configuration file at C:\Users\CPComputer\.cloudflared\lsvindustry.yml, replacing the UUID and domain below:

~~~yaml
tunnel: YOUR-TUNNEL-UUID
credentials-file: C:/Users/CPComputer/.cloudflared/YOUR-TUNNEL-UUID.json
ingress:
  - hostname: lsvindustry.site
    service: http://127.0.0.1:5000
  - service: http_status:404
~~~

4. Create the hostname's DNS route, then start that named tunnel:

~~~powershell
cloudflared tunnel route dns lsvindustry lsvindustry.site
cloudflared tunnel --config "$env:USERPROFILE\.cloudflared\lsvindustry.yml" run lsvindustry
~~~

Keep the local server running. These example commands leave the named tunnel in that terminal; keep it open. The existing start script starts the temporary tunnel too. Once the custom hostname works, replace the quick-tunnel launch with the named-tunnel command or configure the named tunnel as a Windows service. A tunnel service alone does not start Flask.

Keep Cloudflare's certificate and tunnel credential JSON outside the project and private. Do not point your custom domain at the temporary trycloudflare hostname.

Cloudflare references:
- [Quick tunnel behavior and limits](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
- [Create a named tunnel and DNS route](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/create-local-tunnel/)
- [Windows service setup](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/as-a-service/windows/)

## Verification performed

- All four existing application smoke tests passed using their in-memory test database.
- Localhost, the PC's LAN address, and the public HTTPS homepage returned HTTP 200.
- Store, product, registration, login, and admin login pages worked.
- All 53 local assets referenced by the homepage and shop were fetched successfully locally and publicly.
- Khmer Unicode, CSRF-protected language switching, and sessions worked over local HTTP and public HTTPS.
- Public session cookies had Secure set.
- Protected account and admin routes redirected unauthenticated visitors to login.
- Twelve private/debug URL probes returned 404 locally and publicly.
- The existing database SHA256 was identical before and after setup.
- The firewall rule was confirmed enabled for Private / LocalSubnet / TCP 5000.
- Both server and tunnel remained running after their launching PowerShell commands exited.

Browser automation was unavailable in this session; verification used HTTP requests and the existing application tests.

## Branding and named-tunnel migration status

Requested permanent public URL: https://lsvindustry.site (not configured or live yet).
Requested named tunnel: lsvindustry.
Local origin: http://127.0.0.1:5000.

Both storefront and admin base templates now contain the exact title element <title>LSVIndustry</title>. Public page title and Khmer checks passed. The database checksum is unchanged.

At the latest setup attempt, public DNS returned NXDOMAIN for lsvindustry.site, and the official registry RDAP lookup returned HTTP 404 (no domain record found). Cloudflare browser authorization is also pending; no cert.pem is present. Domain registration/activation and Cloudflare authorization are required before DNS, the named tunnel, and its Windows service can be completed. None of those changes have been claimed or activated.

The existing Quick Tunnel remains running. Complete registration of a domain you control, add it to Cloudflare and activate the assigned nameservers, then finish cloudflared tunnel login in the browser. Never share account passwords or tunnel credentials in chat.

Start the currently working setup:

~~~powershell
Set-Location 'C:\Word\weblsv'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-LSVIndustry.ps1
~~~

Start only the local website when a named tunnel is managed separately:

~~~powershell
Set-Location 'C:\Word\weblsv'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-LSVIndustry.ps1 -LocalOnly
~~~

After a named-tunnel Windows service has actually been installed, it can be restarted in Administrator PowerShell with Restart-Service cloudflared. That service is not installed yet.