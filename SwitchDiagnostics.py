import os
import csv
import ipaddress
from pprint import pprint

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


# if __name__ == '__main__':
#     arp_list = []
#     raw_arp_table = ''
#     with open('switch_arp/192.168.2.2', 'r') as f:
#         raw_arp_table = f.read()
#
#     fixed_arp_list = [x.strip() for x in raw_arp_table.split("\n")[6:-2]]
#     pprint(fixed_arp_list)
#     for item in fixed_arp_list:
#         item = item.replace('     ', ' ').replace('    ', ' ').replace('   ', ' ').replace('  ', ' ')
#         item = item.split(' ')
#         if len(item) > 3:
#             arp_list.append({
#                 'IP': item[0],
#                 'MAC': item[1],
#                 'Port': item[3]
#             })
#     pprint(arp_list)
#
#     with open('SwitchAddresses.csv', 'r') as f:
#         reader = csv.reader(f)
#         commands = ['arp']
#         ip_list = generate_ip_list(IP_RANGE)
#         for row in reader:
#             ping_from_switch(row[0], ip_list)
#             show_switch(row[0], commands)
