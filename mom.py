#!/usr/bin/env python
import os, sys
import re
import ConfigParser
from subprocess import call, check_output
from termcolor import colored

#default config file
RCFILE="~/.momrc"
#defaults
INFODIR="~/.mom"
COMPACT=0
TABLEN=5
COLORIZE=True
# highlight program name
HLPROGRAM=True
HLPROGBEG="\\on_yellow \\bold"
HLPROGEND="\\ \\"
HLOPTION=True
HLOPTBEG="\\bold"
HLOPTEND="\\"
# reset decorations after each line
RESETLINE=True
# decorations for service outputs
HLSERVBEG="\\underline"
HLSERVEND="\\"
# editor (if $EDITOR is not set)
EDITOR="vim"

colsfg="grey red green yellow blue magenta cyan white"
colsbg="on_grey on_red on_green on_yellow on_blue on_magenta on_cyan on_white"
attrs="bold dark underline blink reverse concealed"

savecats = dict()
savecats["cfg"]=[]
savecats["cbg"]=[]
savecats["att"]=[]
lastcmd=[]

def readrcf(rcfil):
    # read config and change defaults
    conf = ConfigParser.RawConfigParser()
    conf.readfp(FakeSecHead(open(rcfil)))
    par = dict(conf.items("asection"))
    Params = dict()
    for k, v in par.iteritems():
        Params[k.upper()] = v
    globals().update(Params)
    # restore type
    global COMPACT, TABLEN
    COMPACT = int(COMPACT)
    TABLEN = int(TABLEN)
    global COLORIZE, HLPROGRAM, HLOPTION, RESETLINE
    COLORIZE = to_bool(COLORIZE)
    HLPROGRAM = to_bool(HLPROGRAM)
    HLOPTION = to_bool(HLOPTION)
    RESETLINE = to_bool(RESETLINE)

# no sections in rcfile
class FakeSecHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[asection]\n'
    def readline(self):
        if self.sechead:
            try: return self.sechead
            finally: self.sechead = None
        else: return self.fp.readline()

def to_bool(value):
    """
       Converts 'something' to boolean. Raises exception for invalid formats
           Possible True  values: 1, True, "1", "TRue", "yes", "y", "t"
           Possible False values: 0, False, None, [], {}, "", "0", "faLse", "no", "n", "f", 0.0, ...
    """
    if str(value).lower() in ("yes", "y", "true",  "t", "1"): return True
    if str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))

def ensure_dir(d):
    if not os.path.exists(d):
        print "create",d
        os.makedirs(d)

def outputhelp(fil):
    # output help file
    hf=open(fil,'r')
    newl = True
    for line in hf:
        if line[0]=="*":
            if not newl:
                print
            printline(line[2:])
            if not COMPACT:
                print
                newl = True
            else:
                newl = False
        else:
            if not COMPACT:
                print " "*TABLEN,
            else:
                print " - ",
            printline(line)
            print
            newl = True
    hf.close()

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

def printword(w):
    curcfg = savecats["cfg"][-1] if savecats["cfg"] else None
    curcbg = savecats["cbg"][-1] if savecats["cbg"] else None
    print colored(w,curcfg,curcbg,attrs=list(set(savecats["att"]))),

def highlight(line,pattern,hlbeg,hlend):
    i = 0; output = ''
    for m in re.finditer(pattern,line):
        output += "".join([line[i:m.start()],
                        " ",hlbeg," ",
                        line[m.start():m.end()],
                        " ",hlend," "])
        i = m.end()
    return "".join([output,line[i:]])

def preprocess(line):
    if HLPROGRAM:
        # highlight the name of program
        line = highlight(line,"(?<!\.)(\\b"+sys.argv[1]+"\\b)",HLPROGBEG,HLPROGEND)
   
    if HLOPTION:
        # highlight options (words starting with -)
        line = highlight(line,r"(\B-+)\w+",HLOPTBEG,HLOPTEND)
    return line 

def printline(line):
    # print a line with colors and attributes
    line = preprocess(line)
    words=line.split()
    global savecats
    global lastcmd
    if RESETLINE:
        savecats["cfg"]=[]
        savecats["cbg"]=[]
        savecats["att"]=[]
        lastcmd=[]
    for w in words:
        if w[0]!="\\":
            printword(w)
        elif w=="\\":
            #end
            if lastcmd:
                savecats[lastcmd.pop()].pop()
        else:
            wordcmd(w[1:])


def addhelp(fil):
    # add help from stdin
    hf=open(fil,'a')
    printline(HLSERVBEG+" Topic "+HLSERVEND)
    inp=raw_input(': ')
    if len(inp) > 0:
        hf.write("* "+inp+"\n")
        printline(HLSERVBEG+" Description "+HLSERVEND)
        inp=raw_input(': ')
        if len(inp)>0:
            hf.write(inp+"\n")
    hf.close()

def rmhelp(fil):
    # rm help from file
    printline(HLSERVBEG+" Remove with \\red x "+HLSERVEND)
    print
    hf=open(fil,'r')
    lines=hf.readlines()
    hf.close()
    hf=open(fil+".tmp",'w')
    rmd=False
    for line in lines:
        if line[0]=="*":
            printline(line[2:])
            inp=raw_input(" : ")
            if inp!="x":
                hf.write(line)
            else:
                rmd=True
        elif not rmd:
            hf.write(line)
    hf.close()
    os.rename(fil+".tmp",fil)

def main():
    #expand ~
    rcfil=os.path.expanduser(RCFILE)

    #config
    if os.path.isfile(rcfil):
        readrcf(rcfil)

    infdir=os.path.expanduser(INFODIR)
    ensure_dir(infdir)
    if len(sys.argv)==1:
        print "Use ",colored(sys.argv[0],"red"), "<command>"
        return
    helpf=os.path.join(infdir,sys.argv[1]+".m0m")
    
    if len(sys.argv)>2:
        # some options
        opt=sys.argv[2]
        if opt == "add":
            addhelp(helpf)
        elif opt == "rm":
            if os.path.isfile(helpf):
                rmhelp(helpf)
        elif opt == "edit":
            UseEditor = os.environ.get('EDITOR',EDITOR)
            call([UseEditor,helpf])

    elif os.path.isfile(helpf):
        outputhelp(helpf)
    else:
        # call standard help
        try:
            lines = check_output([sys.argv[1],"-h"])
            printline(HLSERVBEG+" Standard help "+HLSERVEND)
            print
            for line in lines.split('\n'):
                printline(line)
                print
        except:
            pass

if __name__ == '__main__':
    main()
