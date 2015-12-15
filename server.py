#!/usr/bin/python3

from __future__ import print_function
import os
import sys

from IPython.kernel.inprocess import InProcessKernelManager
from IPython.core.interactiveshell import InteractiveShell

import asyncio
import logging

from slixmpp import ClientXMPP

#ipython

def print_process_id():
        print('Process ID is:', os.getpid())

def init_ipython_shell():
    print_process_id()

    # Create an in-process kernel
    # >>> print_process_id()
    # will print the same process ID as the main process
    kernel_manager = InProcessKernelManager()
    kernel_manager.start_kernel()
    kernel = kernel_manager.kernel
    #kernel.gui = 'qt4'
    #kernel.shell.push({'foo': 43, 'print_pid': print_process_id})

    shell = InteractiveShell(manager=kernel_manager)
    return shell


#xmpp
class EchoBot(ClientXMPP):

    def __init__(self, jid, password, shell):
        ClientXMPP.__init__(self, jid, password)

        self.shell = shell
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

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
        if msg['type'] in ('chat', 'normal'):
            print(str(msg['body']))
            res = self.shell.run_cell(msg['body'])
            if res.success:
                msg.reply(str(res.result)).send()
            else:
                msg.reply("Fail:" + str(res.result)).send()


if __name__ == '__main__':
    # Ideally use optparse or argparse to get JID,
    # password, and log level.

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    shell = init_ipython_shell()

    xmpp = EchoBot(sys.argv[1], sys.argv[2], shell)
    xmpp.connect()
    xmpp.process()
