import os
import csv
from netmiko import ConnectHandler
from secret import HP_USERNAME, HP_PASSWORD
from halo import Halo


def get_connection(ip):
    connection = ConnectHandler(ip=ip,
                                device_type='hp_procurve',
                                username=HP_USERNAME,
                                password=HP_PASSWORD)
    return connection


def show_switch(ip, item):
    spinner = Halo(spinner='dots')
    spinner.start(f'Connecting to {ip}')
    connection = get_connection(ip)
    spinner.succeed()
    spinner.stop()
    spinner.start(f'Getting {item}. This might take a bit.')
    startup_config = connection.send_command(f'show {item}')
    spinner.succeed()
    spinner.stop()
    spinner.start(f'Closing connection to {ip}')
    connection.disconnect()
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


if __name__ == '__main__':
    with open('SwitchAddresses.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            show_switch(row[0], 'config')
            show_switch(row[0], 'running-config')
            show_switch(row[0], 'arp')
            show_switch(row[0], 'mac-address')

