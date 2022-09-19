import netmiko.exceptions
from netmiko import ConnectHandler
import datetime
import csv
from os.path import exists
from os import makedirs


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
                print("Erro na leitura dos parâmetros. Pressione Enter para continuar...")
                input()
                return None
            result[key] = value
        return result


# Retorna a porta confiável a partir do nome da porta padronizado
def trustPort(int_status, trust_port_name):
    tuple_list = list(enumerate(int_status.split()))
    for i, text in tuple_list:
        if text == trust_port_name:
            for element in tuple_list[i-1]:
                if str(element) != str(i-1):
                    result = element
                    return result
    return None


# Retorna uma lista de portas não confiáveis.
def untrustedPorts(int_status, trust_port):
    result = []
    for element in list(int_status.split()):
        if (r"Fa0/" in element or r"Gi0/" in element or r"Gi1/" in element) and element != trust_port:
            result.append(element)
    return result


# Retorna uma lista de vlans
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


# Retorna uma lista de portas contendo um conteúdo específico
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


# Retorna a data e o horário local
def dateTime():
    return f'[{datetime.datetime.today().strftime("%d/%m/%Y - %H:%M:%S")}] - '


# Retorna uma lista de ips a partir de um arquivo ".csv" padronizado da seguinte maneira:
# A primeira coluna deve conter o endereço IPv4 do host
# A segunda coluna define se o programa realizará a configuração do endereço através do dado 'Y' para sim ou 'N' para não.
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


# Define se a configuração allow untrusted partir de um arquivo ".csv" padronizado da seguinte maneira:
# A primeira coluna deve conter o endereço IPv4 do host
# A segunda coluna define se o programa realizará a configuração do endereço através do dado 'Y' para sim ou 'N' para não.
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


# Função auxiliar para retornar as vlans exclusivas que forma definidas em conjunto com a equipe de redes.
def exclusiveVlans():
    result = [1, 6, 97, 99, 105, 146, 240, 500, 600, 650, 666, 675, 680, 690, 750, 777, 789, 800, 840, 900, 950, 999,
              1002, 1003, 1004, 1005, 2000, 2001]
    for i in range(301, 446):
        result.append(i)
    return result


# Função auxiliar para definir a lista de comandos a serem executados
def configCommands(vlan_list, csv_path, ip_address, porta_confiavel, portas_nao_confiaveis, portas_especificas,
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

    # interface {porta}
    # ip dhcp snooping limit rate {limit_rate}
    for porta in portas_nao_confiaveis:
        result.append(f"interface {porta}")
        if porta in portas_especificas:
            result.append(f"ip dhcp snooping limit rate {specific_limit_rate}")
        else:
            result.append(f"ip dhcp snooping limit rate {default_limit_rate}")

    # interface {porta_confiavel}
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
    # Parâmetros do Usuário
    parameters = readParameters('parameters.txt')

    user = parameters['user']  # Usuário de autenticação
    password = parameters['password']  # Senha de autenticação
    csv_path = parameters['csv_path']  # Caminho para o arquivo ".csv"
    trust_port_name = parameters['trust_port_name']  # Nome padronizado da porta que será configurada como confiável;
    specific_text = parameters['specific_text']  # Texto específico contido nas portas específicas;
    exclusive_vlans = parameters['exclusive_vlans']  # Lista de vlans que não devem ser incluídas na configuração
    specific_limit_rate = parameters['specific_limit_rate']  # Limit rate das portas específicas
    default_limit_rate = parameters['default_limit_rate']  # Limit rate padrão
    ignore_errors = parameters['ignore_errors']  # Expressão bool para ignorar erros
    simulation = parameters['simulation']  # Expressão bool para simular configuração
    timeout = parameters['timeout']  # Valor em segundos para tempo máximo de tentativa de conexão

    # Verifica se existe a pasta "reports" e, caso não exista, cria a mesma.
    if not exists('reports'):
        makedirs('reports')

    # Cria o arquivo de relatório final dentro da pasta "reports"
    report_file_name = f'reports/0-dhcp-snooping-config-report-({datetime.datetime.today().strftime("%d.%m.%Y_%H.%M.%S")}).txt'
    report = open(report_file_name, 'w', encoding="utf-8")

    # Inicia a variável contadora
    counter = 0
    ip_address_list = ipListFromCSV(csv_path)

    for ip_address in ip_address_list:

        # Incremento do contador
        counter += 1

        # Cria o documento de texto referente à configuração do endereço de ip atual na pasta "reports"
        log = open(f'reports/{counter}-dhcp-snooping-config-log-[{ip_address}]-({datetime.datetime.today().strftime("%d.%m.%Y_%H.%M")}).txt', 'w', encoding="utf-8")

        # Insere o endereço atual ao relatório
        print(f"\n{counter} - {ip_address}...")
        report.write(f"\n{counter} - {ip_address}...")

        # Início da definição de variáveis
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=- Definição de Parâmetros -=-=-=-=-=-=-=-=-=-=-=-\n')

        # Define os parâmetros do host
        log.write(f'{dateTime()}Definindo parâmetros do host...')
        Network_Device_1 = {"host": ip_address,
                            "username": user,
                            "password": password,
                            "device_type": "cisco_ios",
                            "secret": "secret",
                            "timeout": timeout
                            }
        log.write(f' OK!\n')

        # Estabelece conexão com o host
        try:
            log.write(f'{dateTime()}Estabelecendo conexão com o equipamento {ip_address}...')
            connection = ConnectHandler(**Network_Device_1)
            log.write(f' OK!\n')
        except netmiko.exceptions.AuthenticationException:
            log.write(f' Erro de autenticação.\n')
            log.write(f'{dateTime()}Configuração encerrada devido ao erro relatado.\n')
            print(f"{counter} - {ip_address} - Erro de autenticação.")
            report.write(f"\n{counter} - {ip_address} - Erro de autenticação.\n")
            if ignore_errors:
                continue
            else:
                break
        except netmiko.exceptions.ConfigInvalidException:
            log.write(f' Erro de configuração do aparelho.\n')
            log.write(f'{dateTime()}Configuração encerrada devido ao erro relatado.\n')
            print(f"{counter} - {ip_address} - Erro de configuração do aparelho. ({Network_Device_1})")
            report.write(f"{counter} - {ip_address} - Erro de configuração do aparelho. ({Network_Device_1})\n")
            if ignore_errors:
                continue
            else:
                break
        except netmiko.exceptions.NetmikoTimeoutException:
            log.write(f' Tempo de conexão excedido.\n')
            log.write(f'{dateTime()}Configuração encerrada devido ao erro relatado.\n')
            print(f"{counter} - {ip_address} - Erro de timeout durante tentativa de conexão ssh. ({ip_address})")
            report.write(f"\n{counter} - {ip_address} - Erro de timeout durante tentativa de conexão ssh. ({ip_address})\n")
            if ignore_errors:
                continue
            else:
                break

        # Envia o comando "enable"
        log.write(f'{dateTime()}Entrando com o comando \"enable\"...')
        connection.enable()
        log.write(f' OK!\n')

        # Resgata o hostname através do comando "sh run | in hostname | ex router"
        log.write(f'{dateTime()}Resgatando hostname...')
        hostname = connection.send_command("sh run | in hostname | ex router")
        log.write(f' OK!\n')

        # Resgata as vlans configuradas no host através do envio do comando "sh vlan brief"
        log.write(f'{dateTime()}Resgatando vlan brief...')
        vlan_brief = connection.send_command("sh vlan brief")
        log.write(f' OK!\n')

        # Resgata as interfaces do host através do envio do comando "sh int status"
        log.write(f'{dateTime()}Resgatando int status...')
        int_status = connection.send_command("sh int status")
        log.write(f' OK!\n')

        # Define a porta confiável
        log.write(f'{dateTime()}Definindo porta confiável...')
        porta_confiavel = trustPort(int_status, trust_port_name=trust_port_name)
        if porta_confiavel is not None:
            log.write(f' OK!\n')
        else:
            log.write(f' Erro: O host não possui nenhuma porta com o nome \"{trust_port_name}\".\n')
            log.write(f'{dateTime()}Configuração encerrada devido ao erro relatado.\n')
            log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n')
            print(f"{counter} - {ip_address} - Erro: O host não possui nenhuma porta com o nome \"{trust_port_name}\".")
            report.write(f"\n{counter} - {ip_address} - Erro: O host não possui nenhuma porta com o nome \"{trust_port_name}\".\n")
            if ignore_errors:
                continue
            else:
                break

        # Define as portas não confiáveis
        log.write(f'{dateTime()}Definindo portas não confiáveis...')
        portas_nao_confiaveis = untrustedPorts(int_status, porta_confiavel)
        log.write(f' OK!\n')

        # Lista as vlans a serem configuradas
        log.write(f'{dateTime()}Definindo lista de vlans...')
        vlan_list = vlanList(vlan_brief, exclusive_vlans=exclusive_vlans)
        log.write(f' OK!\n')

        # Definição das portas específicas
        log.write(f'{dateTime()}Verificando portas específicas...')
        portas_especificas = specificPorts(int_status, specific_text=specific_text)
        log.write(f' OK!\n')

        # Definição dos comandos de configuração
        log.write(f'{dateTime()}Definindo lista de Comandos...')
        config_commands = configCommands(vlan_list, csv_path, ip_address, porta_confiavel, portas_nao_confiaveis,
                                         portas_especificas, specific_limit_rate, default_limit_rate)
        log.write(f' OK!\n')
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n\n\n')

        # Configuração
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- CLI -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n')
        if not simulation:
            set_config = connection.send_config_set(config_commands)
            log.write(f'{set_config}\n')
        else:
            for command in config_commands:
                log.write(f'{command}')
                log.write("\n")
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n\n\n')

        # Exibição do resultado e informações de consulta
        log.write(f'{dateTime()}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= RESULTADO =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n')
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
