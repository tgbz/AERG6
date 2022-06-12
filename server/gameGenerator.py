import threading, json, random, pprint, re

class gameGenerator():
    def __init__(self, rounds):
        self.songsDB = "../common/songlist.json" #path para o ficheiro de musicas
        self.songList = json.load(open(self.songsDB)) # carrega o ficheiro de musicas
        self.gameRounds = rounds #número de rondas do jogo
        self.gameOptions = ""
    def shuffleGame(self, d):
        temp = list(d.values())
        random.shuffle(temp)
        res = dict(zip(d, temp))
        return res
    
    #menu-r1$id$id$id$id-r2$id$id$id$id-r3$id$id$id$id-sols%id
    def getOptionsForSongs(self):
        self.gameOptions += "menu-"
        songsAvailable = []
        for i in range(self.gameRounds):
            self.gameOptions += "r" + str(i+1)
            tmp = []
            for j in range(4):
                #add 4 random songs to tmp, with no duplicates selected based on thr id of self.songList
                while True:
                    song = random.randint(1, len(self.songList))
                    if song not in tmp:
                        tmp.append(song)
                        break
                self.gameOptions += "$" + str(tmp[j])
            songsAvailable.append(tmp)
            self.gameOptions += "-"
        self.gameOptions += "sols-"
        for i in range(self.gameRounds):
            #select random item from songsAvailable[i]
            self.gameOptions += "%" + str(songsAvailable[i][random.randint(0,3)])
        return self.gameOptions
    

       
    def generateMenu(self):
        rs = self.gameOptions
        opts = []
        solutions = []
        for g in re.findall(r'r\d((\$\d){4})',self.gameOptions):
            opts.append(g[0].split('$')[1:])
        print(opts)
        print(len(opts))
        for sols in re.findall(r'((\%\d){'+str(len(opts))+'})',self.gameOptions):
            #print(sols[0].split('%')[1:])
            solutions = sols[0].split('%')[1:]
        print(solutions) 
def main():
    gg = gameGenerator(3)
    gg.getOptionsForSongs()
    gg.generateMenu()

if __name__ == "__main__":
    main()