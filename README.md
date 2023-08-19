# s33 arp replier
## Workaround for accessing the Arris S33 management page.
I've seen a number of posts around the internet regarding difficulties accessing the S33's management page. I also faced this issue and discovered a workaround for my particular use-case.

For context, this is my setup:
```
          [Linux box - 192.168.0.1] 

             |                 | 

 [eth0 - 192.168.0.0/24]  [eth2 - Connected to S33 ] 

             |                 | 

    [ Internal LAN ]       [ The internet ]
```
So basically the Linux box is the router for my home network, and also the gateway to the internet via the S33. After adding a static route to `192.168.100.1` out `eth2`, I was able to ping the Arris, but trying to curl the modem on port 80 or 443 would just timeout (no response whatsoever). nmap to `192.168.100.1` showed:
```
PORT    STATE    SERVICE
80/tcp  filtered http
443/tcp filtered https
```
After running a tshark on `eth2`, what I found was that in response to my curl request, Arris was sending the following (I've altered my actual mac and public ip):
```
Broadcom_aa:bb:cc → Broadcast    ARP 60 Who has 3.1.23.96? Tell 192.168.0.1
```
Hrm... well, that's interesting. I contact the Arris on one address (`192.168.100.1`), but the subsequent arp request comes from a _different_ address (`192.168.0.1`). (3.1.23.96 is the public ip on eth2 in this example).

So basically in addition to `192.168.100.1`, the Arris is apparently setup to also assume it owns and controls `192.168.0.1`. When contacted on `192.168.100.1` over tcp, it starts using `192.168.0.1` to fulfill its arp requests, which is totally unexpected and imho buggy.

In my setup, this is obviously never going to work, as I've assigned `192.168.0.1` to my Linux box. So when the kernel receives some spurious arp request from its own address on one of its interfaces, I assume it just ignores it.

Then the question is what to do about it? I could probably reconfigure my internal LAN to use a different subnet and/or addresses, but I'm not going through all that hassle for this modem. So instead I just wrote a bit of python to listen for this very specific arp request from the s33. Once received, I construct the arp reply packet manually and stick it on the wire (basically doing what the kernel would do under normal circumstances). From that point forward communication works properly.

Your mileage may vary with this hack, and ability to use it will very much depend on your specific setup / environment.
