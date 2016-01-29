#!/usr/bin/python3

from __future__ import print_function
import os
import sys
import re

import asyncio
import logging
from functools import partial

from slixmpp import ClientXMPP
from IpyAdapter import init_ipy

#xmpp
class EchoBot(ClientXMPP):

    def __init__(self, jid, password, shell):
        ClientXMPP.__init__(self, jid, password)

        self.shell = shell
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("disconnected", self.disconnected)

        # If you wanted more functionality, here's how to register plugins:
        # self.register_plugin('xep_0030') # Service Discovery
        # self.register_plugin('xep_0199') # XMPP Ping

        # Here's how to access plugins once you've registered them:
        # self['xep_0030'].add_feature('echo_demo')

    def session_start(self, event):
        self.send_presence()
        self.get_roster()

        # Most get_*/set_* methods from plugins use Iq stanzas, which
        # are sent asynchronously. You can almost always provide a
        # callback that will be executed when the reply is received.

    def message(self, msg):
        def ipy_send_callback(m):
            # remove color character from shell
            self.send_message(mto=msg['from'].bare,mbody=re.sub(r'\x1b\[\d*(;\d+)?m','',str(m)),mtype='chat')

        if msg['type'] in ('chat', 'normal'):
            print(str(msg['body']))
            #self.shell.run(msg['body'],partial(self.send_message, mto=msg['from'].bare))
            self.shell.run(msg['body'],ipy_send_callback)

    def disconnected(self, event):
        print('disconnected')
        self.connect()



if __name__ == '__main__':
    # Ideally use optparse or argparse to get JID,
    # password, and log level.

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    shell = init_ipy()

    xmpp = EchoBot(sys.argv[1], sys.argv[2], shell)
    xmpp.connect()
    xmpp.process()
