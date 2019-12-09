# pathmon
Pathmon is an IP Hop /AS Path monitoring tool

## Why? How?

More on this on my blog: http://easyipv6.wordpress.com/2019/12/09/python3-routing-path-monitoring-tool/

# what it basically does

Remember the goal is to have access to AS Path, RTT, Loss historical data afterwards & be able to be alerted about them in realtime, if necessary.

So my script would look like this, executed all XX minutes by a cronjob:

Read a list of IP destinations to trace too

- For each IP 
  - Use MTR to generate an output
  - Parse the output
  - Store the formated data in a file with timestamp
  - Parse the formated data & generate an SVG
  - Store the SVG with timestamp
  - Check if the last trace before changed in some way (RTT >, Loss, AS Path)
  - If yes generate E-Mail Alert with details & links to the data (Apache2 serving the file listing)
  
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
