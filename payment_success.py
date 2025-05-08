import serial
import csv
import os
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

CSV_BALANCES = "rfid_balances.csv"
CSV_RECORDS = "parking_records.csv"
DEFAULT_BALANCE = 500.00
MINIMUM_CHARGE = 100


def print_header(message):
    print(f"\n{Fore.CYAN}{'=' * 50}")
    print(f"{Fore.CYAN}{message.center(50)}")
    print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")


def initialize_files():
    if not os.path.exists(CSV_BALANCES):
        with open(CSV_BALANCES, 'w', newline='') as f:
            f.write("UID,Balance\n")
    if not os.path.exists(CSV_RECORDS):
        with open(CSV_RECORDS, 'w', newline='') as f:
            f.write("UID,EntryTime,ExitTime,Paid,Amount\n")


def calculate_charge(entry_time):
    exit_time = datetime.now()
    duration = exit_time - entry_time
    minutes = duration.total_seconds() / 60

    if minutes <= 30:
        return MINIMUM_CHARGE
    return MINIMUM_CHARGE + 100 * ((minutes - 30) // 30 + 1)


def handle_rfid(uid):
    balances = []
    current_balance = DEFAULT_BALANCE
    exists = False

    # Load balances
    with open(CSV_BALANCES, 'r') as f:
        reader = csv.DictReader(f)
        balances = list(reader)
        for row in balances:
            if row['UID'] == uid:
                current_balance = float(row['Balance'])
                exists = True
                break

    # Handle new cards
    if not exists:
        balances.append({'UID': uid, 'Balance': str(DEFAULT_BALANCE)})
        current_balance = DEFAULT_BALANCE
        print_header("NEW CARD REGISTERED")
        print(f"{Fore.GREEN}│ UID: {uid}")
        print(f"{Fore.GREEN}│ Initial Balance: {DEFAULT_BALANCE} units")
        print(f"{Fore.GREEN}└──────────────────────────────────────────────────")

    records = []
    entry_found = False
    charge = 0
    duration = None

    # Process parking records
    with open(CSV_RECORDS, 'r') as f:
        reader = csv.DictReader(f)
        records = list(reader)

        for record in reversed(records):
            if record['UID'] == uid and record['Paid'] == '0':
                entry_time = datetime.strptime(record['EntryTime'], "%Y-%m-%d %H:%M:%S")
                exit_time = datetime.now()
                duration = exit_time - entry_time
                charge = calculate_charge(entry_time)

                # Update balance
                new_balance = current_balance - charge
                for b in balances:
                    if b['UID'] == uid:
                        b['Balance'] = str(new_balance)

                # Update record
                record['ExitTime'] = exit_time.strftime("%Y-%m-%d %H:%M:%S")
                record['Paid'] = '1'
                record['Amount'] = str(charge)
                entry_found = True

                # Print payment details
                print_header("PAYMENT PROCESSED")
                print(f"{Fore.YELLOW}│ UID: {uid}")
                print(f"{Fore.YELLOW}│ Entry Time: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{Fore.YELLOW}│ Exit Time: {exit_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{Fore.YELLOW}│ Duration: {str(duration).split('.')[0]}")
                print(f"{Fore.YELLOW}│ Charge: {charge} units")
                print(f"{Fore.YELLOW}│ Remaining Balance: {new_balance} units")
                print(f"{Fore.YELLOW}└──────────────────────────────────────────────────")
                break

    if not entry_found:
        records.append({
            'UID': uid,
            'EntryTime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'ExitTime': '',
            'Paid': '0',
            'Amount': ''
        })
        print_header("ENTRY LOGGED")
        print(f"{Fore.BLUE}│ UID: {uid}")
        print(f"{Fore.BLUE}│ Current Balance: {current_balance} units")
        print(f"{Fore.BLUE}│ Entry Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.BLUE}└──────────────────────────────────────────────────")

    # Save updates
    with open(CSV_BALANCES, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['UID', 'Balance'])
        writer.writeheader()
        writer.writerows(balances)

    with open(CSV_RECORDS, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['UID', 'EntryTime', 'ExitTime', 'Paid', 'Amount'])
        writer.writeheader()
        writer.writerows(records)

    return entry_found


def main():
    initialize_files()
    print_header("RFID PARKING SYSTEM STARTED")

    try:
        ser = serial.Serial('COM7', 9600, timeout=1)
        print(f"\n{Fore.CYAN}System ready. Waiting for RFID cards...{Style.RESET_ALL}")

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                if line.startswith('CARD_UID:'):
                    uid = line.split(':')[1].upper()
                    is_exit = handle_rfid(uid)
                    response = b"SUCCESS\n" if is_exit else b"ENTRY_LOGGED"
                    ser.write(response)

    except KeyboardInterrupt:
        ser.close()
        print_header("SYSTEM SHUTDOWN")


if __name__ == "__main__":
    main()