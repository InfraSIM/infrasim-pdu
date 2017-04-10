import os
import sys
import signal
import sys
import time
from . import logger
import pdusim
from common import config, helper
from common.daemon import daemonize
from vpduhandler import vPDUHandler


SIG_KILL = 9
pdu_sim = None


def init_signal():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def signal_handler(signum, frame):
    global pdu_sim
    logger.info("Signal {0} received.".format(signum))
    if pdu_sim is not None and pdu_sim.is_alive():
        pdu_sim.stop()
    logger.info("vPDU exit.")
    sys.exit(0)


def start(no_daemon=None):
    if status():
        raise Exception("[ {:<6} ] is already running".format(
            helper.get_pid_from_pid_file(config.server_pid_file)))
    precheck()
    global pdu_sim
    if no_daemon:
        logger.initialize("pdusim", "stdout")
        if not os.path.exists(os.path.dirname(config.server_pid_file)):
            os.mkdir(os.path.dirname(config.server_pid_file))
        with open(config.server_pid_file, "w+") as f:
            f.write("{}\n".format(os.getpid()))
    else:
        daemonize(config.server_pid_file, stdout="/dev/stdout")

    logger.info("vPDU started")
    print "[ {:<6} ] starts to run".format(helper.get_pid_from_pid_file(config.server_pid_file))
    # daemonized, redirect stdout to /dev/null
    if not no_daemon:
        of = file("/dev/null", "a+")
        os.dup2(of.fileno(), sys.stdout.fileno())

    init_signal()
    pdu_sim = pdusim.PDUSim()
    pdu_sim.set_daemon()
    pdu_sim.start()

    logger.info("PDU service PID: {}".format(pdu_sim.pid))
    logger.info("Server started")
    server = vPDUHandler(pdu_sim)
    server.serve_forever()


def precheck():
    port_num = 20022
    if helper.check_if_port_in_use("127.0.0.1", port_num):
        raise Exception("{} is already in use".format(port_num))


def stop():
    if not os.path.exists(config.server_pid_file):
        logger.info("PDU service is not running")
        print "[ {:<6} ] is stopped.".format("")
        return
    pid = helper.get_pid_from_pid_file(config.server_pid_file)
    os.kill(int(pid), signal.SIGTERM)
    print "[ {:<6} ] stop".format(pid)
    time.sleep(1)
    if os.path.exists("/proc/{}".format(pid)):
        os.kill(int(pid), SIG_KILL)
    logger.info("PDU service stopped.")


def status(stdout=False):
    pid = None
    if os.path.exists(config.server_pid_file):
        with open(config.server_pid_file, "r") as f:
            pid = f.readline().strip()
        if not os.path.exists("/proc/{}".format(pid)):
            pid = None
            os.remove(config.server_pid_file)
    if stdout:
        if pid:
            print "[ {:<6} ] is running".format(pid)
        else:
            print "[ {:<6} ] is stopped".format(" ")
    return pid


def restart():
    stop()
    start()





