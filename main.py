#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS Checker and Updater Script (for BIND DNS Only)
--------------------------------------------------

Author:  Didi Li (https://didi-thesysadmin.com)
Contact: me@didi-thesysadmin.com
Created: 2025-11-11
Version: 1.0
License: MIT License (see LICENSE.md)

Description:
    This script automatically checks and updates A records for top-level domains (apex/naked),
    especially when a CNAME cannot be used due to RFC1912 restrictions.
    It resolves the target (e.g., AWS dualstack domain), compares IPs with current A records,
    regenerates the zone file using a template, validates it, and restarts the BIND DNS service.

Features:
    - Fetch current and external DNS A records
    - Compare and detect IP changes
    - Generate updated BIND zone files dynamically
    - Validate zone files using `named-checkzone`
    - Automatically restart BIND service if changes occur
    - Send email notifications about detected changes

Usage:
    $ python3 main.py

Configuration:
    Edit `config.ini` before running:
        [app]
        ext_dns = <Public DNS Server IP>
        int_dns = <Local Master DNS Server IP>
        top_domain = <Your top-level domain>
        dt_domain = <AWS dualstack domain>
        ...

Notes:
    - Always test this script in a staging environment before production.
    - Requires Python 3.x and the `dnspython` library.
    - Must run with sufficient privileges to modify zone files and restart BIND.

"""


import subprocess
import os
import datetime
import shutil
import smtplib
from email.mime.text import MIMEText
import os
import configparser
import dns.resolver
import dns.exception
import dns.name
import ipaddress

config_file = os.path.join(os.getcwd()+'/', 'config.ini')
print(config_file)
config = configparser.ConfigParser()
config.read(config_file)

# Configuration
ext_dns = config['app']['ext_dns']
int_dns = config['app']['int_dns']
top_domain = config['app']['top_domain']
dt_domain = config['app']['dt_domain']
prev_file = os.path.join(os.getcwd()+'/', config['app']['prev_file'])
current_file = os.path.join(os.getcwd()+'/', config['app']['current_file'])
template_zonefile = os.path.join(os.getcwd()+'/', config['app']['template_zonefile'])
generated_zonefile = os.path.join(os.getcwd()+'/', config['app']['generated_zonefile'])
binddns_zonefile = config['app']['binddns_zonefile']
named_checkzone_cmd = config['app']['named_checkzone_cmd']
systemctl_cmd = config['app']['systemctl_cmd']
email_to = config['app']['email_to']
email_from = config['app']['email_from']



def fetch_ips(domain, file_path, dns_server="8.8.8.8"):
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]

        answers = resolver.resolve(domain, 'A')  # Query A records
        ips = sorted([rdata.address for rdata in answers])

        print(ips)
        with open(file_path, 'w') as f:
            f.write("\n".join(ips))
    except dns.resolver.NoAnswer:
        print(f"No A records found for {domain}")
    except dns.exception.DNSException as e:
        print(f"Error fetching IPs for {domain}: {e}")


def fetch_current_serial_no(domain, dns_server='8.8.8.8'):
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]

        answers = resolver.resolve(domain, 'SOA')
        for rdata in answers:
            serial_number = str(rdata.serial)
            print(f"SOA Serial Number: {serial_number}")
            return serial_number

        print("SOA record not found.")
        return None
    except dns.resolver.NoAnswer:
        print(f"No SOA record found for {domain}")
        return None
    except dns.exception.DNSException as e:
        print(f"Error fetching SOA record: {e}")
        return None

def generate_serial_number(base_serial=None):
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    if not base_serial or len(base_serial) < 10:
        return f"{current_date}01"
    base_date = base_serial[:8]
    base_increment = int(base_serial[8:])
    if base_date != current_date:
        return f"{current_date}01"
    else:
        new_increment = str(base_increment + 1).zfill(2)
        return f"{current_date}{new_increment}"

def send_email(subject, body, from_addr, to_addr):
    # Configure SMTP server accordingly
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    try:
        # Example using localhost SMTP server
        with smtplib.SMTP('localhost') as server:
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    # Fetch previous IPs
    fetch_ips(top_domain, prev_file, int_dns)
    # Fetch current IPs
    fetch_ips(dt_domain, current_file, ext_dns)
    # Get current serial number
    soa_serial_number = fetch_current_serial_no(top_domain, int_dns)
    new_serial_number = generate_serial_number(soa_serial_number)
    print(f"New Serial No.: {new_serial_number}")

    # Check if previous file exists
    if os.path.exists(prev_file):
        subject = f"DNS IP Address Change Notification for {top_domain}"
        print("Checking for changes in IP addresses...")
        changed = False
        email_body = f"Changes detected for {top_domain}:\n\n"

        with open(prev_file) as f:
            prev_ips = set(line.strip() for line in f if line.strip())

        with open(current_file) as f:
            current_ips = set(line.strip() for line in f if line.strip())

        removed_ips = prev_ips - current_ips
        added_ips = current_ips - prev_ips

        if removed_ips:
            for ip in removed_ips:
                email_body += f"IP address {ip} has been removed.\n"
            changed = True

        if added_ips:
            for ip in added_ips:
                email_body += f"New IP address detected: {ip}\n"
            changed = True

        if changed:
            email_body += "\nPrevious IP addresses:\n" + "\n".join(prev_ips)
            email_body += "\n\nCurrent IP addresses:\n" + "\n".join(current_ips)

            # Update previous IPs file
            shutil.copy(current_file, prev_file)

            # Generate zone file content
            with open(template_zonefile) as f:
                zone_str = f.read()

            zone_str = zone_str.replace("SERIALNO", new_serial_number)

            is_ip_valid = True

            generated_lines = [f";Generated : {datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}"]
            for ip in current_ips:
                try:
                    # Validate IPv4 address
                    ip_obj = ipaddress.IPv4Address(ip)

                    generated_lines.append(f"@     IN A {ip}")
                    #generated_lines.append(f"login IN A {ip}")
                except ipaddress.AddressValueError:
                    print(f"Invalid IPv4 address skipped: {ip}")
                    is_ip_valid = False

            if is_ip_valid:
                zone_str += "\n" + "\n".join(generated_lines) + "\n"

                # Write generated zone file
                with open(generated_zonefile, 'w') as f:
                    f.write(zone_str)

                # Check zone validity
                try:
                    result = subprocess.run(
                        [named_checkzone_cmd, top_domain, generated_zonefile],
                        capture_output=True,
                        text=True
                    )
                    if "OK" in result.stdout:
                        email_body += "\n\n Zone File Valid.\n\nReplace {} with latest generated!\n".format(binddns_zonefile)
                        shutil.copy(generated_zonefile, binddns_zonefile)
                        # Restart bind service
                        subprocess.run([systemctl_cmd, "restart", "named.service"])
                        email_body += "Done!\n"
                    else:
                        email_body += "\nInvalid zone file.\n"
                except Exception as e:
                    email_body += f"Error checking zone: {e}\n"

            else:
                email_body = f"The script was trying to change the IP in the zone file; however, an error occurred. Please check!"
                subject = "ERROR - " + subject
                # Send email
            send_email(subject, email_body, email_from, email_to)
            print(email_body)
        else:
            print("No change in IP addresses.")
    else:
        print("Previous IP addresses file does not exist. Creating it.")
        shutil.copy(current_file, prev_file)
        print("Current IP addresses:\n" + open(current_file).read())

if __name__ == "__main__":
    main()
