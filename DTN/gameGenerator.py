import threading, json, random, pprint

class gameGenerator():
    def __init__(self, rounds):
        threading.Thread.__init__(self)
        self.songsDB = "assets/songlist.json" #path para o ficheiro de musicas
        self.songList = json.load(open(self.songsDB)) # carrega o ficheiro de musicas
        self.currentGamePlayers = dict() #dicionario com os jogadores desse jogo
        self.gameRounds = rounds #número de rondas do jogo
        self.selectedSongs = dict()
        self.gameOptions = dict()  
    """
        Iterar sobre a lista de musicas disponivel na base de dados e escolher
            <self.gameRounds> músicas aleatórias
            retornando um dicionario com as musicas escolhidas com o seguinte formato:
                {
                 "id": {
                     "title": <title>,
                     "artist": <artist>
                     "filePath": <filePath>
                 },
                 "id" : {
                        "title": <title>,
                        "artist": <artist>
                }
                ...
                } 
    """
    def chooseSongs(self):
        choices = random.sample(range(1, len(self.songList)+1), self.gameRounds)
        for i in range(self.gameRounds):
            self.selectedSongs[str(choices[i])] = self.songList[str(choices[i])]
        pprint.pprint(self.selectedSongs)
        return self.selectedSongs
        
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
    
    def shuffleGame(self, d):
        temp = list(d.values())
        random.shuffle(temp)
        res = dict(zip(d, temp))
        return res
    
    def getOptionsForSongs(self):
        for i in range(self.gameRounds):
            self.gameOptions[str(i)] = dict()
            for j in range(3):
                song = self.songList[str(random.randint(1, len(self.songList)))]
                while song in self.gameOptions[str(i)].values() or song in self.selectedSongs.values():
                    song = self.songList[str(random.randint(1, len(self.songList)))]
                self.gameOptions[str(i)][str(j)] = song
        k = 0
        for song in self.selectedSongs.values():
            self.gameOptions[str(k)][str(int(self.gameRounds))] = song
            self.gameOptions [str(k)] = self.shuffleGame(self.gameOptions[str(k)])
            k += 1

        return self.gameOptions
    

    def getSongs(self):
        return self.selectedSongs
    
    def getOptions(self):
        return self.gameOptions
    
    def generateGame(self):
        self.chooseSongs()
        self.getOptionsForSongs()
    
    
def main():
    gg = gameGenerator(3)
    