from __future__ import unicode_literals
import socket
import sys
import inspect
from pprint import pprint
import csv
from SwitchDiagnostics import *
from halo import Halo
from secret import IP_RANGE


def retrieve_name(var):
    """
    Gets name of variable passed to a function.
    :param var: Variable whos name is needed.
    :return: String of original variable name.
    """
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var][0]


def write_result_csv(source, method, prepend=None):
    """
    Writes a list of dictionaries to a CSV file in CWD. Name
    of file is generated from name of list variable. Requires
    'retrieve_name' function.
    :param source: List of dictionaries with same field names.
    :param method: Method of writing ('w', 'w+', 'a', 'a+').
    :param prepend: String to prepend to filename, optional.
    :return: None
    """
    file_empty = os.stat('collection1.dat').st_size == 0
    if prepend is None:
        filename = f'{retrieve_name(source)}.csv'
    else:
        filename = f'{prepend}-{retrieve_name(source)}.csv'
    fieldnames = list(source[0].keys())
    with open(filename, method) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n', delimiter=',')
        if file_empty:
            writer.writeheader()
        for data in source:
            writer.writerow(data)
            pprint(f"Writing Row: {data}")


def reformat_mac(mac):
    """
    Reformat MAC address to all lowercase with
     dashes separating octets e.g. 1a-2a-a3-b5-e4-2a
    :param mac: MAC address to format
    :return: reformatted MAC as string
    """
    mac = mac.replace('-', '').replace(':', '')
    mac = '-'.join(mac[i:i + 2] for i in range(0, 12, 2)).lower()
    return mac


def get_hostname_by_ip(ip):
    """
    Gets hostname by IP address.
    :param ip: IP to check as string.
    :return: Either the hostname as a string or 'Hostname not found'
    """
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return 'Hostname not found'


def write_mac_tables(ip):
    spinner = Halo(spinner='dots')
    try:
        commands = ['arp']
        ip_list = generate_ip_list(IP_RANGE)
        ping_from_switch(ip, ip_list)
        show_switch(ip, commands)
        arp_list = []
        spinner.start(f'\nGetting ARP table from switch at {ip}')
        with open(f'switch_arp/{ip}', 'r') as f:
            raw_arp_table = f.read()
        spinner.succeed()
        spinner.stop()
        spinner.start(f'\nFormatting ARP table and writing to file.')
        fixed_arp_list = [x.strip() for x in raw_arp_table.split("\n")[6:-2]]
        for item in fixed_arp_list:
            item = item.replace('     ', ' ').replace('    ', ' ').replace('   ', ' ').replace('  ', ' ')
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
        spinner.succeed(f'\nFile written to switch_arp/{ip}')
        spinner.stop()
        return f'Success on {ip}'
    except (KeyboardInterrupt, SystemExit):
        spinner.stop()


if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # get_all_ips(IP_RANGE)
    with open('SwitchAddresses.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            write_mac_tables(row[0])
