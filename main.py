from __future__ import unicode_literals

import sys

from manage_switches.DoConcurrent import *
from manage_switches.DocFunctions import *
from manage_switches.NetworkFunctions import *
from manage_switches.SwitchFunctions import *

from secret import IP_RANGE, USERNAME, PASSWORD, DEVICE_TYPE


def write_arp_tables(ip: str):
    """
    Retrieves ARP table from switch. Writes remote device IP, remote device
    MAC, remote device hostname, switch ip, and switch port the remote
    device is connected too into a CSV file.
    :param ip: IP address of switch as string
    :return: Success string 'Success on {ip}'
    """
    spinner = Halo(spinner='dots')
    try:
        coninfo = {
            'ip': ip,
            'device_type': DEVICE_TYPE,
            'username': USERNAME,
            'password': PASSWORD
        }
        commands = ['show arp']
        run_commands(coninfo, commands)
        arp_list = []
        spinner.start(f'\nGetting ARP table from switch at {ip}')
        with open(f'switch_show_arp/{ip}', 'r') as f:
            raw_arp_table = f.read()
        spinner.succeed()
        spinner.stop()
        spinner.start(f'\nFormatting ARP table and writing to file.')
        fixed_arp_list = [x.strip() for x in raw_arp_table.split("\n")[6:-2]]
        for item in fixed_arp_list:
            item = item.replace('     ', ' ')\
                .replace('    ', ' ')\
                .replace('   ', ' ')\
                .replace('  ', ' ')
            item = item.split(' ')
            if len(item) > 3:
                arp_list.append({
                    'IP': item[0],
                    'MAC': reformat_mac(item[1]),
                    'Hostname': get_hostname_by_ip(item[0]),
                    'Switch IP': ip,
                    'Switch Port': item[3]
                })
        write_result_csv(arp_list, 'a+', prepend=ip)
        spinner.succeed(f'\nFile written to {ip}-arp_list.csv')
        spinner.stop()
        return f'Success on {ip}'
    except (KeyboardInterrupt, SystemExit):
        spinner.stop()


def populate_arp_table(ip: str):
    """
    Logs into switch, pings every address in IP_RANGE to populate ARP table
    :param ip: IP address of switch as string
    :return: Success string 'Success on {ip}'
    """
    try:
        coninfo = {
            'ip': ip,
            'device_type': DEVICE_TYPE,
            'username': USERNAME,
            'password': PASSWORD
        }
        ip_list = generate_ip_list(IP_RANGE)
        ping_from_switch(coninfo, ip_list)
        return f'Success on {ip}'
    except (KeyboardInterrupt, SystemExit):
        sys.exit()


if __name__ == '__main__':
    coninfo = {
        'ip': '',
        'device_type': DEVICE_TYPE,
        'username': USERNAME,
        'password': PASSWORD
    }
    switch_ips = []
    ping_ips = []
    ip_list = generate_ip_list(IP_RANGE)
    with open('PingSwitch.csv', 'r') as f:
        for row in csv.reader(f):
            ping_ips.append(row[0])
    with open('SwitchAddresses.csv', 'r') as f:
        for row in csv.reader(f):
            switch_ips.append(row[0])
    multithread(populate_arp_table, ['192.168.2.9'])
    multithread(write_arp_tables, ['192.168.2.9'])
