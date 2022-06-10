import threading, json

class mainServer():
    def __init__(self, rounds):
        self.connectedClients = dict()
        