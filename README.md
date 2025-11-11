# DNS Checker and Updater Script (for BIND DNS Only)

[![Python](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)]()
[![BIND](https://img.shields.io/badge/BIND9-Compatible-orange.svg)]()

---

## Description

This script resolves top-level (apex/naked) domains that use a CNAME pointing to another domain, such as AWS dualstack hosts.  
In BIND DNS, it’s **not allowed** to configure a CNAME record for a top-level domain due to [RFC1912 section 2.4](https://datatracker.ietf.org/doc/html/rfc1912#section-2.4):  
> “A CNAME record is not allowed to coexist with any other data.”

Use this script as a **temporary workaround** while implementing a permanent solution — for example, migrating the CNAME to a subdomain.

### What the script does
- Retrieves the IP addresses of external domains that your apex domain should resolve to  
- Compares them with your existing A records for the top-level domain  
- Regenerates a new zone file by merging the updated A records with the zone template  
- Validates the generated zone file  
- Restarts the BIND DNS service automatically

---

## ⚠️ Important Warning
This script **modifies DNS zone files directly**. Incorrect configuration may result in:
- DNS resolution failures  
- Service downtime  
- DNS propagation issues  

Always:
- Test in a **staging environment** first  
- Maintain proper **zone backups**  
- Run this script only on the **Master DNS server**

**This script is not for you if your CNAME points to a fixed IP address.**
---

## Requirements
- Python 3.x  
- `python3-dnspython`

---

## Installation

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-dnspython
```

### Using pip
```bash
pip3 install dnspython
```

---

## Configuration

Edit the `config.ini` file with your environment settings:

```ini
[app]
ext_dns = <Public DNS Server IP>
int_dns = <Local Master DNS Server IP>
top_domain = <Your top-level domain>
dt_domain = <AWS dualstack domain>
prev_file = previous_ips.txt
current_file = current_ips.txt
template_zonefile = <Zone template file>
generated_zonefile = <Generated zone file name>
binddns_zonefile = /path/to/your/zone/<BIND zone file>
named_checkzone_cmd = /usr/bin/named-checkzone
systemctl_cmd = /usr/bin/systemctl
email_to = <Your email address>
email_from = dnscheck@dns01.didi-thesysadmin.com
```

### Configuration Notes
- Replace all `<...>` placeholders with actual values  
- Ensure `binddns_zonefile` points to your correct BIND zone file path  
- Verify paths for `named_checkzone_cmd` and `systemctl_cmd` are valid on your system  
- Use valid email addresses for notifications  

---

## Usage

Run manually:
```bash
python3 main.py
```

### Automated Execution (Recommended)
Add to crontab for periodic checks (example: every 5 minutes):
```bash
*/5 * * * * /usr/bin/python3 /path/to/your/script/main.py
```

---

## Example Output

```text
[2025-11-11 09:30:12] Checking DNS for domain: didi-thesysadmin.com
[2025-11-11 09:30:13] External DNS IPs: 54.123.45.67, 3.14.159.26
[2025-11-11 09:30:13] Current zone file IPs: 54.123.45.67
[2025-11-11 09:30:13] Detected changes. Regenerating zone file...
[2025-11-11 09:30:14] Zone file validation passed.
[2025-11-11 09:30:15] Restarting BIND service...
[2025-11-11 09:30:16] BIND restarted successfully.
```

---

## Best Practices
- Test thoroughly in a **staging environment** before deploying to production  
- Always **backup** your zone files before modification  
- Monitor both **script output** and **DNS resolution** after implementation  
- Ensure the script has permission to **read/write zone files** and **restart BIND**  
- Remember to update the Zone Template file after modifying a record in the BIND DNS zone file.

---

## Troubleshooting
- Verify file permissions for zone and template files  
- Ensure the script user can restart the BIND service  
- Check system logs for any DNS-related errors  
- Confirm email notifications are configured and functioning  

---

## License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Author & Contact
Maintained by **Didi Li**  
🌐 [https://didi-thesysadmin.com](https://didi-thesysadmin.com)  
📧 me@didi-thesysadmin.com