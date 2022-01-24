import subprocess
import inspect
import csv
from pprint import pprint

from netmiko import ConnectHandler
import xml.etree.ElementTree as ET
from secret import HP_USERNAME, HP_PASSWORD, IP_RANGE


def retrieve_name(var):
    callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var][0]


def write_result_csv(source, ip=None):
    if ip is None:
        filename = f'{retrieve_name(source)}.csv'
    else:
        filename = f'{ip}-{retrieve_name(source)}.csv'
    fieldnames = list(source[0].keys())
    with open(filename, 'w+') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for data in source:
            writer.writerow(data)
            print(f"Writing Row: {data}")


# def parse_xml(xmlfile):
#     tree = ET.parse(xmlfile)
#     root = tree.getroot()
#     host_ip = []
#     for item in root.findall('./host/hostnames'):
#


def get_all_ips(network_range):
    sp = subprocess.Popen(f"nmap -sP -oX scan.xml {network_range}",
                          shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    out, err = sp.communicate()
    if out:
        print(out.decode(('utf-8')))
    if err:
        print(err.decode(('utf-8')))



def write_macs():
    comp_fail_list = []
    comp_mac_list = []
    with open('ADcomputerslist.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            print(row[0])
            sp = subprocess.Popen(f"getmac /s {row[0]} /fo csv",
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            out, err = sp.communicate()
            if out:
                print("Command Succeeded")
                subprocess_return = out.decode('utf-8')
                return_list = subprocess_return.split(',')
                mac = return_list[1].split('\n')[1].replace('"', '').lower()
                print(f'{row[0]}: {mac}')
                comp_mac_list.append({"Name": row[0], "MAC": mac})
            if err:
                print('Command Failed')
                subprocess_return = err.decode('utf-8')
                comp_fail_list.append({"Name": row[0], "Error": subprocess_return.strip()})
    write_result_csv(comp_mac_list)
    write_result_csv(comp_fail_list)


def write_mac_tables(ip):
    matches = []
    connection = ConnectHandler(ip=ip, device_type='hp_procurve', username=HP_USERNAME, password=HP_PASSWORD)
    test_out = connection.send_command_timing('no page')
    if 'Press any key' in test_out:
        test_out += connection.send_command_timing('y')
    raw_mac_table = connection.send_command('show mac-address')
    print(raw_mac_table)
    print('Fixed MAC Table')
    fixed_mac_list = [x.strip() for x in raw_mac_table.split("\n")[4:-1]]
    mac_port_dict_list = []
    if '' in fixed_mac_list:
        fixed_mac_list.remove('')
    for line in fixed_mac_list:
        line = line.split(' ')
        print(line)
        mac = line[0]
        port = line[1]
        host = ''
        mac = mac.replace('-', '')
        mac = '-'.join(mac[i:i + 2] for i in range(0, 12, 2))
        with open('comp_mac_list.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # print(f'Switch Mac: {mac} -- AD Mac: {row["MAC"]}')
                if row["MAC"] == mac:
                    matches.append({"Name": row["Name"], "MAC": mac})
                    host = row["Name"]
        mac_port_dict_list.append({'MAC': mac, 'Port': port, 'Host': host})
    if matches:
        write_result_csv(matches, ip=ip)
    pprint(mac_port_dict_list)
    write_result_csv(mac_port_dict_list, ip=ip)
    connection.disconnect()


if __name__ == '__main__':
    # write_ad_comp_macs()
    # with open('SwitchAddresses.csv', 'r') as f:
    #     reader = csv.reader(f)
    #     for row in reader:
    #         write_mac_tables(row[0])
    get_all_ips(IP_RANGE)
