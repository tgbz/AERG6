import threading, json

class gameGenerator():
    def __init__(self, rounds):
        threading.Thread.__init__(self)
        self.songsDB = "assets/songlist.json" #path para o ficheiro de musicas
        self.songList = json.load(open(self.songDB)) # carrega o ficheiro de musicas
        self.currentGamePlayers = dict() #dicionario com os jogadores desse jogo
        self.gameRounds = rounds #número de rondas do jogo
        self.selectedSongs = dict()
        self.gameOptions = dict()  
    """
        Iterar sobre a lista de musicas disponivel na base de dados e escolher
            <self.gameRounds> músicas aleatórias
            devolvendo um dicionario com as musicas escolhidas com o seguinte formato:
                {
                 "id": {
                     "title": <title>,
                     "artist": <artist>
                 },
                 "id" : {
                        "title": <title>,
                        "artist": <artist>
                }
                ...
                } 
    """
    def chooseSongs(self):
        for i in range(self.gameRounds):
            song = self.songList[i]
            self.selectedSongs[i]["title"] = song["title"]
            self.selectedSongs[i]["artist"] = song["artist"]
            self.selectedSongs[i]["filePath"] = song["filePath"]
        print("Musicas escolhidas para jogo: ", self.selectedSongs)

    """
    Função responsável por iterar a self.selectedSongs e a cada iteração
        procurar na self.songList outras 3 músicas aleatórias que não sejam
        as que já foram escolhidas, adicionando ao self.gameOptions no seguinte formato:
            {
                "r1": {
                    "id": {
                        "title": <title>,
                        "artist": <artist>
                    },
                    "id": {
                        "title": <title>,
                        "artist": <artist>
                    ...
                    },
                "r2": {
                    "id": {
                        "title": <title>,
                        "artist": <artist>
                    },
                    "id": {
                        "title": <title>,
                        "artist": <artist>
                    ...
                    
                }

    """
    def getOptionsForSongs(self):
        for round in self.selectedSongs:
            for i in range(3):
                song = self.songList[i]
                if song not in self.selectedSongs[round]:
                    self.gameOptions[round][i]["title"] = song["title"]
                    self.gameOptions[round][i]["artist"] = song["artist"]
        print("Opções para as musicas escolhidas: ", self.gameOptions)
    
    def generateGame(self):
        self.chooseSongs()
        self.getOptionsForSongs()
        return self.gameOptions()