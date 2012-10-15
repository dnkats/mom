#!/usr/bin/env python
import os, sys
from termcolor import colored

#default config file
rcfile="~/.momrc"
#defaults
infodir="~/.mom"
compact=0
tablen=5
color=1
colsfg="grey red green yellow blue magenta cyan white"
colsbg="on_grey on_red on_green on_yellow on_blue on_magenta on_cyan on_white"
attrs="bold dark underline blink reverse concealed"

def readrcf(rcfile):
    # read config and change defaults
    rcf=open(rcfile,'r')
#   for line in rcf:
#       print line
    rcf.close()

def ensure_dir(d):
    if not os.path.exists(d):
        print "create",d
        os.makedirs(d)

def outputhelp(fil):
    # output help file
    hf=open(fil,'r')
    for line in hf:
        if line[0]=="*":
            printline(line[2:])
            print
        else:
            print " "*tablen,
            printline(line)
            print
    hf.close()

def outputhelpcompact(fil):
    # output help file
    hf=open(fil,'r')
    for line in hf:
        if line[0]=="*":
            print line[2:-1],
        else:
            print " - ",line,
    hf.close()

savecats = dict()
savecats["cfg"]=[]
savecats["cbg"]=[]
savecats["att"]=[]
lastcmd=[]
def wordcmd(w):
    #analyse and save a command
    global savecats
    global lastcmd
    if w in colsfg:
        #save new foreground
        lastcmd.append("cfg")
    elif w in colsbg:   
        #save new background
        lastcmd.append("cbg")
    elif w in attrs:
        #add attribute
        lastcmd.append("att")
    else:
        print colored(w,"red","on_grey"),
        return
    savecats[lastcmd[-1]].append(w)

def printline(line):
    # print a line with colors and attributes
    words=line.split()
    global savecats
    global lastcmd
    for w in words:
        if w[0]!="\\":
            curcfg = savecats["cfg"][-1] if savecats["cfg"] else None
            curcbg = savecats["cbg"][-1] if savecats["cbg"] else None
            print colored(w,curcfg,curcbg,attrs=list(set(savecats["att"]))),
        elif w=="\\":
            #end
            if lastcmd:
                savecats[lastcmd.pop()].pop()
        else:
            wordcmd(w[1:])


def addhelp(fil):
    # add help from stdin
    hf=open(fil,'a')
    inp=raw_input('Topic: ')
    
    hf.write("* "+inp+"\n")
    inp=raw_input('Description: ')
    if len(inp)>0:
        hf.write(inp+"\n")
    hf.close()

def rmhelp(fil):
    # rm help from file
    print colored("Remove with",attrs=["underline"]),colored("x","red",attrs=["underline"])
    hf=open(fil,'r')
    lines=hf.readlines()
    hf.close()
    hf=open(fil,'w')
    rmd=False
    for line in lines:
        if line[0]=="*":
            inp=raw_input(line[2:-1]+" : ")
            if inp!="x":
                hf.write(line)
            else:
                rmd=True
        elif not rmd:
            hf.write(line)
    hf.close()

def main():
    #expand ~
    rcfil=os.path.expanduser(rcfile)

    #config
    if os.path.isfile(rcfil):
        readrcf(rcfil)

    infdir=os.path.expanduser(infodir)
    ensure_dir(infdir)
    if len(sys.argv)==1:
        print "Use ",colored(sys.argv[0],"red"), "<command>"
        return
    helpf=os.path.join(infdir,sys.argv[1])
    
    if len(sys.argv)>2:
        # some options
        opt=sys.argv[2]
        if opt=="add":
            addhelp(helpf)
        elif opt=="rm":
            if os.path.isfile(helpf):
                rmhelp(helpf)

    elif os.path.isfile(helpf):
        if compact==1:
            outputhelpcompact(helpf)
        else:
            outputhelp(helpf)


if __name__ == '__main__':
    main()
