import copy
import random
from threading import Thread
from socket import AF_INET, SOCK_STREAM

from utils import *


def check_for_winner(board):
    # Check horizontals
    for i in range(3):
        if board[i] in [['X', 'X', 'X'], ['0', '0', '0']]:
            return board[i][0]

    # Check verticals
    for i in range(3):
        if [board[j][i] for j in range(3)] in [['X', 'X', 'X'], ['0', '0', '0']]:
            return board[0][i]

    # Check diagonals
    if [board[0][0], board[1][1], board[2][2]] in [['X', 'X', 'X'], ['0', '0', '0']] \
            or [board[2][0], board[1][1], board[0][2]] in [['X', 'X', 'X'], ['0', '0', '0']]:
        return board[1][1]

    return False


def process_players_turns(curr_lobby, turn, lobbies):
    while True:
        player_number = int(not turn)
        data = bytes_to_dict(
            curr_lobby.players_sockets[player_number].recv(1024)
        )

        curr_cell_id = 1
        for i, row in enumerate(curr_lobby.board):
            for j, col in enumerate(row):
                if curr_cell_id == data['cell']:
                    curr_lobby.board[i][j] = data['game_char']
                curr_cell_id += 1

        winner = check_for_winner(curr_lobby.board)

        curr_lobby.players_sockets[0].send(dict_to_bytes({'board': curr_lobby.board, 'winner': winner}))
        curr_lobby.players_sockets[1].send(dict_to_bytes({'board': curr_lobby.board, 'winner': winner}))
        if winner is not False:
            lobbies.pop(curr_lobby.name)
            return None

        turn = not turn


def run_lobby(lobby_socket: socket, lobby_name, lobbies: dict[str, Lobby]):
    curr_lobby = lobbies[lobby_name]

    # Start awaiting second player connection
    accepted_socket = lobby_socket.accept()[0]

    data = bytes_to_dict(accepted_socket.recv(1024))

    curr_lobby.players.append(data.get('username'))
    curr_lobby.players_sockets.append(accepted_socket)

    turn = random.choice([True, False])
    curr_lobby.players_chars.update({
        'X': curr_lobby.players_sockets[0 if turn else 1],
        '0': curr_lobby.players_sockets[1 if turn else 0]
    })

    curr_lobby.players_sockets[0].send(dict_to_bytes({'board': curr_lobby.board, 'your_turn': turn}))
    curr_lobby.players_sockets[1].send(dict_to_bytes({'board': curr_lobby.board, 'your_turn': not turn}))

    process_players_turns(curr_lobby, turn, lobbies)


def create_new_lobby(lobbies, lobby_name, player_socket, username):
    lobby_socket = socket(AF_INET, SOCK_STREAM)
    lobby_socket_port = random.randint(11_000, 12_000)
    lobby_socket.bind((SERVER_IP_ADDRESS, lobby_socket_port))
    lobby_socket.listen()

    player_socket.send(dict_to_bytes({'new_lobby_port': lobby_socket_port}))
    accepted_socket = lobby_socket.accept()[0]

    lobbies.update({
        lobby_name: Lobby(
                lobby_socket=lobby_socket,
                name=lobby_name,
                board=copy.deepcopy(INITIAL_BOARD),
                players=[username],
                players_sockets=[accepted_socket],
            )
    })

    Thread(target=run_lobby, args=(lobby_socket, lobby_name, lobbies)).start()


def join_lobby(lobbies: dict[str, Lobby], player_socket):
    while True:
        lobbies_dict = {
            lobby_name: lobby.lobby_socket.getsockname()[1]
            for lobby_name, lobby in lobbies.items()
            if len(lobby.players) < 2
        }
        player_socket.send(dict_to_bytes(lobbies_dict))
        data = bytes_to_dict(player_socket.recv(1024))
        if data['action'] == 'refresh_lobbies':
            continue


def process_player_session(player_socket, lobbies):
    try:
        data = bytes_to_dict(player_socket.recv(1024))
    except json.decoder.JSONDecodeError:
        # Player's session has been closed
        return

    action = data.get('action')

    if action == 'create':
        create_new_lobby(lobbies, data.get('lobby_name'), player_socket, data.get('username'))
    elif action == 'join':
        join_lobby(lobbies, player_socket)


def start_accepting_hosts(lobbies):
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((SERVER_IP_ADDRESS, int(SERVER_PORT)))
    server_socket.listen()
    while True:
        accepted_data = server_socket.accept()
        accepted_socket = accepted_data[0]

        Thread(target=process_player_session, args=(accepted_socket, lobbies)).start()


def run():
    print('Server is running...')
    lobbies = {}
    start_accepting_hosts(lobbies)


if __name__ == '__main__':
    run()
