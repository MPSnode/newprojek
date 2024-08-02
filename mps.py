import os
import serial
import serial.tools.list_ports
import threading
import logging
import time
from colorama import Fore, Style, init
import tkinter as tk
from tkinter import simpledialog, messagebox
import sqlite3
from cryptography.fernet import Fernet
from flask import Flask, render_template
import sys

# Inisialisasi colorama
init(autoreset=True)

# Pengaturan logging
logging.basicConfig(filename='sms_log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Inisialisasi database
conn = sqlite3.connect('sms_data.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                  (id INTEGER PRIMARY KEY, number TEXT, message TEXT, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# Generate encryption key and cipher suite
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Fungsi untuk mengenkripsi pesan
def encrypt_message(message):
    encrypted_message = cipher_suite.encrypt(message.encode())
    return encrypted_message

# Fungsi untuk mendekripsi pesan
def decrypt_message(encrypted_message):
    decrypted_message = cipher_suite.decrypt(encrypted_message).decode()
    return decrypted_message

# Fungsi untuk validasi nomor telepon
def validate_phone_number(number):
    return number.isdigit() and len(number) >= 10

# Fungsi untuk validasi pesan
def validate_message(message):
    return 0 < len(message) <= 160

# Fungsi untuk mengecek saldo/kredit pada kartu SIM
def check_balance(device):
    try:
        # Implementasi cek saldo tergantung pada perangkat dan operator
        # Misalnya, menggunakan perintah AT untuk modem GSM:
        # device.send_command('AT+CUSD=1,"*123#",15')
        # Kode berikut adalah simulasi:
        balance = "Rp10.000"  # Contoh hasil cek saldo
        print(Fore.GREEN + f"Sisa saldo: {balance}")
        return balance
    except Exception as e:
        print(Fore.RED + "Gagal mengecek saldo:", e)
        return None

# Fungsi untuk menampilkan menu utama
def main_menu():
    print(Fore.GREEN + "="*50)
    print(Fore.GREEN + " WELCOME TO SMS SENDER CLI ".center(50, "="))
    print(Fore.GREEN + "="*50)
    print(Fore.GREEN + "Silakan pilih jenis perangkat yang akan digunakan:")
    print(Fore.GREEN + "[1] PONSEL")
    print(Fore.GREEN + "[2] MODEM")
    print(Fore.GREEN + "[3] KELUAR")
    print(Fore.GREEN + "="*50)
    choice = input(Fore.GREEN + "Masukkan pilihan Anda (1/2/3): ")

    if choice == "1":
        device_menu_cli("PONSEL")
    elif choice == "2":
        device_menu_cli("MODEM")
    elif choice == "3":
        print(Fore.GREEN + "Terima kasih telah menggunakan layanan kami. Sampai jumpa!")
        exit()
    else:
        print(Fore.RED + "Pilihan tidak valid. Silakan coba lagi.")
        main_menu()

# Fungsi untuk menampilkan menu perangkat (ponsel atau modem) dalam CLI
def device_menu_cli(device_type):
    while True:
        print("\n" + Fore.GREEN + "="*50)
        print(Fore.GREEN + f"MENU {device_type}".center(50))
        print(Fore.GREEN + "="*50)
        print(Fore.GREEN + "Silakan pilih aksi:")
        print(Fore.GREEN + "[1] SCAN PERANGKAT")
        print(Fore.GREEN + "[2] KIRIM PESAN")
        print(Fore.GREEN + "[3] CEK SALDO")
        print(Fore.GREEN + "[4] KEMBALI")
        print(Fore.GREEN + "="*50)
        choice = input(Fore.GREEN + "Masukkan pilihan Anda (1/2/3/4): ")

        if choice == "1":
            scan_devices(device_type)
        elif choice == "2":
            send_menu_cli(device_type)
        elif choice == "3":
            # Cek saldo/kredit
            check_balance(device_type)
        elif choice == "4":
            main_menu()
        else:
            print(Fore.RED + "Pilihan tidak valid. Silakan coba lagi.")

# Fungsi untuk memindai perangkat USB yang terhubung
def scan_devices(device_type):
    logging.info(f"Memindai perangkat {device_type}...")
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print(Fore.RED + f"Tidak ada perangkat {device_type} yang terdeteksi.")
        return

    for port in ports:
        device_info = f"{port.device} - {port.description}"
        print(Fore.GREEN + f"Perangkat ditemukan: {device_info}")
        logging.info(f"Perangkat ditemukan: {device_info}")
        print(Fore.GREEN + f"DEVICE: {device_type}")
        print(Fore.GREEN + f"INFO DEVICE: {port.description}")
        print(Fore.GREEN + "INFO PROVIDER: Nama Provider (contoh data)")
        print(Fore.GREEN + "INFO BALANCE: Sisa Pulsa (contoh data)")

# Fungsi untuk mengatur dan mengirim pesan (CLI)
def send_menu_cli(device_type):
    message = ""
    numbers = []

    while True:
        print("\n" + Fore.GREEN + "="*50)
        print(Fore.GREEN + "PENGATURAN PESAN".center(50))
        print(Fore.GREEN + "="*50)
        print(Fore.GREEN + "Silakan pilih aksi:")
        print(Fore.GREEN + "[1] SET PESAN")
        print(Fore.GREEN + "[2] SET NOMOR")
        print(Fore.GREEN + "[3] MULAI KIRIM")
        print(Fore.GREEN + "[4] KEMBALI")
        print(Fore.GREEN + "="*50)
        choice = input(Fore.GREEN + "Masukkan pilihan Anda (1/2/3/4): ")

        if choice == "1":
            message = input(Fore.GREEN + "Masukkan pesan: ")
            if validate_message(message):
                with open("message.txt", "w") as f:
                    f.write(message)
            else:
                print(Fore.RED + "Pesan tidak valid. Pastikan tidak kosong dan tidak lebih dari 160 karakter.")
        elif choice == "2":
            number = input(Fore.GREEN + "Masukkan nomor (pisahkan dengan koma untuk banyak nomor): ")
            numbers = [num.strip() for num in number.split(',') if validate_phone_number(num.strip())]
            with open("numbers.txt", "w") as f:
                for num in numbers:
                    f.write(num + "\n")
            if not numbers:
                print(Fore.RED + "Nomor tidak valid. Pastikan formatnya benar dan setidaknya 10 digit.")
        elif choice == "3":
            if not message or not numbers:
                print(Fore.RED + "Pesan atau nomor belum diset.")
            else:
                encrypted_message = encrypt_message(message)
                thread = threading.Thread(target=send_message_with_retry, args=(device_type, encrypted_message, numbers))
                thread.start()
        elif choice == "4":
            device_menu_cli(device_type)
        else:
            print(Fore.RED + "Pilihan tidak valid. Silakan coba lagi.")

# Fungsi untuk mengirim pesan ke nomor yang telah ditentukan dengan retry mechanism
def send_message_with_retry(device_type, message, numbers, retry_count=3):
    for number in numbers:
        for attempt in range(retry_count):
            try:
                # Implementasi pengiriman pesan dengan perangkat yang terhubung
                # Misalnya, menggunakan perintah AT untuk modem GSM
                time.sleep(1)  # Simulasi pengiriman
                success = True  # Ganti dengan kondisi nyata
                if success:
                    print(Fore.GREEN + f"NUMBER: {number}")
                    print(Fore.GREEN + "INFO: BERHASIL" + Style.RESET_ALL)
                    logging.info(f"Pesan ke {number} berhasil dikirim.")
                    cursor.execute("INSERT INTO messages (number, message, status) VALUES (?, ?, ?)",
                                   (number, message, "BERHASIL"))
                    break
                else:
                    raise ValueError("Simulasi error: pulsa tidak cukup atau nomor tidak valid.")
            except Exception as e:
                print(Fore.RED + f"NUMBER: {number}")
                print(Fore.RED + "INFO: GAGAL" + Style.RESET_ALL)
                print(Fore.RED + f"KET: {str(e)} (percobaan {attempt + 1} dari {retry_count})" + Style.RESET_ALL)
                logging.error(f"Pesan ke {number} gagal: {str(e)}")
                if attempt == retry_count - 1:
                    cursor.execute("INSERT INTO messages (number, message, status) VALUES (?, ?, ?)",
                                   (number, message, f"GAGAL: {str(e)}"))
    conn.commit()

# Fungsi untuk menjadwalkan pengiriman pesan
def schedule_message(device_type, message, numbers, send_time):
    # Konversi waktu pengiriman ke detik dari waktu sekarang
    delay = send_time - time.time()
    if delay > 0:
        time.sleep(delay)
    send_message_with_retry(device_type, message, numbers)

# Inisialisasi Flask untuk dashboard pemantauan
app = Flask(__name__)

@app.route('/')
def index():
    conn = sqlite3.connect('sms_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages")
    messages = cursor.fetchall()
    conn.close()
    return render_template('index.html', messages=messages)

def run_flask_app():
    sys.stdout = open(os.devnull, 'w')  # Sembunyikan output stdout
    sys.stderr = open(os.devnull, 'w')  # Sembunyikan output stderr
    try:
        app.run(debug=False, port=5000)
    except OSError:
        print(Fore.RED + "Port 5000 sudah digunakan. Menjalankan pada port lain...")
        app.run(debug=False, port=5001)
    finally:
        sys.stdout = sys.__stdout__  # Kembalikan stdout
        sys.stderr = sys.__stderr__  # Kembalikan stderr

if __name__ == "__main__":
    # Memulai antarmuka pengguna
    threading.Thread(target=main_menu).start()
    # Menjalankan dashboard pemantauan dengan Flask
    threading.Thread(target=run_flask_app).start()
    # Menutup koneksi database
    conn.close()
