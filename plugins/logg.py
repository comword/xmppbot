#!/usr/bin/env /usr/bin/python3
import main
import privilage
import config

import time,os
import lang
import gzip
import tarfile
import re

m_conf=config.get_plgconf("logg")
R = main.R
log_path=os.getcwd()+m_conf["path"]
log_flag={}
ISOTIMEFORMAT='%Y-%m-%d %X'

def check_log_dir():
	if os.path.isdir(log_path):
		return True
	else:
		return False

def go_gzip(s,d):
	buf = b""
	if os.path.isfile(s):
		with open(s, 'rb') as f:
			buf += f.read()
		with gzip.open(d, 'wb') as f:
			f.write(buf)
		return 0
	else:
		return -1

def mergegzfile(path,f_name_list, dest_f_name):
	buf = ""
	for i in f_name_list:
		if not os.path.isfile(path+'/'+i):
			return -1
		with gzip.open(path+'/'+i, 'rb') as f:
			buf += f.read()
			buf += '\n'
	with gzip.open(path+'/'+dest_f_name, 'wb') as f:
		f.write(content)
	return 0

def mergelogperday(date, log_path):
	#date %Y%m%d
	if not os.path.isdir(log_path):
		return -1
	log_files = [f for f in os.listdir(os.getcwd()+m_conf["path"]) if os.path.isfile(os.path.join(os.getcwd()+m_conf["path"], f))]
	log_files.sort()
	res = list()
	for f in log_files:
		f_date = os.path.basename(f)[0:8]
		if f_date == date:
			res.append(f)
	if len(res) != 0:
		mergegzfile(log_path,res,res[0])

def tar_reset(tarinfo):
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "root"
    return tarinfo

def tarlog_range(orgmsg, log_path, datefrom, dateto, filename):
	if not os.path.isdir(log_path):
		return -1
	log_files = [f for f in os.listdir(os.getcwd()+m_conf["path"]) if os.path.isfile(os.path.join(os.getcwd()+m_conf["path"], f))]
	log_files.sort()
	if not orgmsg['type'] in ('chat', 'normal'):
		log_files = [ x for x in log_files if orgmsg['from'].bare.split('@',1)[0] in x ]
	compress_list = list()
	res = "Compressed:\n"
	for f in log_files:
		f_date = os.path.basename(f)[0:8]
		if(f_date<=dateto) and (f_date>=datefrom):
			compress_list.append(os.getcwd()+m_conf["path"]+"/"+f)
			res += (f+'\n')
	tar = tarfile.open(filename, "w")
	for name in compress_list:
		tar.add(name, filter=tar_reset, arcname=os.path.basename(name))
	tar.close()
	return res

@R.add(_("\/startlog\s?"),"oncommand")
def start_log(groups,orgmsg):
	if orgmsg['from'].bare in log_flag:
		return _("This session is being logged.")
	else:
		log_flag[orgmsg['from'].bare] = {}
		log_flag[orgmsg['from'].bare]['ignore_char'] = ''
		log_flag[orgmsg['from'].bare]["filename"] = log_path+"/"+time.strftime("%Y%m%d%H%M%S", time.localtime())+orgmsg['from'].bare.split('@')[0]+".log"
		log_flag[orgmsg['from'].bare]["file"] = open(log_flag[orgmsg['from'].bare]["filename"],'w')
		log_flag[orgmsg['from'].bare]["logging"] = True
		log_flag[orgmsg['from'].bare]["sttime"] = time.localtime()
		return _("A new log started at %(time)s")% {'time':time.strftime(ISOTIMEFORMAT, time.localtime())}

@R.add(_("\/stoplog\s?"),"oncommand")
def stop_log(groups,orgmsg):
	if orgmsg['from'].bare in log_flag:
		log_flag[orgmsg['from'].bare]["file"].close()
		go_gzip(log_flag[orgmsg['from'].bare]["filename"],log_flag[orgmsg['from'].bare]["filename"]+".gz")
		os.remove(log_flag[orgmsg['from'].bare]["filename"])
		log_flag.pop(orgmsg['from'].bare)
		return _("The log is stopped at %(time)s") % {'time':time.strftime(ISOTIMEFORMAT, time.localtime())}
	else:
		return _("This session is not being logged.")

@R.add(_("\/pauselog\s?"),"oncommand")
def pause_log(groups,orgmsg):
	if orgmsg['from'].bare in log_flag:
		if (log_flag[orgmsg['from'].bare]["logging"] == True):
			log_flag[orgmsg['from'].bare]["logging"] = False
			return _("Current log process paused.")
		else:
			return _("This logging session is paused.")
	else:
		return _("This session is not being logged.")

@R.add(_("\/resumelog\s?"),"oncommand")
def resume_log(groups,orgmsg):
	if orgmsg['from'].bare in log_flag:
		if (log_flag[orgmsg['from'].bare]["logging"] == False):
			log_flag[orgmsg['from'].bare]["logging"] = True
			return _("Current log process resumed.")
		else:
			return _("This logging session is not paused.")
	else:
		return _("This session is not being logged.")

@R.add(_("\/lslog\s?"),"oncommand")
def ls_log(groups,orgmsg):
	log_files = [f for f in os.listdir(os.getcwd()+m_conf["path"]) if os.path.isfile(os.path.join(os.getcwd()+m_conf["path"], f))]
	log_files.sort()
	if not orgmsg['type'] in ('chat', 'normal'):
		log_files = [ x for x in log_files if orgmsg['from'].bare.split('@',1)[0] in x ]
	if len(log_files) == 0:
		return _("No available log to show.")
	else:
		res = ""
		for i in log_files:
			res += i
			res += '\n'
		return res

@R.add(_("\/catlog\s(\S+)\s?"),"oncommand")
def cat_log(groups,orgmsg):
	try:
		cmd = groups.group(1)
		cmd = fliter_command(cmd)
	except IndexError:
		return None
	if not os.path.isfile(os.getcwd()+m_conf["path"]+'/'+cmd):
		return _("File %s not found.") % cmd
	buf = ""
	with gzip.open(os.getcwd()+m_conf["path"]+'/'+cmd, 'rb') as f:
		buf += f.read().decode("utf-8")
		buf += '\n'
	return buf

@R.add(_("\/setignore\s(\S+)\s?"),"oncommand")
def set_ignore(groups,orgmsg):
	if orgmsg['from'].bare in log_flag:
		if(log_flag[orgmsg['from'].bare]["logging"] == True):
			try:
				cmd = groups.group(1)
			except IndexError:
				log_flag[orgmsg['from'].bare]["ignore_char"] = ''
				return _("Ignore regx removed successfully.")
			try:
				re.compile(cmd)
			except:
				return _("Regx test failed.")
			log_flag[orgmsg['from'].bare]["ignore_char"] = cmd
			return _("Set ignore regx to %s successfully.") % cmd
	return _("This session is not being logged.")

@R.add(_("\/tarfile\s(\d+)\s(\d+)\s(\S+)\s?"),"oncommand")
def gen_file(groups,orgmsg):
	try:
		datefrom = groups.group(1)
		dateto = groups.group(2)
	except IndexError:
		return None
	try:
		filename = groups.group(3)
	except IndexError:
		filename = log_path+"/"+time.strftime("%Y%m%d%H%M%S", time.localtime())+orgmsg['from'].bare.split('@')[0]+".tar"
	return tarlog_range(orgmsg,log_path, datefrom, dateto, filename)

@R.add("proclog","onmessage")
def proc_log(cla,msg):
	if msg['from'].bare in log_flag:
		if(log_flag[msg['from'].bare]["logging"] == True):
			if(check_ign(log_flag[msg['from'].bare]["ignore_char"],msg["body"])):
				log_flag[msg['from'].bare]["file"].write(time.strftime("%H:%M:%S", time.localtime())+" "+msg['mucnick']+": "+msg["body"]+"\n")
				log_flag[msg['from'].bare]["file"].flush()

def fliter_command(cmd):
	cmd = cmd.replace('/',"")
	cmd = cmd.replace('\\',"")
	cmd = cmd.replace(';',"")
	cmd = cmd.replace(':',"")
	cmd = cmd.replace('`',"")
	cmd = cmd.replace('"',"")
	cmd = cmd.replace('\'',"")
	cmd = cmd.replace('|',"")
	cmd = cmd.replace('>',"")
	cmd = cmd.replace('<',"")
	cmd = cmd.replace('$',"")
	cmd = cmd.replace('*',"")
	cmd = cmd.replace('..',"")
	return cmd

def check_ign(ignore_str,msg):
	res = re.search(ignore_str,msg)
	if res == None:
		return True
	else:
		return False

if (check_log_dir() == False):
	print (_("Log directory not exist, creating..."))
	os.makedirs(log_path)

privilage.set_priv("startlog",2)
privilage.set_priv("stoplog",2)
privilage.set_priv("pauselog",2)
privilage.set_priv("resumelog",2)
privilage.set_priv("lslog",2)
privilage.set_priv("catlog",2)
privilage.set_priv("setignore",2)

R.set_help("logg",_("""Log bot usage:
/startlog	Start a new log session.
/stoplog	Stop current log session.
/pauselog	Pause current log session.
/resumelog	Resume paused log session.
/lslog	List all logs.
/catlog <LOGNAME>	Show log.
/setignore <IGNORE CHAR> A message started with this character won't be included in log. Leave second parameter to empty to accept all message. IGNORE CHAR format should be separated by ` e.g: (`{`< , then ( { < will be ignored.
/tarfile
"""))
