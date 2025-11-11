$TTL 3600

didi-thesysadmin.com. IN SOA dns01.didi-thesysadmin.com. domain-admin.didi-thesysadmin.com. (
                        2025110601      ; YYYYMMDDVV Serial
                        10800           ; Refresh
                        3600            ; Retry
                        3600         ; Expire
                        86400 )         ; Minimum TTL

; DNS Servers
@				                IN NS		dns01.didi-thesysadmin.com.
dns01				            IN A		192.168.20.12
app				                IN CNAME	dualstack.webbalancer-1382782522.ap-southeast-1.elb.amazonaws.com.
@				                IN MX 10	mail.didi-thesysadmin.com.

;@                              IN  CNAME   dualstack.webbalancer-1382782522.ap-southeast-1.elb.amazonaws.com.

_dmarc.didi-thesysadmin.com.	IN TXT		"v=DMARC1; p=quarantine; pct=50; sp=none; fo=0; rua=mailto:postmaster@didi-thesysadmin.com."
@                               IN TXT		"v=spf1 include:amazonses.com a mx ~all"
default._domainkey              IN TXT		( "v=DKIM1; h=sha256; k=rsa; "
                                            "p=MIIBHjANBgkqhkiG9w0BAQEFAAOCAQsAMIIBBgKB/gCuAv+ei11CcFQDIinQFz/FcW30nlCikmw3A0SLpo1I9av64RanhI/rqqnrx90w+KER+2FcGmUfSS3cRvDeZkKtwoswq1pxMhH875D2g2H9P/j+9JAr4GyFndmSQmKZp0i7vmUxyAR3E5XahasU+Z4jBX5uDdQngyO+XSu8HXefpVqa5nEEXTAC3zMZzL1Yf8GvxSo79D5oANVLTj"
                                            "/Vq4k1LWJx6w4uOCgeDDuqDhO16G29TKCNv9Iv6X3jdAU1aZ5mAbPs/31TAkjftwfV3q7bcryuhi7mdi22zPC6q/4uzSi7JtdxToDgYWLMqAijkeJeXoIdTd3d5LH1aOHXAgMBAAE=" )
;Generated : 2025-11-11 08:37:20 AM
@     IN A 54.169.21.121
@     IN A 54.169.181.246
@     IN A 18.142.135.163
