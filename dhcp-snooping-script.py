import netmiko.exceptions
from netmiko import ConnectHandler
import datetime
import csv
from os.path import exists
from os import makedirs


# Read the "parameters.txt" and return a dict.
def readParameters(path):
    with open(path, 'r', encoding="utf-8") as parameters:
        result = {}
        for line in parameters.readlines():
            key = line.split('=')[0]
            if line.split('=')[0] in ['user', 'password', 'csv_path', 'trust_port_name', 'specific_text']:
                value = str(line.split('=')[1].strip())
            elif line.split('=')[0] in ['specific_limit_rate', 'default_limit_rate', 'timeout']:
                value = int(line.split('=')[1].strip())
            elif line.split('=')[0] in ['ignore_errors', 'simulation']:
                value = bool(line.split('=')[1].strip())
            elif line.split('=')[0] == 'exclusive_vlans':
                value = line.split('=')[1].strip()
            else:
                raise Exception("Error reading parameters. Check file variables.")
                return None
            result[key] = value
        return result


# Returns the trusted port from the stardardized port name.
def trustPort(int_status, trust_port_name):
    tuple_list = list(enumerate(int_status.split()))
    for i, text in tuple_list:
        if text == trust_port_name:
            for element in tuple_list[i-1]:
                if str(element) != str(i-1):
                    result = element
                    return result
    return None


# Returns a list of untrusted ports.
def untrustedPorts(int_status, trust_port):
    result = []
    for element in list(int_status.split()):
        if (r"Fa0/" in element or r"Gi0/" in element or r"Gi1/" in element) and element != trust_port:
            result.append(element)
    return result


# Returns a list of vlans.
def vlanList(vlan_brief, exclusive_vlans=None):
    if exclusive_vlans is None:
        exclusive_vlans = []
    result = []
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    for item in list(vlan_brief.split()):
        for digit in digits:
            if digit in item and "gi" not in item.lower() and "fa" not in item.lower() and "vlan" not in item.lower() and item not in exclusive_vlans and item not in result:
                result.append(item)
    return result


# Returns a list of ports that contain the given specific text
def specificPorts(int_status, specific_text):
    result = []
    if specific_text is None:
        return result
    else:
        tuple_list = list(enumerate(int_status.split()))
        for i, text in tuple_list:
            if str(specific_text) in text:
                for elemento in tuple_list[i - 1]:
                    if str(elemento) != str(i - 1):
                        result.append(elemento)
        return result


# Returns the local date and time
def dateTime():
    return f'[{datetime.datetime.today().strftime("%d/%m/%Y - %H:%M:%S")}] - '


# Returns a list of ips from a standardized ".csv" file as follows:
# The first column must contain the IPv4 address of the host
# The second column defines whether the program will configure the address through the data 'Y' for yes or 'N' for no.
def ipListFromCSV(path):
    with open(path) as arquivo:
        result = []
        leitor = csv.reader(arquivo)
        dados = list(leitor)
        for line in dados:
            for element in line:
                try:
                    if str(element.split(';')[1]).upper() == "Y":
                        result.append(element.split(';')[0])
                except IndexError:
                    continue
        return result


# Defines whether the "allow untrusted" configuration should be executed from a standardized ".csv" file as follows:
# The first column must contain the IPv4 address of the host
# The third column defines whether the program will configure the address through the data 'Y' for yes or 'N' for no.
def allowUntrusted(path, ip_address):
    with open(path) as arquivo:
        leitor = csv.reader(arquivo)
        dados = list(leitor)
        for line in dados:
            for element in line:
                try:
                    if element.split(';')[1] == ip_address and str(element.split(';')[2]).upper() == 'Y':
                        return True
                    else:
                        return False
                except IndexError:
                    pass


# Defines the list of commands to be executed
def configCommands(vlan_list, csv_path, ip_address, porta_confiavel, portas_nao_confiaveis, specific_ports,
                   specific_limit_rate, default_limit_rate):

    result = []

    # ip dhcp snooping vlan
    vlans = ""
    for vlan in vlan_list:
        vlans += vlan
        if vlan != vlan_list[len(vlan_list) - 1]:
            vlans += ","
    result.append(f"ip dhcp snooping vlan {vlans}")

    # ip dhcp snooping information option allow-untrusted
    if allowUntrusted(csv_path, ip_address):
        result.append(f"ip dhcp snooping information option allow-untrusted")

    # interface {port}
    # ip dhcp snooping limit rate {limit_rate}
    for porta in portas_nao_confiaveis:
        result.append(f"interface {porta}")
        if porta in specific_ports:
            result.append(f"ip dhcp snooping limit rate {specific_limit_rate}")
        else:
            result.append(f"ip dhcp snooping limit rate {default_limit_rate}")

    # interface {trust_port}
    # ip dhcp snooping trust
    result.append(f"interface {porta_confiavel}")
    result.append("ip dhcp snooping trust")

    # exit
    result.append("exit")

    # errdisable recovery cause all
    # errdisable recovery interval 30
    # errdisable detect cause all
    result.append("errdisable recovery cause all")
    result.append("errdisable recovery interval 30")
    result.append("errdisable detect cause all")

    # ip dhcp snooping
    result.append("ip dhcp snooping")

    # wr
    result.append("do wr")

    return result


# Método main()
def main():
    
    # Assigns the user parameters to the "parameters" variable
    parameters = readParameters('parameters.txt')
    
    # Assignment of parameters to their respective variables
    user = parameters['user']  # authentication user
    password = parameters['password']  # authentication password
    csv_path = parameters['csv_path']  # path to the ".csv" file
    trust_port_name = parameters['trust_port_name']  # standardized name of the port that will be configured as trusted
    specific_text = parameters['specific_text']  # specific text contained in specific ports
    exclusive_vlans = parameters['exclusive_vlans']  # list of vlans that should not be included in the configuration
    specific_limit_rate = parameters['specific_limit_rate']  # specific portas limit rate
    default_limit_rate = parameters['default_limit_rate']  # default limit rate
    ignore_errors = parameters['ignore_errors']  # bool expression to ignore errors
    simulation = parameters['simulation']  # bool expression to simulate config
    timeout = parameters['timeout']  # value in seconds for maximum connection attempt time

    # Checks if the "reports" folder exists and, if not, creates it.
    if not exists('reports'):
        makedirs('reports')

    # Create the report file with index 0 inside the "reports" folder
    report_file_name = f'reports/0-dhcp-snooping-config-report-({datetime.datetime.today().strftime("%d.%m.%Y_%H.%M.%S")}).txt'
    report = open(report_file_name, 'w', encoding="utf-8")

    # Starts the counter variable
    counter = 0
    
    # Load the ip address list from the csv file
    ip_address_list = ipListFromCSV(csv_path)

    for ip_address in ip_address_list:

        # Increment the counter
        counter += 1

        # Creates the text document referring to the configuration of the current ip address in the "reports" folder
        log = open(f'reports/{counter}-dhcp-snooping-config-log-[{ip_address}]-({datetime.datetime.today().strftime("%d.%m.%Y_%H.%M")}).txt', 'w', encoding="utf-8")

        # Insert the current address to the report
        print(f"\n{counter} - {ip_address}...")
        report.write(f"\n{counter} - {ip_address}...")

        # Start of defining variables
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-= PARAMETERS DEFINITION =-=-=-=-=-=-=-=-=-=-=-=-\n')

        # Set host parameters
        log.write(f'{dateTime()}Definindo parâmetros do host...')
        Network_Device_1 = {"host": ip_address,
                            "username": user,
                            "password": password,
                            "device_type": "cisco_ios",
                            "secret": "secret",
                            "timeout": timeout
                            }
        log.write(f' OK!\n')

        # Establish connection to host
        try:
            log.write(f'{dateTime()}Connecting to {ip_address}...')
            connection = ConnectHandler(**Network_Device_1)
            log.write(f' OK!\n')
        except netmiko.exceptions.AuthenticationException:
            log.write(f' Auth error.\n')
            log.write(f'{dateTime()}Terminated due to reported error.\n')
            print(f"{counter} - {ip_address} - Auth error.")
            report.write(f"\n{counter} - {ip_address} - Auth error.\n")
            if ignore_errors:
                continue
            else:
                break
        except netmiko.exceptions.ConfigInvalidException:
            log.write(f' Device configuration error.\n')
            log.write(f'{dateTime()}Terminated due to reported error.\n')
            print(f"{counter} - {ip_address} - Device configuration error. ({Network_Device_1})")
            report.write(f"{counter} - {ip_address} - Device configuration error. ({Network_Device_1})\n")
            if ignore_errors:
                continue
            else:
                break
        except netmiko.exceptions.NetmikoTimeoutException:
            log.write(f' Connection timeout.\n')
            log.write(f'{dateTime()}Terminated due to reported error.\n')
            print(f"{counter} - {ip_address} - Connection timeout. ({ip_address})")
            report.write(f"\n{counter} - {ip_address} - Connection timeout. ({ip_address})\n")
            if ignore_errors:
                continue
            else:
                break

        # Send "enable" command
        log.write(f'{dateTime()}Sending "enable" command \"enable\"...')
        connection.enable()
        log.write(f' OK!\n')

        # Assign the command "sh run | in hostname | ex router" output to the variable hostname
        log.write(f'{dateTime()}Assigning hostname...')
        hostname = connection.send_command("sh run | in hostname | ex router")
        log.write(f' OK!\n')

        # Assign the command "sh vlan brief" output to the variable vlan_brief
        log.write(f'{dateTime()}Assigning vlan brief from host...')
        vlan_brief = connection.send_command("sh vlan brief")
        log.write(f' OK!\n')

        # Assign the command "sh int status" output to the variable int_status
        log.write(f'{dateTime()}Assigning interface status from host...')
        int_status = connection.send_command("sh int status")
        log.write(f' OK!\n')

        # Defines the trusted port
        log.write(f'{dateTime()}Defining trusted port...')
        trust_port = trustPort(int_status, trust_port_name=trust_port_name)
        if trust_port is not None:
            log.write(f' OK!\n')
        else:
            log.write(f' Error: There is no port named \"{trust_port_name}\".\n')
            log.write(f'{dateTime()}Terminated due to reported error.\n')
            log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n')
            print(f"{counter} - {ip_address} - Error: There is no port named \"{trust_port_name}\".")
            report.write(f"\n{counter} - {ip_address} - Error: There is no port named \"{trust_port_name}\".\n")
            if ignore_errors:
                continue
            else:
                break

        # Defines the untrusted ports
        log.write(f'{dateTime()}Defining the untrusted ports...')
        untrusted_ports = untrustedPorts(int_status, trust_port)
        log.write(f' OK!\n')

        # Defines the list of vlans to be configured
        log.write(f'{dateTime()}Defining the list of vlans to be configured...')
        vlan_list = vlanList(vlan_brief, exclusive_vlans=exclusive_vlans)
        log.write(f' OK!\n')

        # Defines the specific ports
        log.write(f'{dateTime()}Defining the specific ports...')
        specific_ports = specificPorts(int_status, specific_text=specific_text)
        log.write(f' OK!\n')

        # Defines the config commands
        log.write(f'{dateTime()}Defining the config commands...')
        config_commands = configCommands(vlan_list, csv_path, ip_address, trust_port, untrusted_ports,
                                         specific_ports, specific_limit_rate, default_limit_rate)
        log.write(f' OK!\n')
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n\n\n')

        # Configuration
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- CLI -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n')
        if not simulation:
            set_config = connection.send_config_set(config_commands)
            log.write(f'{set_config}\n')
        else:
            for command in config_commands:
                log.write(f'{command}')
                log.write("\n")
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n\n\n')

        # Shows the result and additional information
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- RESULTS -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n')
        log.write(f'sh run | in hostname | ex router:\n\n{hostname}\n\n\n')
        ip_dhcp_snooping = connection.send_command("show ip dhcp snooping")
        log.write(f'show ip dhcp snooping\n\n{ip_dhcp_snooping}\n\n\n')
        log.write(f'show vlan brief\n{vlan_brief}\n\n\n')
        log.write(f'show int status\n{int_status}\n\n\n')

        print(f"{counter} - {ip_address} OK!")
        report.write(f"\n{counter} - {ip_address} OK!\n")

        log.close()

    report.close()


if __name__ == "__main__":

    main()
