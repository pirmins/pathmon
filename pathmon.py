#!/usr/bin/env python

import subprocess
import argparse
import sys
import base64
import os
import ipaddress
import os
import socket
import smtplib
from graphviz import *
from datetime import datetime
from shutil import copyfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

#mail sending function
def send_mail(recipient, subject, body):
    s = smtplib.SMTP(host='smtp.domain.tld', port=25)
    s.starttls()
    s.login('email@domain.tld', 'passw0rd')
    msg = MIMEMultipart()
    message = body

    # setup the parameters of the message
    msg['From']='email@domain.tld'
    msg['To']=recipient
    msg['Subject']=subject

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # send the message via the server set up earlier.
    s.send_message(msg)
    del msg

    # Terminate the SMTP session and close the connection
    s.quit()

#launches mtr traceroute towards target and returns the command output
def exec_traceroute(target):
    cmt_output = ''
    # Depending on the router model there will be a different ansible job launched
    myCmd = "mtr -z -r -n -c 10 %s" % (target)
#       print(myCmd)
    cmd_output = subprocess.check_output([myCmd], shell=True)
    return cmd_output

#checks if a passed IP is a valid IP address
def is_valid_ip(line):
    try:
        ip = ipaddress.ip_address(line)
        print('%s is a correct IP%s address.' % (ip, ip.version))
        return True
    except:
        print('address/netmask is invalid: %s' % line)
        return False

#parses the mtr traceroute output, It's built for "mtr -z -r -n -c 10 %s"
def parse_trace():
    new = ''
    with open('temp', 'r') as raw:
        for line in raw:
            print(line)
            newline = ''
            if 'Start' in line or 'HOST' in line:
                print("skip this line")
            else:
                print(line)
                if ' ???' in line:
                    print("I see the ??? marks")
                    newline += ' ??? '+'\n'
                else:
                    print(line)
                    a, b, c, d, e, f, g, h, i, j = line.split()
                    newline += b+' '+c+' '+d+' '+f+'\n'
                new += newline
    return new

#gets the trace information from the last traceroute before the current one
def get_last_trace(tracepath):
    output = ''
    if os.path.exists(tracepath+'last'):
        f = open(tracepath+'last', 'r')
        output = f.read()
        f.close()
    else:
        print('no "last" file in directory '+tracepath+' maybe it s the first time the script is run to this target IP')
    return output

#generates an svg file based on current traceroute output
def generate_svg(tracepath, timestp, svgpath):
    # ceate a directed graph with name timestap in svg directory
    dot = Digraph(name='tempsvg')
    # create a list of graphes
    sgraphlist = []
    # set a couple options for svg styling
    dot.attr('node', fontsize='11')
    dot.attr('node', color='black')
    # make the graph vertically going
    dot.attr(rankdir='LR')
    # open the last traceroute file
    with open(tracepath+'last', 'r') as raw:
        # set previous as variable to ''
        prevas = ''
        # create a directed graph that will act as a subgraph to the dot graph
        s = Digraph(name='sgraph_0')
        s.attr(rank='same')
        # for each line in the traceroute
        for num, line in enumerate(raw, 1):
            # if as is unkown with no ping
            if " ??? " in line:
                # add the node to the actual subgraph
                s.node(str(num), "???")
                s.attr(rank='same')
            else:
                # if its a normal traceroute line, split into the single elements
                a, b, c, d = line.split()
                # if it's the same as as the previous hop one's
                if a == prevas:
                    # add a node to the actual subgraph
                    s.node(str(num), a+"\n"+b+"\n"+c+" loss\n"+d+"ms")
                    s.attr(rank='same')
                # else if it's another AS
                else:
                    # add the current subgraph to the graph list
                    sgraphlist.append(s)
                    # create a new directed subgraph and add the node to it
                    s = Digraph(name='sgraph_'+str(num))
                    s.node(str(num), a+"\n"+b+"\n"+c+" loss\n"+d+"ms")
                    s.attr(rank='same')
                # set the previous as to the current one
                prevas = a
            # if its not the first traceroute line, create the link between this node and the prior node
            if num > 1:
                dot.edge(str(num-1), str(num))

    # add the last subgraph to the main graph
    sgraphlist.append(s)

    # for every element in the graph list
    for t in sgraphlist:
        # set rank to the same level
        t.attr(rank='same')
        # add the subgraph to the main graph
        dot.subgraph(t)

    # set output format to 'svg'
    dot.format = 'svg'
    # generate the svg file
    dot.render(svgpath+'temp')

    # copy the rendered svg to the 'last.svg' file
    copyfile(svgpath+'temp.svg', svgpath+timestp+'.svg')

    # copy the rendered svg to the 'last.svg' file
    copyfile(svgpath+timestp+'.svg', svgpath+'last.svg')

#compares the current traceroute to the previous traceroute to detect discrepancies
def compare_to_last_trace(tracepath):
        #take first line of this trace and compare to the first line of last trace
        if os.path.exists(tracepath+'last'):
            if os.path.exists(tracepath+'lastlast'):
                aschg=False
                pktloss=False
                f1 = open(tracepath+'last', 'r')
                f2 = open(tracepath+'lastlast', 'r')
                this_trace = f1.readlines()
                last_trace = f2.readlines()
                for num, lineB in enumerate(last_trace, 0):
                    print('START SEQUENCE LOOP')
                    print(str(num)+'   '+lineB)
                    print(len(this_trace))
                    if len(this_trace)>=num:
                        print('current trace is still in range of last trace')
                        lineA = this_trace[num]
                        print(str(num)+'   '+lineA)
                        if " ??? " in lineB or " ??? " in lineA:
                            print('not known AS/IP for one of both')
                        else:
                            # if its a normal traceroute line, split into the single elements
                            a1, b1, c1, d1 = lineA.split()
                            a2, b2, c2, d2 = lineB.split()
                            c1 = c1.replace('%','')
                            c2 = c2.replace('%','')
                            c1 = float(c1)
                            c2 = float(c2)
                            if a1 != a2:
                                print('AS changed')
                                aschg=True
                            else:
                                print('still same AS')
                                if b1 == b2:
                                    print('still same hop IP')
                                else:
                                    print('but not same hop')
                            if c1 > 0:
                                print('anyway there is some packetloss on this hop')
                                if c2 > 0:
                                    print('...just like before')
                                    pktloss=True
                                else:
                                    print('there was none before')
                            else:
                                pktloss=False
                                if c2 > 0:
                                    print('no more packetloss compared to previous trace ')
                                else:
                                    print('there was no packetloss')
                    else:
                        print('current trace not in range of last trace')
                f1.close()
                f2.close()
            print('end of compare')
            return aschg, pktloss

def main(cfgfile):
        # read the config file
    with open(cfgfile, 'r') as f:
                # for each target in config file
        for line in f:
            # if the config line is a valid ip address (ipv4 or ipv6)
            target = line.strip()
            if is_valid_ip(target):
                # define tracepath variable
                tracepath = 'targets/'+target+'/trace/'
                svgpath = 'targets/'+target+'/svg/'

                # ensures directory structure exists or then creates it
                os.system('mkdir -p '+tracepath)
                os.system('mkdir -p '+svgpath)

                # executes a traceroute for the destination
                raw_output = ''
                raw_output = exec_traceroute(target)

                # write it temporary down
                temp = open('temp', 'wb')
                temp.write(raw_output)
                temp.close()

                # generate a simplified version of it
                this_trace = ''
                this_trace = parse_trace()

                # copy the rendered svg to the 'last.svg' file
                if os.path.exists(svgpath+'last.svg'):
                    copyfile(svgpath+'last.svg', svgpath+'lastlast.svg')


                # reads and returns the previous log trace
                last_trace = get_last_trace(tracepath)
                lastlast = open(tracepath+'lastlast', 'w+')
                lastlast.write(last_trace)
                lastlast.close()
                print(last_trace)
                print ("saving the previous last trace for further comparison")

                # overwrites the previous las with this trace
                last = open(tracepath+'last', 'w+')
                last.write(this_trace)
                last.close()
                print("writing down the new last file")

                # define timestp for homogenity in time stamp names along a sequence
                timestp = datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")

                # also write it into a "timestamp" file
                timestpfile = open(tracepath+timestp, 'w+')
                timestpfile.write(this_trace)
                timestpfile.close()
                print("writing down the new trace into its timestamp file")

                # generate svg
                generate_svg(tracepath, timestp, svgpath)
                print("SVG generated")

                # compare this trace to the previous last one
                print("comparing the two last traces to see if there is an issue")
                # checks for discrepencies > (only when it went up/loss/whatever)
                # if finds one, sends an alert with included svg and last two trace logs
                aschg, pktloss = compare_to_last_trace(tracepath)

                hostname = socket.gethostbyaddr(socket.gethostname())[0]
                port = ':8080'
                thissvg = hostname+port+'/'+svgpath+timestp+'.svg'
                lastsvg = hostname+port+'/'+svgpath+'last-'+timestp+'.svg'

                #action to take
                if aschg:
                    if os.path.exists(svgpath+'last.svg'):
                        copyfile(svgpath+'last.svg', svgpath+'last-'+timestp+'.svg')
                    print('the path changed, sending an alert per email...')
                    message = 'Last traceroute: \n'+this_trace +'Link to SVG: http://'+thissvg+'\n\nTrace before: \n'+last_trace+'\nLink to SVG: http://'+lastsvg
                    #create SMTP
                    send_mail('noc@domain.tld','From server '+hostname+' Path to '+target+' changed', message)
                if pktloss:
                    if os.path.exists(svgpath+'last.svg'):
                        copyfile(svgpath+'last.svg', svgpath+'last-'+timestp+'.svg')
                    print('There is some packet loss on the path, sending an alert per email...')
                    message = 'Last traceroute: \n'+this_trace +'Link to SVG: http://'+thissvg+'\n\nTrace before: \n'+last_trace+'\nLink to SVG: http://'+lastsvg
                    send_mail('noc@domain.tld','Packet loss detected on path to '+target,message)


# Parse the arguments
parser = argparse.ArgumentParser(
    description='executes traceroutes on targets, parses & logs them, creates an svg file then compares to the precedent trace to detect path changes, latency increases or packetlosses')
parser.add_argument('-c', '--config', required=True,help='List of traceroute targets (either IPv4s or FQDNs')
args = parser.parse_args()
# launch program Main()
main(args.config)
