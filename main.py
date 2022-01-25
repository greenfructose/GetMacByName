from __future__ import unicode_literals
import subprocess
import socket
import os
import sys
import time
import inspect
import csv
from pprint import pprint

from netmiko import ConnectHandler
import xml.etree.ElementTree as ET
from halo import Halo
from secret import HP_USERNAME, HP_PASSWORD, IP_RANGE, ADDRESS_OF_SCANNER


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
    if prepend is None:
        filename = f'{retrieve_name(source)}.csv'
    else:
        filename = f'{prepend}-{retrieve_name(source)}.csv'
    fieldnames = list(source[0].keys())
    with open(filename, method) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n', delimiter=',')
        writer.writeheader()
        for data in source:
            writer.writerow(data)
            pprint(f"Writing Row: {data}")


def reformat_mac(mac):
    mac = mac.replace('-', '').replace(':', '')
    mac = '-'.join(mac[i:i + 2] for i in range(0, 12, 2)).lower()
    return mac


def get_hostname_by_ip(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return 'Hostname not found'


def parse_xml(xmlfile):
    spinner = Halo(spinner='dots')
    ip_mac_list = []
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    # print('Getting all hosts detected.')
    for item in root.findall('./host'):
        spinner.start(text='Checking hosts in XML file for IP/MAC addresses')
        temp_list = []
        for child in item:
            # print('Checking if host has address.')
            if child.tag == 'address':
                if child.attrib['addr'] == ADDRESS_OF_SCANNER:
                    spinner.fail(text=f'Skipping {ADDRESS_OF_SCANNER}, scanning self gives invalid data')
                    spinner.stop()
                    continue
                spinner.succeed(text=f'Address {child.attrib["addr"].lower()} found. Adding to list')
                spinner.stop()
                temp_list.append(child.attrib['addr'].lower())
            else:
                spinner.fail(text='No Address, checking next host.')
                spinner.stop()
        if temp_list:
            spinner.start(text=f'Getting Hostname for IP {temp_list[0]}')
            host = get_hostname_by_ip(temp_list[0])
            # print('Adding IP/MAC/Hostname to data list')
            ip_mac_list.append({'IP': temp_list[0], 'MAC': reformat_mac(temp_list[1]), 'Hostname': host})
            spinner.succeed(text='Entry added to list')
            spinner.stop()
    spinner.start(text=f'Writing results to CSV.')
    write_result_csv(ip_mac_list, 'w+')
    spinner.succeed(text='Done parsing XML')
    spinner.stop()


def get_all_ips(network_range):
    spinner = Halo(spinner='dots')
    spinner.start(text=f'Arp scanning network_range {network_range}. This may take awhile.')
    sp = subprocess.Popen(f"nmap -sP -oX scan.xml {network_range}",
                          shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    out, err = sp.communicate()
    if out:
        with open('scan_success.log', 'a+') as f:
            f.write(out.decode('utf-8'))
        spinner.succeed(text='Scan completed successfully. View log at scan_success.log')
        spinner.stop()
    if err:
        with open('scan_error.log', 'a+') as f:
            f.write(err.decode('utf-8'))
        spinner.fail(text='Scan failed. View log at scan_error.log')
        spinner.stop()


def write_mac_tables(ip):
    spinner = Halo(spinner='dots')
    ip_mac_switch_port_list = []
    try:
        spinner.start(text=f'Connecting to switch at IP {ip}')
        connection = ConnectHandler(ip=ip, device_type='hp_procurve', username=HP_USERNAME, password=HP_PASSWORD)
        if connection:
            spinner.succeed(text=f'Connected to switch at IP {ip}')
            spinner.stop()
        else:
            spinner.fail(text=f'Failed to connect to switch at IP {ip}')
            spinner.stop()
        test_out = connection.send_command_timing('no page')
        if 'Press any key' in test_out:
            test_out += connection.send_command_timing('y')
        spinner.start(text='Getting MAC addresses. This will take a bit.')
        raw_mac_table = connection.send_command('show mac-address')
        spinner.succeed(text=f'Got MAC table from switch at {ip}')
        spinner.stop()
        print(f'Disconnecting from switch {ip}')
        connection.disconnect()
        spinner.start(text='Formatting MAC table')
        fixed_mac_list = [x.strip() for x in raw_mac_table.split("\n")[4:-1]]
        mac_port_dict_list = []
        if '' in fixed_mac_list:
            fixed_mac_list.remove('')
        for line in fixed_mac_list:
            line = line.split(' ')
            print(line)
            if line:
                mac = reformat_mac(line[0])
                port = line[1]
                print('Adding MAC/Port pair to dictionary')
                mac_port_dict_list.append({'MAC': mac, 'Port': port})
        spinner.succeed(text='Mac Table Formatted')
        spinner.stop()
        spinner.start(text=f'Checking for MAC matches in IP range {IP_RANGE}')
        write_result_csv(mac_port_dict_list, 'a+')
        full_mac_port_dict_list = []
        with open('mac_port_dict_list.csv', 'r') as f:
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                full_mac_port_dict_list.append({'MAC': row["MAC"], 'Port': row["Port"]})
        with open('ip_mac_list.csv', 'r') as f:
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                # print('TEST: Is row retrieval working')
                # print(f'MAC from READER = {row["MAC"]}')
                for item in full_mac_port_dict_list:
                    # print(f'MAC from ITEM = {item["MAC"]}')
                    # print('Checking for MAC matches between dictionary and list')
                    if row['MAC'] == item['MAC']:
                        spinner.succeed(text=f'Match found.')
                        spinner.stop()
                        spinner.start(text=f'Adding entry for MAC {item["MAC"]} on switchport {item["Port"]}')
                        ip_mac_switch_port_list.append(
                            {'IP': row['IP'],
                             'MAC': item['MAC'],
                             'Hostname': row['Hostname'],
                             'Switch IP': ip,
                             'Switch Port': item['Port']})
                        spinner.succeed(f'Item Added')
                        spinner.stop()
                spinner.fail(text='No matches found, trying next row')
                spinner.stop()
        if ip_mac_switch_port_list:
            print(f'Showing complete list for switch {ip}')
            print('_________________________________________________________________________')
            pprint(ip_mac_switch_port_list)
            print('_________________________________________________________________________')
            spinner.start(text='Appending results to CSV')
            write_result_csv(ip_mac_switch_port_list, 'a+')
            spinner.succeed('File written')
            spinner.stop()
        print(f'Done with switch {ip}')
        print('_________________________________________________________________________')
    except (KeyboardInterrupt, SystemExit):
        spinner.stop()


if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # get_all_ips(IP_RANGE)
    parse_xml('scan.xml')
    with open('SwitchAddresses.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            write_mac_tables(row[0])
