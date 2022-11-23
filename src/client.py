import time
from socket import AF_INET, SOCK_STREAM

from utils import *


# REMOTE_SERVER_IP_ADDRESS = '127.0.0.1'
REMOTE_SERVER_IP_ADDRESS = '3.89.207.99'
REMOTE_SERVER_PORT = 7999


def clear_screen():
    os.system('cls')


def print_board(board):
    for i, row in enumerate(board):
        for j, col in enumerate(row):
            print(f'   {col}   ', end='|' if j < len(row) - 1 else '\n')
        if i < len(row) - 1:
            print('-' * (len(board)*7 + len(board) - 1))


def get_available_cells(board):
    empty_cells_indexes = []
    curr_cell_id = 1
    for row in board:
        for col in row:
            if col == ' ':
                empty_cells_indexes.append(curr_cell_id)
            curr_cell_id += 1
    return empty_cells_indexes


def choose_cell(board):
    while True:
        cell = int(input("\n Choose the cell(1-9 places as keys on cellphone): "))

        if cell in list(range(1, 10)) and cell in get_available_cells(board):
            return cell
        clear_screen()
        print_board(board)
        print(f'Cell #{cell} is not empty! Choose empty one!')


def play(username, lobby_socket, board, your_turn):
    clear_screen()
    print_board(board)
    game_char = 'X' if your_turn else '0'
    while True:
        if your_turn:
            cell = choose_cell(board)

            lobby_socket.send(dict_to_bytes(
                {'cell': cell, 'game_char': game_char}
            ))
        else:
            print('\n Wait on your turn...')
        data = bytes_to_dict(lobby_socket.recv(1024))
        board = data['board']

        clear_screen()
        print_board(board)
        if data['winner'] is not False:
            result = 'You won!' if game_char == data['winner'] else 'You lost. Try again.'
            print('\n', result)
            input("\n\nEnter anything to got back to Menu: ")

            break
        your_turn = not your_turn

    # Cleanup
    lobby_socket.close()

    open_menu(username)


def host_lobby(username, server_socket, lobby_socket):
    lobby_name = input('Enter name for lobby: ')
    request_data = dict_to_bytes({'action': 'create', 'lobby_name': lobby_name, 'username': username})
    server_socket.send(request_data)

    data = bytes_to_dict(server_socket.recv(1024))
    lobby_socket_port = data['new_lobby_port']

    lobby_socket.connect((REMOTE_SERVER_IP_ADDRESS, lobby_socket_port))

    print(f'Start awaiting for a second player... ({int(lobby_socket.timeout)} seconds)')
    return lobby_socket


def join_lobby(username, server_socket, lobby_socket):
    while True:
        clear_screen()
        request_data = dict_to_bytes({'action': 'join'})
        server_socket.send(request_data)

        lobbies_dict = bytes_to_dict(server_socket.recv(1024))
        print('List of available lobbies:')
        if len(lobbies_dict.items()) != 0:
            for name in lobbies_dict.keys():
                print(f'\t{name}')
        else:
            print('(found 0 active lobbies)')

        lobby_name = input('\n Enter name of lobby to join it: ')
        if lobbies_dict.get(lobby_name, None) is not None:
            break
        else:
            choice = input('\nYou misspelled a lobby name or entered no existing one!\n'
                           '\n1. Refresh lobbies list and choose again '
                           '\n2. Go to Menu\n'
                           'Choose your option: ')
            if choice == '1':
                continue
            elif choice == '2':
                return False

    lobby_socket.connect((REMOTE_SERVER_IP_ADDRESS, lobbies_dict.get(lobby_name)))
    lobby_socket.send(dict_to_bytes({'username': username}))
    return lobby_socket


def open_menu(username: str):
    server_socket = socket(AF_INET, SOCK_STREAM)
    while True:
        try:
            print(' Trying to connect to the remote server...')
            server_socket.connect((REMOTE_SERVER_IP_ADDRESS, REMOTE_SERVER_PORT))
            break
        except ConnectionRefusedError:
            print(' Server is still down... Pause before next try... ')
            time.sleep(3)
            clear_screen()

    lobby_socket = socket(AF_INET, SOCK_STREAM)
    lobby_socket.settimeout(LOBBY_TIMEOUT)

    entered_wrong_option = False
    while True:
        clear_screen()
        c = input(
            f"1. Create lobby\n"
            f"2. Join lobby\n"
            f"3. Exit\n\n"
            f"{'You have chosen a not existing option' if entered_wrong_option else ''}"
            f"Choose your option: "
        )

        if c == '1':
            lobby_socket = host_lobby(username, server_socket, lobby_socket)
            break
        elif c == '2':
            result = join_lobby(username, server_socket, lobby_socket)
            if result is not False:
                lobby_socket = result
                break
            else:
                return open_menu(username)
        elif c == '3':
            clear_screen()
            return
        else:
            entered_wrong_option = True

    data = None
    received_data = False
    while True:
        try:
            data = bytes_to_dict(lobby_socket.recv(1024))
            received_data = True
            break
        except TimeoutError:
            clear_screen()
            print(f' No players joined the room in last {int(lobby_socket.timeout)}  seconds.\n')
            c = input(f' Enter 1, if you want to keep awaiting(for another {int(lobby_socket.timeout)} seconds),'
                      '\n otherwise enter any key to go to Menu: ')
            if c == '1':
                clear_screen()
                print(f'Keep awaiting for a second player... ({int(lobby_socket.timeout)} seconds)')
                continue
            else:
                break

    if received_data:
        play(username, lobby_socket, data['board'], data['your_turn'])
    else:
        open_menu(username)


def main():
    clear_screen()
    username = input('\nEnter your username: ')
    clear_screen()
    while True:
        try:
            open_menu(username)
            break
        except ConnectionResetError:
            clear_screen()
            print(' Remote server is down. Trying to reconnect...')


if __name__ == '__main__':
    main()
