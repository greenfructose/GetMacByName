import os
import ipaddress

from netmiko import ConnectHandler
from secret import HP_USERNAME, HP_PASSWORD, IP_RANGE
from halo import Halo


def get_connection(ip):
    connection = ConnectHandler(ip=ip,
                                device_type='hp_procurve',
                                username=HP_USERNAME,
                                password=HP_PASSWORD)
    return connection


def ping_from_switch(switch_ip, ip_list):
    spinner = Halo(spinner='dots')
    spinner.start(f'Connecting to {switch_ip}')
    connection = get_connection(switch_ip)
    spinner.succeed()
    spinner.stop()
    for ip in ip_list:
        spinner.start(f'Pinging {ip}')
        connection.send_command(f'ping {ip}')
        spinner.succeed()
        spinner.stop()
    connection.disconnect()


def generate_ip_list(range):
    return [str(ip) for ip in ipaddress.IPv4Network(range)]


def show_switch(ip, items):
    """
    Cycles through a list of 'show' commands to run on a switch
    :param ip: Address of switch as String
    :param items: Text that follows 'show' in desired command as String
    :return: None
    """
    spinner = Halo(spinner='dots')
    spinner.start(f'Connecting to {ip}')
    connection = get_connection(ip)
    spinner.succeed()
    spinner.stop()
    for item in items:
        spinner.start(f'Getting {item}. This might take a bit.')
        startup_config = connection.send_command(f'show {item}')
        spinner.succeed()
        spinner.stop()
        item = item.replace(' ', '_').replace('-', '_')
        spinner.start(f'Writing {item} to switch_{item}/{ip}')
        if not os.path.exists(f'switch_{item}'):
            os.mkdir(f'switch_{item}')
        with open(f'switch_{item}/{ip}', 'w+') as f:
            f.write(startup_config)
        spinner.succeed(f'Command "show {item}" on {ip} completed and written to switch_{item}/{ip}')
        spinner.stop()
    spinner.start(f'Closing connection to {ip}')
    connection.disconnect()
    spinner.succeed()
    spinner.stop()

