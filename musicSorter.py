import os,shutil,stat,time
def getSinger(fileName:str):
    n=fileName.rfind(" - ")
    return fileName[n+3:-4]
def forceDelete(fileName:str):
    if(not os.path.exists("./"+fileName)):
        return
    os.chmod("./"+fileName,stat.S_IRWXO+stat.S_IRWXG+stat.S_IRWXU)
    if(os.path.isdir("./"+fileName)):
        shutil.rmtree("./"+fileName)
        return
    os.remove("./"+fileName)

# 引用于 https://blog.csdn.net/orangefly0214/article/details/81385405
def all_list(arr):
    result = {}
    for i in set(arr):
        result[i] = arr.count(i)
    return result

f=open("music.txt","r")
content=f.readlines()
f.close()
folder=content[0][0:-1]
newFolder=content[1][0:-1]
singerNum=int(content[2][0:-1])
folderLeastNum=int(content[3][0:-1])
if(content[singerNum+3][-1]!="\n"):
    content[singerNum+3]=content[singerNum+3]+"\n"
singer=[]
for i in range(4,4+singerNum):
    singer.append(content[i][:-1])
musics=os.listdir("./"+folder)
tmp=[]
for i in range(0,len(musics)):
    if(musics[i].find(" - ")>=0 and (musics[i][-4:]==".mp3" or musics[i][-4:]==".m4a")):
        tmp.append(musics[i])
musics=tmp
musicNum=len(tmp)
print("音乐文件数量: "+str(musicNum))
isCopied=[]
for i in range(0,len(musics)):
    isCopied.append(False)
os.chmod(".",stat.S_IRWXO+stat.S_IRWXG+stat.S_IRWXU)
forceDelete(newFolder)
time.sleep(2)
os.chmod(".",stat.S_IRWXO+stat.S_IRWXG+stat.S_IRWXU)
os.mkdir(newFolder)
os.chmod("./"+newFolder,stat.S_IRWXO+stat.S_IRWXG+stat.S_IRWXU)
cnt=0
for i in range(0,len(singer)):
    os.mkdir("./"+newFolder+"/"+singer[i])
    curMusic=[]
    for j in range(0,musicNum):
        if(getSinger(musics[j]).find(singer[i])>=0):
            curMusic.append(j)
    print(singer[i]+": "+str(len(curMusic)))
    for j in range(len(curMusic)):
        shutil.copy("./"+folder+"/"+musics[curMusic[j]],"./"+newFolder+"/"+singer[i]+"/"+musics[curMusic[j]])
        isCopied[curMusic[j]]=True
        cnt+=1
        if(j%10==9):
            print(str(j+1)+"/"+str(len(curMusic)))
    print("finish   all: "+str(cnt)+"/"+str(musicNum))
    print("======================")
remains=[]
for i in range(0,len(musics)):
    if(isCopied[i]):
        continue
    remains.append(musics[i])
print("其它: "+str(len(remains)))
os.mkdir("./"+newFolder+"/0其它")
remainedSingers=[]
for i in range(0,len(remains)):
    remainedSingers.append(getSinger(remains[i]))
appearedTimes=all_list(remainedSingers)
singer=[]
singerNum=0
for k,v in appearedTimes.items():
    if(v>=folderLeastNum):
        singer.append(k)
        singerNum+=1
musics=remains
allMusicNum=musicNum
musicNum=len(musics)
isCopied=[]
for i in range(0,musicNum):
    isCopied.append(False)
for i in range(0,singerNum):
    os.mkdir("./"+newFolder+"/0其它/"+singer[i])
    curMusic=[]
    for j in range(0,musicNum):
        if(getSinger(musics[j]).find(singer[i])>=0):
            curMusic.append(j)
    print(singer[i]+": "+str(len(curMusic)),end="")
    for j in range(len(curMusic)):
        shutil.copy("./"+folder+"/"+musics[curMusic[j]],"./"+newFolder+"/0其它/"+singer[i]+"/"+musics[curMusic[j]])
        isCopied[curMusic[j]]=True
        cnt+=1
    print(" finish  all: "+str(cnt)+"/"+str(allMusicNum))
remains=[]
for i in range(0,len(musics)):
    if(isCopied[i]):
        continue
    remains.append(musics[i])
print("剩余: "+str(len(remains)))
for i in range(0,len(remains)):
    shutil.copy("./"+folder+"/"+remains[i],"./"+newFolder+"/0其它/"+remains[i])
    cnt+=1
    if(i%10==9):
        print(str(i+1)+"/"+str(len(remains))+"   all: "+str(cnt)+"/"+str(allMusicNum))
print("Finish")
