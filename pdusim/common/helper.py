# This script contains useful functions
import sys
import os
import socket
import subprocess
from . import logger

install_data_dir = [
    os.path.join(os.environ['HOME'], '.pdusim'),
    os.path.join(sys.prefix, 'pdusim'),
    os.path.join(sys.prefix, 'share', 'pdusim'),
    os.path.join(os.path.split(__file__)[0], 'pdusim'),
    os.path.dirname(os.path.abspath(__file__))
]


def run_command(cmd="", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    """
    :param cmd: the command should run
    :param shell: if the type of cmd is string, shell should be set as True, otherwise, False
    :param stdout: reference subprocess module
    :param stderr: reference subprocess module
    :return: tuple (return code, output)
    """
    child = subprocess.Popen(cmd, shell=shell, stdout=stdout, stderr=stderr)
    cmd_result = child.communicate()
    cmd_return_code = child.returncode
    if cmd_return_code != 0:
        result = ""
        if cmd_result[1] is not None:
            result = cmd + ":" + cmd_result[1]
        else:
            result = cmd
        logger.error(result)
        raise Exception(result, cmd_result[0])
    return 0, cmd_result[0]


def get_install_dir():
    configdir_found = False
    for dir in install_data_dir:
        path = os.path.join(dir, 'conf', 'host.conf')
        if os.path.exists(path):
            return dir
    if not configdir_found:
        return None


def add_third_party_to_path():
    for dir in install_data_dir:
        path = os.path.join(dir, 'third-party')
        if os.path.exists(path):
            for d in os.listdir(path):
                sys.path.insert(0, os.path.join(path, d))


def get_pid_from_pid_file(file):
    with open(file, "r+") as f:
        pid = f.readline().strip()
    return pid


def check_if_port_in_use(address, port):
    """
    True if port in use, false if not in use
    """
    s = socket.socket()
    try:
        s.connect((address, port))
        s.close()
        return True
    except socket.error:
        s.close()
        return False