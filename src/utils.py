import os
import json
from typing import List
from socket import socket
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


SERVER_IP_ADDRESS = os.environ['SERVER_IP_ADDRESS']
SERVER_PORT = os.environ['SERVER_PORT']

LOBBY_TIMEOUT = 30

INITIAL_BOARD = [
    [' ', ' ', ' '],
    [' ', ' ', ' '],
    [' ', ' ', ' '],
]


@dataclass
class Lobby:
    lobby_socket: socket
    name: str
    board: list
    players: List[str] = None
    players_sockets: List[socket] = None
    players_chars: dict = dict


def dict_to_bytes(d: dict) -> bytes:
    return bytes(json.dumps(d), encoding='utf-8')


def bytes_to_dict(b: bytes) -> dict:
    return json.loads(str(b, encoding='utf-8'))
