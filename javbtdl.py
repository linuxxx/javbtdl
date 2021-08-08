#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import requests
import json
import sqlite3
import threading
import os
import ctypes,sys
'''
javbtdl.com
启动后程序会自动更新数据库
'''
date = []
title = []
actress = []
magnet = []
ulist = []
tt = 0 #数据库中最新数据的时间
num = ""#数据库总条目

baseurl = "https://www.javbtdl.com"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def getdata(num):
    try:
        global date,title,actress,magnet,ulist
        referer = str(ulist[num]).replace("\n","")
        if referer == "":
            return
        url = referer.replace("https://www.javbtdl.com/","https://www.javbtdl.com/assets/data/")+"index.json"
        hdr= {
            "referer": referer,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        }
        
        res = requests.get(url,headers=hdr).json()
        temp = res['data']['posts']['belongsTo']['edges']
        vlen = len(temp)
        i = 0
        while i < vlen:
            title.append(temp[i]['node']['title']) #标题
            try:
                actress.append(temp[i]['node']['actress'][0]['title'])#演员
            except:
                actress.append("")
                pass 
            date.append(temp[i]['node']['date'][0]['date']) #日期
            magnet.append(temp[i]['node']['magnet'])#磁力
            i += 1
    except:
        print("更新数据获取异常!")
        pass

        
'''
导入数据库
'''

def uniqrow():
    try:
        print("数据库去重...")
        con = sqlite3.connect("javbtdl.db")
        cur = con.cursor()
        sql2 = '''delete from tb_javbtdl where tb_javbtdl.rowid not in (select MAX(tb_javbtdl.rowid) from tb_javbtdl group by title)'''
        cur.execute(sql2)    
        con.commit()
        cur.close()
        con.close()
    except:
        print("数据库去重复异常!")
        pass
        
def InsertToDatabase():
    print("正在更新数据库")
    global date,title,actress,magnet
    con = sqlite3.connect("javbtdl.db")
    cur = con.cursor()
    sql = '''CREATE TABLE IF NOT EXISTS tb_javbtdl(id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT,title TEXT,actress TEXT,magnet TEXT)'''
    cur.execute(sql)    
    i = len(magnet)-1 
    while i > -1:
        cur.execute("INSERT INTO tb_javbtdl(date,title,actress,magnet)values(?,?,?,?)",(date[i],title[i],actress[i],magnet[i]))
        i -= 1
    #执行插入操作后需要提交数据插入才能生效
    con.commit()
    cur.close()
    con.close()
    print("数据库导入完成")
    
    


#创建表
#sql = '''CREATE TABLE IF NOT EXISTS tb_javbtdl(id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT,title TEXT,actress TEXT,magnet TEXT)'''
#cur.execute(sql)

#getdata()
#InsertToDatabase()
def search():
    global num
    con = sqlite3.connect("javbtdl.db")
    cur = con.cursor()    
    sql = "select count(id) from tb_javbtdl"
    res = cur.execute(sql)
    num = str(res.fetchall()[0]).replace(",","")
    while True:
        print("当前数据库总条目:"+str(num))
        key = input("输入番号:")
        if key == "":
            continue
        key = key.upper()
        if "-" in str(key):
            key = str(key).replace("-","")
        sql = "select * from tb_javbtdl where title like "+"\'%"+str(key)+"%\'"+" or date like "+"\'%"+str(key)+"%\'"+" or actress like "+"\'%"+str(key)+"%\'"
        res = cur.execute(sql)
        data = res.fetchall()
        print("时间\t\t\t番号\t\t演员\t\t\t磁力链接")
        for i in data:
            print("%s|%s|%s%s" %(str(i[1]).ljust(20),str(i[2]).ljust(15),str(i[3]).ljust(22," "),str(i[4]).center(100)))




def getulist(num):
    global ulist,prelist
    r = requests.get(prelist[num])
    temp = r.text.split("<div class=\"mb-5\"><a href=\"")
    i = 1
    print("第"+str(num)+"页")
    while i < len(temp):
        print(baseurl+str(temp[i].split("\"")[0]))
        ulist.append(baseurl+str(temp[i].split("\"")[0]))
        i += 1

'''
多线程获取二级列表
'''
#def MT_ulist():
    #global ulist
    #for i in range(0,149):
        #thread = threading.Thread(target=getulist,args=(i,))
        #thread.start()
        #thread.join()
    #f = open("ulist.txt","a",encoding="utf-8")
    #for i in ulist:
        #f.write(i+"\n")
    #f.close()
    #print("下载完成!")
    

    
    
def MT_getdata():
    global ulist
    for i in range(0,len(ulist)):
        thread = threading.Thread(target=getdata,args=(i,))
        thread.start()
        thread.join()
    print("磁力链接抓取完成!")

    
    
#def getDate_from_ulist():
    #global ulist
    #with open("ulist.txt","r",encoding="utf-8") as f:
        #ulist = list(f)
        #f.close()    
    #MT_getdata()
    #InsertToDatabase()
    



def getjav(url):
    global ulist,tt,baseurl
    tl = []
    ulist_ = []
    r = requests.get(url)
    temp = r.text.split("<div class=\"mb-5\"><a href=\"")
    i = 1
    while i < len(temp):
        #print(baseurl+str(temp[i].split("\"")[0]))
        ulist_.append(baseurl+str(temp[i].split("\"")[0]))
        tl.append(str(temp[i].split("<h1 class=\"text-4xl font-bold\">")[1].split("<p")[0]).strip())
        i += 1
    for j in tl:
        ttt = int(j.replace("/",""))
        if tt < ttt:
            ulist.append(ulist_[tl.index(j)])
            
        
    
    
    
def checkUpdate():
    '''
    获取数据库中最新数据的时间戳
    '''
    try:
        print("正在检查更新...")
        global tt,baseurl,ulist
        con = sqlite3.connect("javbtdl.db")
        cur = con.cursor()
        sql = "select date from tb_javbtdl order by id desc limit 1"
        res = cur.execute(sql)
        t = str(res.fetchall()[0]).replace("\',)","").replace("(\'","")
        cur.close()
        con.close()
        tt = int(t.replace("/","")) #数据库最新时间戳
        r = requests.get("https://www.javbtdl.com/jav/")
        temp = r.text.split("<div class=\"mb-5\"><a href=\"")
        ttt_ = str(temp[1].split("<h1 class=\"text-4xl font-bold\">")[1].split("<p")[0]).strip()
        ttt = int(ttt_.replace("/",""))
        n = int((ttt-tt)/6)
        if tt < ttt and n == 0:
            print("正在更新数据...")
            tl = []
            ulist_ = []
            i = 1
            while i < len(temp):
                #print(baseurl+str(temp[i].split("\"")[0]))
                ulist_.append(baseurl+str(temp[i].split("\"")[0]))
                tl.append(str(temp[i].split("<h1 class=\"text-4xl font-bold\">")[1].split("<p")[0]).strip())
                i += 1
            for j in tl:
                ttt = int(j.replace("/",""))
                if tt < ttt:
                    ulist.append(ulist_[tl.index(j)])        
            MT_getdata()
            InsertToDatabase()        
        elif tt < ttt and n > 0:
            print("正在更新数据_...")
            prelist = []
            for j in range(0,n):
                if j == 0:
                    prelist.append("https://www.javbtdl.com/jav/")
                else:
                    prelist.append("https://www.javbtdl.com/jav/"+str(j+1)+"/")
            
            for u in prelist:
                getjav(u)
            MT_getdata()      
            InsertToDatabase()
        else:
            print("数据更新完成!")
    except:
        print("资源更新异常!")
        pass

            
        
def check_server_enable():
    url = "https://www.javbtdl.com/"
    try:
        r = requests.get(url)
    except:
        print("网站故障,切换到离线模式")
        return False            
    if str(r.text.split("\"text-3xl md:text-4xl font-semibold\">")[1].split("</h1>")[0]).strip() == "Most Downloaded":
        print("网站运行正常")
        return True
    else:
        print("网站故障,切换到离线模式")
        return False

    
if __name__ == '__main__':
    
    if check_server_enable():
        uniqrow()
        checkUpdate()
        search()        
        #if is_admin():
            #checkUpdate()
            #search()
        #else:
            #ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    else:
        while True:
            search()

'''
2021/01/26	|	SNKH008	|	笹倉杏	|	magnet:?xt=urn:btih:2IVLLWACAXEVWHEOXBCGZUA7DUGMRULV&dn=SNKH-008.mp4
'''

    
