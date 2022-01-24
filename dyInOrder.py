import os
def getNumber(fileName:str):
    l=len(fileName)
    if(l<=6):
        return -1
    if(fileName[-4:]!=".mp4"):
        return -1
    loc=fileName.rfind("-")
    if(loc==-1):
        return -1
    return fileName[loc+1:-4]

def printLen(length:int,num:int):
    num=str(num)
    for i in range(0,length-len(num)):
        num="0"+num
    return num

folders=os.listdir(".")
num=0
for i in range(0,len(folders)):
    if(os.path.isdir("./"+folders[i])):
        num+=1
print("文件夹数量: "+str(num))
order=0
for i in range(0,len(folders)):
    if(not os.path.isdir("./"+folders[i])):
        continue
    order+=1
    print(folders[i],end=": ")
    videos=os.listdir("./"+folders[i])
    numbers=[]
    for j in range(0,len(videos)):
        number=getNumber(videos[j])
        if(number==-1):
            continue
        numbers.append(number)
    print(len(numbers))
    length=len(str(len(numbers)))
    numbers.sort()
    for j in range(0,len(numbers)):
        numstr=str(numbers[j])
        for k in range(0,len(videos)):
            if(videos[k].find(numstr)>=0):
                os.rename("./"+folders[i]+"/"+videos[k],"./"+folders[i]+"/"+printLen(length,j+1)+"-"+videos[k][0:videos[k].find(numstr)-1]+".mp4")
    print("finish"+"  "+str(order)+"/"+str(num))

