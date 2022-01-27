import os

from netmiko import ConnectHandler
from secret import USERNAME, PASSWORD, DEVICE_TYPE
from halo import Halo


def get_connection(ip: str) -> ConnectHandler:
    """
    Connects to switch at provided IP using configured credentials.
    :param ip: IP of switch as string
    :return: Connection as ConnectHandler
    """
    connection = ConnectHandler(ip=ip,
                                device_type=DEVICE_TYPE,
                                username=USERNAME,
                                password=PASSWORD)
    return connection


def ping_from_switch(switch_ip: str, ip_list: list[str]) -> None:
    """
    Pings list of IPs from switch. Used primarily for populating ARP table.
    :param switch_ip: IP of switch to ping from
    :param ip_list: List of IP addresses to ping
    :return: None
    """
    spinner = Halo(spinner='dots')
    spinner.start(f'\nConnecting to {switch_ip}')
    connection = get_connection(switch_ip)
    spinner.succeed()
    spinner.stop()
    for ip in ip_list:
        spinner.start(f'\nPinging {ip} from switch {switch_ip}')
        connection.send_command(f'ping {ip}')
        spinner.succeed()
        spinner.stop()
    connection.disconnect()


def run_commands(ip: str, commands: list[str]) -> None:
    """
    Cycles through a list of 'show' commands to run on a switch
    :param ip: Address of switch as String
    :param commands: Command to run on switch
    :return: None
    """
    spinner = Halo(spinner='dots')
    spinner.start(f'Connecting to {ip}')
    connection = get_connection(ip)
    spinner.succeed()
    spinner.stop()
    for command in commands:
        spinner.start(f'\nRunning "{command}" on switch at {ip}. This might take a bit.')
        return_data = connection.send_command(command)
        spinner.succeed()
        spinner.stop()
        command = command.replace(' ', '_').replace('-', '_')
        spinner.start(f'\nWriting {command} to switch_{command}/{ip}')
        if not os.path.exists(f'switch_{command}'):
            os.mkdir(f'switch_{command}')
        with open(f'switch_{command}/{ip}', 'w+') as f:
            f.write(return_data)
        spinner.succeed(f'\nCommand "show {command}" on {ip} completed and written to switch_{command}/{ip}')
        spinner.stop()
    spinner.start(f'\nClosing connection to {ip}')
    connection.disconnect()
    spinner.succeed()
    spinner.stop()
