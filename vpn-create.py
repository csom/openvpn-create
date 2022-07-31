#!/usr/bin/env python3
##################### METADATA #####################
# NAME: csoM
# USERNAME: csom@mackapaer.se
# COURSE: 
# ASSIGNMENT: 
# DATE OF LAST CHANGE: 20220319
####################################################

import subprocess
import argparse
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def easyrsa(user):
    try:
        os.chdir("/etc/easy-rsa")
        subprocess.run(["/etc/easy-rsa/easyrsa", "build-client-full", "{}".format(user), "nopass"])
    except Exception as e:
        print(e)

def buildovpn(cfile, opath, user):
    
    try:
        confFile = open(cfile, "r")
        caFile = open("/etc/easy-rsa/pki/ca.crt", "r")
        taFile = open("/etc/easy-rsa/pki/ta.key", "r")
        cFile = open("/etc/easy-rsa/pki/issued/{}.crt".format(user), "r")
        kFile = open("/etc/easy-rsa/pki/private/{}.key".format(user), "r")
        ovpnFile = open("{}/{}.ovpn".format(opath, user), "w")
    
        ovpnFile.write(confFile.read())
    
        ovpnFile.write("\n\n<ca>\n")
        ovpnFile.write(caFile.read())
        ovpnFile.write("</ca>\n")

        ovpnFile.write("\n\n<cert>\n")
        ovpnFile.write(cFile.read())
        ovpnFile.write("</cert>\n")

        ovpnFile.write("\n\n<key>\n")
        ovpnFile.write(kFile.read())
        ovpnFile.write("</key>\n")

        ovpnFile.write("\n\n<tls-auth>\n")
        ovpnFile.write(taFile.read())
        ovpnFile.write("</tls-auth>\n")

        confFile.close()
        caFile.close()
        taFile.close()
        cFile.close()
        kFile.close()
        ovpnFile.close()

        print ("OVPN-file created for user: {} at: {}/{}.ovpn".format(user, opath, user))

    except:
        print ("No OVPN-file created...")

def mailfile(email, user, path):
    
    try:
        fromaddr = "vpn@example.se"
        toaddr = "{}".format(email)
        
        # instance of MIMEMultipart
        msg = MIMEMultipart()
        
        # storing the senders email address  
        msg['From'] = fromaddr
        
        # storing the receivers email address 
        msg['To'] = toaddr
        
        # storing the subject 
        msg['Subject'] = "VPN: vpn.example.se"
        
        # string to store the body of the mail
        body = "This is an automatic generated email containing the OpenVPN-file attatched to it of user: {}.ovpn\n\nPlease don't hesitate to reply to this email if something is wrong.\n\n\n/vpn.example.se".format(user)
        
        # attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))
        
        # open the file to be sent 
        filename = "{}/{}.ovpn".format(path, user)
        
        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')
        
        # To change the payload into encoded form
        with open(filename, "rt") as attachment:
            p.set_payload(attachment.read())
        
        # encode into base64
        encoders.encode_base64(p)
        
        p.add_header('Content-Disposition', "attachment; filename= {}.ovpn".format(user))
    
        # attach the instance 'p' to instance 'msg'
        msg.attach(p)
        
        # creates SMTP session
        s = smtplib.SMTP('localhost', 25)
        
        # start TLS for security
        s.starttls()
        
        # Authentication
        #s.login(fromaddr, "Password_of_the_sender")
    
        # Converts the Multipart msg into a string
        text = msg.as_string()
        
        # sending the mail
        s.sendmail(fromaddr, toaddr, text)
        
        # terminating the session
        s.quit()

        print ("Mail sent to {}".format(email))
    except Exception as e:
        print(e)

def run():
    """
    Parse args and call proper function
    """
    parser = argparse.ArgumentParser(description='Script to autogenerate OpenVPN '
                                                 'config alongside with certs. This script rely on that easy-rsa is configured in /etc/easy-rsa and that init-pki, build-ca and server certs are generated')
    parser.add_argument('-c', '--config', metavar='config-file', help='Path to config template [including] filename (the file containing the text before the certs (default: /etc/easy-rsa/pki/template.conf))',
                        default='/etc/easy-rsa/pki/template.conf')
    parser.add_argument('-o', '--output', metavar='output-path', help='(Path where to put the user.ovpn file, [without] trailing slash, [only directory] (default: /etc/easy-rsa/pki))',
                        default='/etc/easy-rsa/pki')
    parser.add_argument('-u', '--user', metavar='username', help='Username for certificate and config (the name of CN and ovpn-file)', required='true')
    parser.add_argument('-m', '--email', metavar='email-address', help='Email address of user to send the ovpn-file to')
    args = parser.parse_args()

    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting...")

    easyrsa(args.user)

    buildovpn(args.config, args.output, args.user)

    if (args.email):
        mailfile(args.email, args.user, args.output)
    
    


if __name__ == "__main__":
    run()
