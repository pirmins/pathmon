# pathmon
Pathmon is an IP Hop /AS Path monitoring tool

## Why?

When it comes to monitoring networks, it will probably sound familiar to you when I say you always miss a piece of information. There's always that tiny bit of data you'd like to know from point T in time because there is one thing network consumers don't get: you're not responsible for the whole internet. How many times did you exactly know your network was running fine, but had wished you knew (and had the data to prove it) what went possibly wrong with packets later on it's way to the destination?

Well, the other day a co-worker came with the idea of implementing such a tool, what he wanted to achieve was basically traceroutes with graphical representation, he then explained that Scapy could do that but doesn't integrate RTTs nor packetloss in the generated SVG.

## How?

I started reading myself into the Scapy github files, trying in vain to get the architecture but as a not pro-developper I found it actually a bit too complex for the use we would have, given that Scapy only allows for the the svg to generate, while we also needed the historical trace data to be stored, then some of this would have to be analyzed to detect changes/loss/RTT increase and will need to trigger some kind of alerting. That's how I decided to not loose anymore time and create it myself, so it would also perfectly fit our needs.

# pathmon.py

Remember the goal is to have access to AS Path, RTT, Loss historical data afterwards & be able to be alerted about them in realtime, if necessary.

So my script would look like this, executed all XX minutes by a cronjob:

Read a list of IP destinations to trace too

For each IP 
  Use MTR to generate an output
  
  Parse the output
  
  store the formated data in a file with timestamp
  
  Parse the formated data & generate an SVG
  
  Store the SVG with timestamp
  
  Check if the last trace before changed in some way (RTT >, Loss, AS Path)
  
  If yes generate E-Mail Alert with details & links to the data (Apache2 serving the file listing)
  
## Directory structure

The directory structure is automatically created during script execution.
  
  - config_file
  - pathmon.py
  - targets/
    - 172.16.10.254
      - trace/
        - last
        - "timestamp"
      - svg/
         - last.svg
         - timestamp".svg
                  
## Apache2 integration

Files will be listed by server "FQDN":8080/targets/IP/svg/DATA.svg or /targets/IP/trace/DATA.

A virtualhost apache2 file would look like this:

```
<VirtualHost *:8080>
  DocumentRoot /home/pathmon
  Servername server.domain.tld:8080
  <Directory /home/pathmon>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
  </Directory>
  ErrorLog ${APACHE_LOG_DIR}/error.log
  CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

## Output

A Packet loss detection E-Mail looks like this:
```
Last traceroute: 
AS65500 172.16.10.1 0.0% 0.5
AS65500 172.16.10.2 0.0% 9.9
AS??? 194.42.48.80 0.0% 0.4
AS6939 72.52.92.129 0.0% 0.5
AS6939 184.105.65.38 0.0% 17.9
AS6939 184.105.81.77 0.0% 85.9
AS6939 184.105.81.218 0.0% 145.1
AS6939 72.52.92.57 0.0% 158.3
AS6939 216.218.186.2 10.0% 146.0
Link to SVG: http://server.domain.tld:8080/targets/216.218.186.2/svg/06-12-2019_08-20-17_AM.svg

Trace before: 
AS65500 172.16.10.1 0.0% 0.3
AS65500 172.16.10.2 0.0% 0.6
AS??? 194.42.48.80 0.0% 0.3
AS6939 72.52.92.129 0.0% 0.4
AS6939 184.105.65.38 0.0% 29.7
AS6939 184.105.81.77 0.0% 85.9
AS6939 184.105.81.218 0.0% 145.1
AS6939 72.52.92.57 0.0% 150.1
AS6939 216.218.186.2 0.0% 145.7

Link to SVG: http://server.domain.tld:8080/targets/216.218.186.2/svg/last-06-12-2019_08-20-17_AM.svg
```
An SVG would then look like this for example:

![Alt text](https://i.ibb.co/9scHmGg/svg.png "sample svg")
