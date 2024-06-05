import os
import subprocess
import sys
from fpdf import FPDF
from colorama import init, Fore, Style
import requests
import socket
import dns.resolver

def install(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError:
        print(f"Error instalando {package}")
        sys.exit(1)

dependencies = ["shodan", "requests", "colorama", "fpdf", "dnspython", "sublist3r"]
for package in dependencies:
    try:
        __import__(package)
    except ImportError:
        install(package)

import shodan
import requests
import colorama
import dns.resolver
import sublist3r

init(autoreset=True)

SHODAN_API_KEY = 'MJKy1ty99gxsLLkKvQiSv25Q86cm9GBJ'
shodan_api = shodan.Shodan(SHODAN_API_KEY)

def obtener_info_ip(ip):
    try:
        resultado = shodan_api.host(ip)
        return resultado
    except shodan.APIError as e:
        return f'Error en Shodan: {e}'

def obtener_info_dns(dominio):
    try:
        url = f"https://api.hackertarget.com/hostsearch/?q={dominio}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.split('\n')
        else:
            return f'Error en DNSDumpster: {response.status_code}'
    except Exception as e:
        return f'Error al acceder a DNSDumpster: {e}'

def obtener_registros_dns(dominio):
    registros = {}
    try:
        respuestas_a = dns.resolver.resolve(dominio, 'A')
        registros['A'] = [rdata.to_text() for rdata in respuestas_a]
    except Exception as e:
        registros['A'] = f'Error al obtener registros A: {e}'
    
    try:
        respuestas_mx = dns.resolver.resolve(dominio, 'MX')
        registros['MX'] = [rdata.exchange.to_text() for rdata in respuestas_mx]
    except Exception as e:
        registros['MX'] = f'Error al obtener registros MX: {e}'
    
    try:
        respuestas_ns = dns.resolver.resolve(dominio, 'NS')
        registros['NS'] = [rdata.to_text() for rdata in respuestas_ns]
    except Exception as e:
        registros['NS'] = f'Error al obtener registros NS: {e}'

    return registros

def detectar_tecnologias(dominio):
    try:
        url = f'http://{dominio}'
        response = requests.get(url)
        headers = response.headers
        tecnologias = []
        server = headers.get('Server')
        if server:
            tecnologias.append(f'Server: {server}')
        x_powered_by = headers.get('X-Powered-By')
        if x_powered_by:
            tecnologias.append(f'X-Powered-By: {x_powered_by}')
        return {'WhatWeb Resultados': tecnologias}
    except Exception as e:
        return f'Error al detectar tecnologías web: {e}'

def obtener_info_github(username):
    url = f'https://api.github.com/users/{username}'
    try:
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            return f'Error en la consulta: {respuesta.status_code}'
    except Exception as e:
        return f'Error al acceder a GitHub: {e}'

def obtener_subdominios(dominio):
    try:
        subdominios = sublist3r.main(dominio, 40, savefile=None, ports=None, silent=True, verbose=False, enable_bruteforce=False, engines=None)
        return subdominios
    except Exception as e:
        return f'Error al ejecutar Sublist3r: {e}'

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 102, 204)
        self.cell(0, 10, 'Informe de OSINT', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.cell(0, 10, 'Generado por ByOSINT', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'ByOSINT', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(255, 69, 0)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_watermark(self):
        self.set_font('Arial', 'I', 50)
        self.set_text_color(200, 200, 200)
        self.rotate(45, x=60, y=60)
        self.text(60, 100, 'ByOSINT')
        self.rotate(0)

    def rotate(self, angle, x=None, y=None):
        if x and y:
            self.x, self.y = x, y
        self._out(f'q {angle} 0 0 {angle} {self.x} {self.y} cm')
        self._out('q')

    def _endpage(self):
        self.add_watermark()
        super()._endpage()

def crear_informe(datos, archivo_pdf):
    pdf = PDF()
    pdf.add_page()
    for titulo, contenido in datos.items():
        pdf.chapter_title(titulo)
        if isinstance(contenido, dict):
            for key, value in contenido.items():
                pdf.chapter_body(f"{key}: {value}")
        elif isinstance(contenido, list):
            contenido = '\n'.join(map(str, contenido))
            pdf.chapter_body(contenido)
        else:
            pdf.chapter_body(contenido)
    pdf.output(archivo_pdf)

def mostrar_banner():
    print(Fore.CYAN + Style.BRIGHT + """
    ##############################################
    #                                            #
    #                  ByOSINT                   #
    #                                            #
    ##############################################
    """ + Style.RESET_ALL)

def main():
    mostrar_banner()
    
    ip = input(Fore.GREEN + 'Introduce la IP a investigar (ej. 8.8.8.8): ' + Style.RESET_ALL)
    dominio = input(Fore.GREEN + 'Introduce el dominio a investigar: ' + Style.RESET_ALL)
    github_username = input(Fore.GREEN + 'Introduce el nombre de usuario de GitHub: ' + Style.RESET_ALL)

    print(Fore.YELLOW + "\nRecolectando información, por favor espera...\n" + Style.RESET_ALL)

    datos = {
        'Información de IP (Shodan)': obtener_info_ip(ip),
        'Información DNS con DNSDumpster': obtener_info_dns(dominio),
        'Registros DNS': obtener_registros_dns(dominio),
        'Detección de tecnologías web con WhatWeb': detectar_tecnologias(dominio),
        'Información de usuario de GitHub': obtener_info_github(github_username),
        'Subdominios (Sublist3r)': obtener_subdominios(dominio)
    }

    crear_informe(datos, 'informe_osint.pdf')
    print(Fore.CYAN + 'Informe generado: informe_osint.pdf' + Style.RESET_ALL)

if __name__ == '__main__':
    main()
