#!/usr/bin/env python3
from __future__ import print_function
import os, sys
import re
try:
    import configparser
except:
    import ConfigParser as configparser
from subprocess import call, check_output
from termcolor import colored

#default config file
RCFILE = "~/.momrc"
#defaults
INFODIR = "~/.mom"
COMPACT = 0
TABLEN = 5
COLORIZE = True
ATTRIZE = True
# highlight program name
HLPROGRAM = True
HLPROGBEG = "\\on_yellow \\bold"
# highlight options (i.e. everything beginning with a "-")
HLOPTION = True
HLOPTBEG = "\\bold"
# highlight topic
HLTOPIC = True
HLTOPICBEG = "\\bold"
# reset decorations after each line
RESETLINE = True
# decorations for service outputs
HLSERVBEG = "\\underline"
# will be generated
HLPROGEND = ""
HLOPTEND = ""
HLTOPICEND = ""
HLSERVEND = ""
# unknown command; colors and attributes have to be given explicitly
UCCOLFG = "red"
UCCOLBG = "on_white"
UCATTR = "" # comma separated string 
# editor (if $EDITOR is not set)
EDITOR = "vim"
# standard help options
HELPOPTIONS = ["-h","--help", "-help"]

EXTENSION = ".m0m"

COLSFG = "grey red green yellow blue magenta cyan white"
COLSBG = "on_grey on_red on_green on_yellow on_blue on_magenta on_cyan on_white"
ATTRS = "bold dark underline blink reverse concealed"

savecats = dict()
savecats["cfg"] = []
savecats["cbg"] = []
savecats["att"] = []
lastcmd = []

def readrcf(rcfil):
    """
       Reads config and changes defaults
    """
    conf = configparser.RawConfigParser()
    if sys.version_info <= (3, 0, 0):
        conf.readfp(FakeSecHead(open(rcfil)))
        par = dict(conf.items("asection"))
        Params = dict()
        for k, v in par.iteritems():
            Params[k.upper()] = v
    else:
        conf.read_string("[asection]\n" + open(rcfil).read())
        par = dict(conf.items("asection"))
        Params = dict()
        for k, v in par.items():
            Params[k.upper()] = v
    globals().update(Params)
    # restore type
    global COMPACT, TABLEN
    COMPACT = int(COMPACT)
    TABLEN = int(TABLEN)
    global COLORIZE, ATTRIZE, HLPROGRAM, HLOPTION, HLTOPIC, RESETLINE
    COLORIZE = to_bool(COLORIZE)
    ATTRIZE = to_bool(ATTRIZE)
    HLPROGRAM = to_bool(HLPROGRAM)
    HLOPTION = to_bool(HLOPTION)
    HLTOPIC = to_bool(HLTOPIC)
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

def notclosedcolors(line):
    """
       Calculates number of not closed colors and attributes in line (line is printed out!)
    """
    global RESETLINE
    saveRL = RESETLINE
    RESETLINE = True
    printline(line)
    RESETLINE = saveRL
    return len(lastcmd)

def genends():
    """
       Generates ends for default highlights
    """
    global HLPROGEND, HLOPTEND, HLTOPICEND, HLSERVEND
    HLPROGEND = "\\ "*notclosedcolors(HLPROGBEG)
    HLOPTEND = "\\ "*notclosedcolors(HLOPTBEG)
    HLTOPICEND = "\\ "*notclosedcolors(HLTOPICBEG)
    HLSERVEND = "\\ "*notclosedcolors(HLSERVBEG)


def ensure_dir(d):
    """
       Creates directory d if not existent 
    """
    if not os.path.exists(d):
        print ("create",d)
        os.makedirs(d)

def outputhelp(fil):
    """
       Outputs a help file
    """
    hf=open(fil,'r')
    newl = True
    for line in hf:
        if line[0]=="#":
            pass
        elif line[0]=="*":
            if not newl: print()
            topic = line[1:].rstrip('\n')
            if HLTOPIC:
                topic = HLTOPICBEG + " " + topic + HLTOPICEND
            printline(topic)
            if not COMPACT:
                print()
                newl = True
            else:
                newl = False
        else:
            if not COMPACT:
                print (" "*(TABLEN),end='')
            else:
                print (" - ",end='')
            printline(line[1:])
            newl = True
    if not newl: print()
    hf.close()

def color(text, color=None, on_color=None, attrs=None):
    """
       wrapper for colored
    """
    if not COLORIZE:
        color = None
        on_color = None
    if not ATTRIZE:
        attrs = None
    # call colored from termcolor
    return colored(text, color, on_color, attrs)

def wordcmd(w):
    """
       Analyses and saves a command
    """
    global savecats
    global lastcmd
    if w in COLSFG.split():
        #save new foreground
        lastcmd.append("cfg")
    elif w in COLSBG.split():   
        #save new background
        lastcmd.append("cbg")
    elif w in ATTRS.split():
        #add attribute
        lastcmd.append("att")
    else:
        # unknown command, colorize using UCCOLFG,UCCOLBG,UCATTR
        if UCATTR.strip():
            attrib = [at.strip() for at in UCATTR.split(",")]
        else:
            attrib = []
        return color(w,UCCOLFG,UCCOLBG,attrib)
    # save command for later use
    savecats[lastcmd[-1]].append(w)
    return ""

def colorize(line):
    """
       Colorizes a line according to savecats[]
    """
    # last values in savecats for colors
    curcfg = savecats["cfg"][-1] if savecats["cfg"] else None
    curcbg = savecats["cbg"][-1] if savecats["cbg"] else None
    # unique list from savecats for attributes
    return color(line,curcfg,curcbg,attrs=list(set(savecats["att"])))

def highlight(line,pattern,hlbeg,hlend):
    """
       Highlights occurrences of a pattern in a line according to hlbeg
    """
    i = 0; output = ''
    for m in re.finditer(pattern,line):
        output += "".join([line[i:m.start()],
                        hlbeg," ",
                        line[m.start():m.end()],
                        hlend])
        i = m.end()
    return "".join([output,line[i:]])

def preprocess(line):
    """
       Highlights program name and/or options in a line
    """
    if HLPROGRAM:
        # highlight the name of program
        line = highlight(line,"(?<!\\.)(\\b"+sys.argv[1]+"\\b)",HLPROGBEG,HLPROGEND)
   
    if HLOPTION:
        # highlight options (words starting with -)
        line = highlight(line,r"(\B-+)\w+",HLOPTBEG,HLOPTEND)
    return line 

def printline(line):
    """
       Prints a line with colors and attributes
    """
    line = preprocess(line)
    global savecats
    global lastcmd
    if RESETLINE:
        savecats["cfg"]=[]
        savecats["cbg"]=[]
        savecats["att"]=[]
        lastcmd=[]

    i = 0; output = ''
    # commands
    for m in re.finditer(r"(\\+)\w+|\\+",line):
        output += colorize(line[i:m.start()])
        w = line[m.start():m.end()]
        i = m.end()
        unknwncmd = ""
        if w=="\\":
            #end
            if lastcmd:
                savecats[lastcmd.pop()].pop()
        else:
            unknwncmd = wordcmd(w[1:])
            output += unknwncmd 
                
        if i < len(line) and line[i]==" " and not unknwncmd:
            i = i + 1
    # print without space at the end
    sys.stdout.write("".join([output,colorize(line[i:])]))
    #print "".join([output,colorize(line[i:])]),

def addhelp(fil):
    """
       Adds a new topic from stdin
    """
    hf=open(fil,'a')
    printline(HLSERVBEG+" Topic"+HLSERVEND)
    if sys.version_info <= (3, 0, 0):
        inp=raw_input(': ')
    else:
        inp=input(': ')
    if len(inp) > 0:
        hf.write("*"+inp+"\n")
        printline(HLSERVBEG+" Description"+HLSERVEND)
        if sys.version_info <= (3, 0, 0):
            inp=raw_input(': ')
        else:
            inp=input(': ')
        if len(inp)>0:
            hf.write(" "+inp+"\n")
    hf.close()

def rmhelp(fil):
    """
       Removes or hides a topic
    """
    printline(HLSERVBEG+" Remove with \\red x\\ , hide with \\blue c\\ "+HLSERVEND)
    print()
    hf=open(fil,'r')
    lines=hf.readlines()
    hf.close()
    lines2=""
    rmd=0
    # rmd: 0 - don't remove
    #      1 - remove
    #      2 - hide
    for line in lines:
        if line[0]=="*":
            rmd=0
            printline(line[1:].rstrip('\n'))
            if sys.version_info <= (3, 0, 0):
                inp=raw_input(" : ")
            else:
                inp=input(" : ")
            if inp=="x":
                rmd=1
            elif inp=="c":
                rmd=2
                # comment
                lines2 += "#"+line
            else:
                lines2 += line
        elif not rmd:
            lines2 += line
        elif rmd==2:
            # comment
            lines2 += "#"+line
    hf=open(fil,'w')
    hf.write(lines2)
    hf.close()

def main():
    #expand ~
    rcfil=os.path.expanduser(RCFILE)

    #config
    if os.path.isfile(rcfil):
        readrcf(rcfil)
    if len(sys.argv)==1 or len(sys.argv)==2 and sys.argv[1] in ["-h","--help"]:
        print ("Use",color(sys.argv[0],"red"), "<command> [option]")
        print ("Options:")
        print (color("  add", "red"), ":    add a new topic")
        print (color("  rm", "red"), ":     remove or hide a topic")
        print (color("  edit", "red"), ":   edit the help file")
        print (color("  ls", "red"), ":     list all help files")
        print (color("  colors", "red"), ": list all text-decorations")
        print (color("  rm-all", "red"), ": delete all topics")
        return
    #generate ends for highlights
    genends()

    infdir=os.path.expanduser(INFODIR)
    ensure_dir(infdir)
    helpf=os.path.join(infdir,sys.argv[1]+EXTENSION)
    
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
        elif opt == "ls":
            # list all help files
            printline(HLSERVBEG+" Available commands"+HLSERVEND)
            print()
            for fil in os.listdir(infdir):
                if fil[-len(EXTENSION):] == EXTENSION:
                    print (fil[:-len(EXTENSION)],end=' ')
            print()
        elif opt == "colors":
            # list all text-decorations
            for col in COLSFG.split():
                printline("\\"+col+" "+col+" \\ ")
            print()
            for col in COLSBG.split():
                printline("\\"+col+" "+col+" \\ ")
            print()
            for col in ATTRS.split():
                printline("\\"+col+" "+col+" \\ ")
            print()
        elif opt == "rm-all":
            # delete the complete file
            printline(HLSERVBEG+" Delete all topics for "+sys.argv[1]+"? (yYjJ/n)"+HLSERVEND)
            if sys.version_info <= (3, 0, 0):
                inp=raw_input(" : ")
            else:
                inp=input(" : ")
            if inp in ["y", "Y", "j", "J"]:
                if os.path.isfile(helpf):
                    os.remove(helpf)
    elif os.path.isfile(helpf):
        outputhelp(helpf)
    else:
        # call standard help
        for hop in HELPOPTIONS: 
            try:
                lines = check_output([sys.argv[1],hop],universal_newlines=True)[:-1] # remove last \n
                printline(HLSERVBEG+" Standard help"+HLSERVEND)
                print()
                for line in lines.split('\n'):
                    printline(line)
                    print()
                break
            except:
                # try next h-option
                pass
                

if __name__ == '__main__':
    main()
