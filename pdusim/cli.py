import argparse
import sys
import main
import password
from common import config, helper
from common.network import NetworkUtils

conf = config.Config(helper.get_install_dir())
config.set_conf_instance(conf)


def args(*args, **kwargs):
    def _decorator(func):
        func.__dict__.setdefault('args', []).insert(0, (args, kwargs))
        return func
    return _decorator


def methods_of(obj):
    result = []
    for i in dir(obj):
        if callable(getattr(obj, i)) and not i.startswith('_'):
            result.append((i, getattr(obj, i)))
    return result


def get_arg_string(args):
    args = args.strip('-')

    if args:
        args = args.replace('-', '_')

    return args


def get_func_args(func, matchargs):
    fn_args = []
    for args, kwargs in getattr(func, 'args', []):
        # The for loop is for supporting short and long options
        for arg in args:
            try:
                arg = kwargs.get('dest') or get_arg_string(args[0])
                parm = getattr(matchargs, arg)
            except AttributeError:
                continue

            fn_args.append(parm)

            # If we already got one params for fn, then exit loop.
            if len(fn_args) > 0:
                break

    return fn_args


class ConfigCommands(object):
    keys = ["pdutype", "dbtype", "dbfile", "snmpdata"]

    @args("key", help="Specify what property of vpdu you want to set.\n Available options: {pdutype, dbtype, dbfile, snmpdata}")
    @args("val", help="Specify the value you want to set for the property")
    def set(self, key, val, conf=conf, keys=keys):
        if key not in keys:
            raise KeyError("Your option {} is not available.".format(key))
        if key == "pdutype":
            conf.pdu_name = val
        elif key == "dbtype":
            conf.db_type = val
        elif key == "dbfile":
            conf.db_file = val
        elif key == "snmpdata":
            conf.snmp_data_dir = val

        conf.update()
        print "{} is set to {}".format(key, val)

    @args("key", help="Specify what property of vpdu you want to set.\n Available options: {pdutype, dbtype, dbfile, snmpdata}")
    def get(self, key, conf=conf, keys=keys):
        if key not in keys:
            raise KeyError("Your option {} is not available.".format(key))
        if key == "pdutype":
            print conf.pdu_name
        elif key == "dbtype":
            print conf.db_type
        elif key == "dbfile":
            print conf.db_file
        elif key == "snmpdata":
            print conf.snmp_data_dir

    def list(self, conf=conf):
        print conf.list()


class MapCommands(object):

    def set(self):
        pass


class IPCommands(object):
    @args("dev", help="Specify the network device you want to set")
    @args("ipaddr", help="Specify the ip address you want to set")
    @args("netmask", nargs="?", default=None, help="Specify the netmask you want to set")
    def set(self, dev, ipaddr, netmask):
        NetworkUtils.set_ip_address(dev, ipaddr)
        if netmask:
            int_netmask = NetworkUtils.convert_ip_to_int(netmask)
            NetworkUtils.set_netmask(dev, NetworkUtils.get_mask(int_netmask))
        status = NetworkUtils.link_status(dev)
        if not status:
            NetworkUtils.link_up(dev)

    @args("dev", help="Specify the network device you want to set")
    def get(self, dev):
        if dev not in NetworkUtils.get_net_interfaces():
            raise Exception("{} not exists!".format(dev))
        ip_address = NetworkUtils.get_ip_address(dev) or "0.0.0.0"
        netmask = NetworkUtils.get_netmask(dev)
        if netmask:
            netmask = NetworkUtils.convert_int_to_ip(NetworkUtils.get_netmask_int(netmask))

        print "ip address: {}, netmask: {}".format(
            ip_address, netmask)

    @args("key", help="Specify the action you want to take.\nAvailable options: {up, down, status}")
    @args("dev", nargs="?", default=None, help="Specify the network device")
    def link(self, key, dev):
        keys = ["up", "down", "status", "list"]
        ifname_list = NetworkUtils.get_net_interfaces()
        if key not in keys:
            raise KeyError("Your option {} is not available.".format(key))
        if key == "list":
            print "Available interfaces:\n{}".format(ifname_list)
            return
        if not dev:
            raise Exception(
                "Too few arguments.\nusage: infrasim pdu ip link [-h] {} [dev]".format(key))
        if dev not in ifname_list:
            raise Exception("{} not exists".format(dev))
        if key == "up":
            NetworkUtils.link_up(dev)
            print "{} is set up".format(dev)
        elif key == "down":
            NetworkUtils.link_down(dev)
            print "{} is brought down".format(dev)
        elif key == "status":
            ret = NetworkUtils.link_status(dev)
            if ret:
                print "{} is up".format(dev)
            else:
                print "{} is down".format(dev)


CATEGORIES = {
    'config': ConfigCommands,
    'map': MapCommands,
    'ip': IPCommands
}


def add_command_parsers(subparser):
    for category in CATEGORIES:
        command_object = CATEGORIES[category]()

        parser = subparser.add_parser(category)
        parser.set_defaults(command_object=command_object)

        category_subparsers = parser.add_subparsers(dest="action")

        for (action, action_fn) in methods_of(command_object):
            parser = category_subparsers.add_parser(action)

            action_kwargs = []
            for args, kwargs in getattr(action_fn, 'args', []):
                parser.add_argument(*args, **kwargs)
                parser.set_defaults(dest="dest")

            parser.set_defaults(action_fn=action_fn)
            parser.set_defaults(action_kwargs=action_kwargs)


def command_handler():
    try:
        parser = argparse.ArgumentParser()

        subparsers = parser.add_subparsers(title="VPDU Commands")
        add_command_parsers(subparsers)

        start_parser = subparsers.add_parser("start", help="Start VPDU service")
        start_parser.set_defaults(start="start")
        start_parser.add_argument("--no-daemon", action="store_true", help="Make process running foreground")

        stop_parser = subparsers.add_parser("stop", help="Stop VPDU service")
        stop_parser.set_defaults(stop="stop")

        restart_parser = subparsers.add_parser("restart", help="Restart VPDU service")
        restart_parser.set_defaults(restart="restart")

        status_parser = subparsers.add_parser("status", help="Show VPDU service status")
        status_parser.set_defaults(status="status")

        args = parser.parse_args(sys.argv[2:])

        if hasattr(args, "start"):
            main.start(args.no_daemon)

        elif hasattr(args, "stop"):
            main.stop()

        elif hasattr(args, "status"):
            main.status(True)

        elif hasattr(args, "restart"):
            main.restart()

        else:
            fn = args.action_fn
            fn_args = get_func_args(fn, args)
            # Handle the command
            fn(*fn_args)

    except Exception as e:
        print e.message





