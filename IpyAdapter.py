import logging
import signal
from queue import Empty

from traitlets import (
    Dict, Any
)
from traitlets.config import catch_config_error
from IPython.utils.warn import error

from jupyter_core.application import JupyterApp, base_aliases, base_flags, NoStart
from jupyter_client.consoleapp import (
        JupyterConsoleApp, app_aliases, app_flags,
    )

from jupyter_console.interactiveshell import ZMQTerminalInteractiveShell
from jupyter_console import __version__

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

_examples = """
jupyter console # start the ZMQ-based console
jupyter console --existing # connect to an existing ipython session
"""

#-----------------------------------------------------------------------------
# Flags and Aliases
#-----------------------------------------------------------------------------

# copy flags from mixin:
flags = dict(base_flags)
# start with mixin frontend flags:
frontend_flags = dict(app_flags)
# update full dict with frontend flags:
flags.update(frontend_flags)

# copy flags from mixin
aliases = dict(base_aliases)
# start with mixin frontend flags
frontend_aliases = dict(app_aliases)
# load updated frontend flags into full dict
aliases.update(frontend_aliases)
aliases['colors'] = 'InteractiveShell.colors'

# get flags&aliases into sets, and remove a couple that
# shouldn't be scrubbed from backend flags:
frontend_aliases = set(frontend_aliases.keys())
frontend_flags = set(frontend_flags.keys())


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class ZMQTerminalIPythonApp(JupyterApp, JupyterConsoleApp):
    name = "jupyter-console"
    version = __version__
    """Start a terminal frontend to the IPython zmq kernel."""

    description = """
        The Jupyter terminal-based Console.
        This launches a Console application inside a terminal.
        The Console supports various extra features beyond the traditional
        single-process Terminal IPython shell, such as connecting to an
        existing ipython session, via:
            jupyter console --existing
        where the previous session could have been created by another ipython
        console, an ipython qtconsole, or by opening an ipython notebook.
    """
    examples = _examples

    classes = [ZMQTerminalInteractiveShell] + JupyterConsoleApp.classes
    flags = Dict(flags)
    aliases = Dict(aliases)
    frontend_aliases = Any(frontend_aliases)
    frontend_flags = Any(frontend_flags)
    
    subcommands = Dict()
    
    force_interact = True

    def parse_command_line(self, argv=None):
        super(ZMQTerminalIPythonApp, self).parse_command_line(argv)
        self.build_kernel_argv(self.extra_args)

    def init_shell(self):
        JupyterConsoleApp.initialize(self)
        # relay sigint to kernel
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.shell = ZMQTerminalInteractiveShell.instance(parent=self,
                        display_banner=False,
                        manager=self.kernel_manager,
                        client=self.kernel_client,
        )
        self.shell.own_kernel = not self.existing

    def init_gui_pylab(self):
        # no-op, because we don't want to import matplotlib in the frontend.
        pass

    def handle_sigint(self, *args):
        if self.shell._executing:
            if self.kernel_manager:
                self.kernel_manager.interrupt_kernel()
            else:
                self.shell.write_err('\n')
                error("Cannot interrupt kernels we didn't start.\n")
        else:
            # raise the KeyboardInterrupt if we aren't waiting for execution,
            # so that the interact loop advances, and prompt is redrawn, etc.
            raise KeyboardInterrupt

    @catch_config_error
    def initialize(self, argv=None):
        """Do actions after construct, but before starting the app."""
        super(ZMQTerminalIPythonApp, self).initialize(argv)
        if self._dispatching:
            return
        # create the shell
        self.init_shell()
        # and draw the banner
        self.init_banner()

    def init_banner(self):
        """optionally display the banner"""
        self.shell.show_banner()
        # Make sure there is a space below the banner.
        if self.log_level <= logging.INFO: print()
    
    def start(self):
        # JupyterApp.start dispatches on NoStart
        super(ZMQTerminalIPythonApp, self).start()
        self.log.debug("Starting the jupyter console mainloop...")
        #self.shell.mainloop()

    def run(self, cmd, callback):
        #TODO: read the jupyter_console.interactiveshell.ZMQTerminalInteractiveShell.interactive
        #      avoid use such closure
        def fun(self, msg_id=''):
            """Process messages on the IOPub channel
               This method consumes and processes messages on the IOPub channel,
               such as stdout, stderr, execute_result and status.
               It only displays output that is caused by this session.
            """
            while self.client.iopub_channel.msg_ready():
                sub_msg = self.client.iopub_channel.get_msg()
                msg_type = sub_msg['header']['msg_type']
                parent = sub_msg["parent_header"]

                if self.include_output(sub_msg):
                    if msg_type == 'status':
                        self._execution_state = sub_msg["content"]["execution_state"]
                    elif msg_type == 'stream':
                        callback(sub_msg["content"]["text"])
                    elif msg_type == 'execute_result':
                        sendback_multimedia(sub_msg["content"]["data"], callback)
                    elif msg_type == 'error':
                        callback('Err')
                        for frame in sub_msg["content"]["traceback"]:
                            #print(frame)
                            callback(str(frame))



        self.shell.__class__.handle_iopub = fun
        if not self.shell.wait_for_kernel(self.shell.kernel_timeout):
            print('kernel error')
        self.shell.run_cell(cmd)

def sendback_multimedia(msg, callback):
        for type in msg:
            if type == 'text/plain':
                callback('Out:'+msg[type])
            else:
                callback('Out:'+str(msg))




def init_ipy():
    ins = ZMQTerminalIPythonApp.instance()
    ins.initialize()
    ins.start()
    return ins
