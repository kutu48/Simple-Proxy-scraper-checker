import os
import requests
import socks
import socket
import concurrent.futures
import time
from colorama import init, Fore
from urllib.parse import urlparse

# Inisialisasi untuk colorama (untuk log berwarna)
init(autoreset=True)

# Fungsi untuk membaca URL dari file data.txt
def read_urls_from_file(filepath):
    urls = {}
    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('SOCKS4'):
                urls['socks4'] = line.split(': ')[1]
            elif line.startswith('SOCKS5'):
                urls['socks5'] = line.split(': ')[1]
            elif line.startswith('HTTP'):
                urls['http'] = line.split(': ')[1]
    return urls

# Fungsi untuk mengunduh konten dari URL dan mengembalikan daftar proxy
def download_proxies(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Memastikan responsnya sukses
        proxies = response.text.splitlines()  # Memisahkan baris menjadi daftar proxy
        return [proxy.strip() for proxy in proxies if proxy.strip()]  # Menghapus spasi kosong
    except requests.RequestException as e:
        print(Fore.RED + f"Error fetching proxies from {url}: {e}")
        return []

# Fungsi untuk menambahkan protocol ke setiap proxy
def add_protocol(proxies, protocol):
    return [f"{protocol}://{proxy}" for proxy in proxies]

# Fungsi untuk mengecek apakah proxy http/https aktif
def check_http_proxy(proxy):
    try:
        proxies = {
            "http": proxy,
            "https": proxy,
        }
        start_time = time.time()
        # Melakukan request ke google.com dengan timeout 5 detik
        response = requests.get("https://google.com", proxies=proxies, timeout=5)
        response.raise_for_status()  # Raise error jika status code bukan 200
        elapsed_time = time.time() - start_time
        print(Fore.GREEN + f"[SUCCESS] {proxy} - Time: {elapsed_time:.2f}s")
        return True
    except requests.RequestException:
        print(Fore.RED + f"[FAILED] {proxy}")
        return False

# Fungsi untuk mengecek apakah proxy SOCKS4 atau SOCKS5 aktif
def check_socks_proxy(proxy, socks_version):
    try:
        # Parsing URL untuk mengambil host dan port
        parsed_url = urlparse(proxy)
        proxy_host = parsed_url.hostname
        proxy_port = parsed_url.port
        
        # Cek jika proxy_host atau proxy_port tidak ditemukan
        if not proxy_host or not proxy_port:
            print(Fore.RED + f"[FAILED] {proxy} - Invalid proxy format")
            return False

        socks.set_default_proxy(socks_version, proxy_host, int(proxy_port))
        socket.socket = socks.socksocket

        start_time = time.time()
        # Coba koneksi ke google.com menggunakan soket langsung
        s = socket.create_connection(("google.com", 80), timeout=5)
        s.sendall(b"HEAD / HTTP/1.1\r\nHost: google.com\r\n\r\n")
        s.recv(1024)
        s.close()

        elapsed_time = time.time() - start_time
        print(Fore.GREEN + f"[SUCCESS] {proxy} - Time: {elapsed_time:.2f}s")
        return True
    except Exception as e:
        print(Fore.RED + f"[FAILED] {proxy} - {e}")
        return False

# Fungsi untuk memfilter proxy yang aktif
def filter_active_proxies(proxies, protocol, max_workers=500):
    active_proxies = []
    total_checked = 0
    successful_proxies = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        if protocol == 'http':
            results = executor.map(check_http_proxy, proxies)
        elif protocol == 'socks4':
            results = executor.map(lambda proxy: check_socks_proxy(proxy, socks.SOCKS4), proxies)
        elif protocol == 'socks5':
            results = executor.map(lambda proxy: check_socks_proxy(proxy, socks.SOCKS5), proxies)
        
        for proxy, is_active in zip(proxies, results):
            total_checked += 1
            if is_active:
                active_proxies.append(proxy)
                successful_proxies += 1

    # Tampilkan total proxy yang dicek dan yang berhasil
    print(Fore.CYAN + f"\nTotal proxies checked ({protocol}): {total_checked}")
    print(Fore.CYAN + f"Total proxies successful ({protocol}): {successful_proxies}")
    
    return active_proxies

# Baca URL dari file data.txt
urls = read_urls_from_file('data.txt')

# Mengunduh proxy dari URL
print("Downloading proxies...")
socks4_proxies = download_proxies(urls.get('socks4', ''))
socks5_proxies = download_proxies(urls.get('socks5', ''))
http_proxies = download_proxies(urls.get('http', ''))

# Tambahkan protocol ke masing-masing proxy
socks4_proxies = add_protocol(socks4_proxies, 'socks4')
socks5_proxies = add_protocol(socks5_proxies, 'socks5')
http_proxies = add_protocol(http_proxies, 'http')

# Filter hanya proxy yang aktif
print("Checking HTTP/HTTPS proxies... Please wait.")
active_http_proxies = filter_active_proxies(http_proxies, 'http')

print("Checking SOCKS4 proxies... Please wait.")
active_socks4_proxies = filter_active_proxies(socks4_proxies, 'socks4')

print("Checking SOCKS5 proxies... Please wait.")
active_socks5_proxies = filter_active_proxies(socks5_proxies, 'socks5')

# Gabungkan semua proxy yang aktif
all_active_proxies = active_http_proxies + active_socks4_proxies + active_socks5_proxies

# Path file hasil
output_dir = '/dawn-bot/'
output_file = os.path.join(output_dir, 'proxy.txt')

# Tulis semua proxy yang aktif ke dalam file output
with open(output_file, 'w') as output:
    for proxy in all_active_proxies:
        output.write(f"{proxy}\n")

# Tampilkan ringkasan akhir
print(Fore.CYAN + f"\nTotal informasi proxies checked (http): {len(http_proxies)}")
print(Fore.CYAN + f"Total proxies successful (http): {len(active_http_proxies)}")

print(Fore.CYAN + f"\nTotal informasi proxies checked (socks4): {len(socks4_proxies)}")
print(Fore.CYAN + f"Total proxies successful (socks4): {len(active_socks4_proxies)}")

print(Fore.CYAN + f"\nTotal informasi proxies checked (socks5): {len(socks5_proxies)}")
print(Fore.CYAN + f"Total proxies successful (socks5): {len(active_socks5_proxies)}")

print(f"Proxies berhasil digabungkan dan disimpan ke dalam {output_file}")
