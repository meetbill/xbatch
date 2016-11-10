#/usr/bin/python
#coding:utf8
import readline,os,commands,sys
readline.set_completer_delims(' \t\n`~!@#$%^&*()=+[{]}\\|;:\'",<>/?')
HOME=commands.getoutput('''echo "$HOME"''')
def allcommands():
    a=commands.getoutput("PATH=$PATH:./:/usr/lib:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/cheung/bin;for c in $(echo $PATH |sed 's/:/ /g');do ls $c;done")
    return a.strip().split('\n')
def alllocalpath(path=''):
    result = []
    if not path: path = '.'
    for f in os.listdir(path):
        qf = os.path.join(path,f)
        if os.path.isdir(qf):
            result.append(f+os.sep)
        else:
            result.append(f)
    return result
    #print result
    #sys.exit()
 
class BufferAwareCompleter(object):
 
    def __init__(self, custcmd, allcmd):
        self.options = custcmd  
        self.current_candidates = []
        self.allcmd = allcmd
        return
 
    def complete(self, text, state):
        response = None
        if state == 0:
            origline = readline.get_line_buffer() 
            begin = readline.get_begidx() 
            end = readline.get_endidx() 
            being_completed = origline[begin:end]  
            words = origline.split() 
 
            if not words: 
                self.current_candidates = sorted(self.options)
            else:
                try:
                    if begin == 0: 
                        candidates = self.allcmd
                    else:
                        if origline.endswith(' '):words.append('')  
                        basedir,basefile = os.path.split(words[-1])
			if words[0].lower()=="select":
				candidates=alllocalpath("%s/cheung/data/hosts/"%HOME)
			else:
                        	candidates = alllocalpath(basedir)
                        being_completed = basefile
 
                    if being_completed: 
                        self.current_candidates = [ w for w in candidates
                                                    if w.startswith(being_completed) ]  
                    else:
                        self.current_candidates = candidates  
 
                except (KeyError, IndexError), err:
                    self.current_candidates = []
 
        try:
            response = self.current_candidates[state]
        except IndexError:
            response = None
        return response
 
custcmd = ['exit','use','select']
allcmd = custcmd[:]
allcmd.extend(allcommands())
 
readline.set_completer(BufferAwareCompleter(custcmd,allcmd).complete)
readline.parse_and_bind('tab: complete')
 
