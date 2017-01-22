#!/usr/bin/env /usr/bin/python3
import lang
import re

class R():
	def __init__(self):
		self.cmd_list = list()
		self.command_map={}
		self.message_map={}
		self.help_map={}
		self.cmd_alias={}
		self.command_map[_("\/help\s(\S+)\s?")] = self.show_help
	def add(self,*args):
		def decorator(f):
			f.register = tuple(args)
			if(tuple(args)[1] == "oncommand"):
				self.command_map[tuple(args)[0]] = f
				self.cmd_list.append(self.get_purecmd_regx(tuple(args)[0]))
			elif(tuple(args)[1] == "onmessage"):
				self.message_map[tuple(args)[0]] = f
			return f
		return decorator

	def show_help(groups,orgmsg):
		try:
			cmd = groups.group(1)
		except IndexError:
			return _("Type /help (plugin) to get help. Type /listplugins to list all plugins.")
		if cmd in self.help_map:
			return self.help_map[cmd]
		else:
			return _("The help of plugin %(pluginname)s is not being registered in manual.") % {'pluginname':cmd}

	def set_help(self,command,context):
		self.help_map[command] = context

	def set_alias(self,command,alias):
		self.cmd_alias[alias] = command

	def go_call(self,command,orgmsg):
		for cmd in self.cmd_alias:
			try:
				res = re.search(cmd,command)
			except:
				return _("Command %(cmd_userinput)s caused a error in %(cmd). It's a bug.") % {'cmd_userinput': command, 'cmd': cmd}
			if res != None:
				real_cmd = self.cmd_alias[cmd]
				if real_cmd in self.command_map:
					return self.command_map[real_cmd](res,orgmsg)
				else:
					return _("Command %s found in alias name, but it's a broken alias link. It's a bug.") % cmd
		for cmd in self.command_map:
			res = re.search(cmd,command)
			if res != None:
				return self.command_map[cmd](res,orgmsg)
		recmd = self.get_purecmd(command)
		if (recmd != None):
			return _("Command %s can't be found.") % recmd
		else:
			return None

	def get_purecmd(self,cmd):
		tmp = re.search('\/(\w+)', cmd)
		if tmp != None:
			return tmp.group(1)

	def get_purecmd_regx(self,cmd):
		tmp = re.search('\\\/(\w+)', cmd)
		if tmp != None:
			return tmp.group(1)

	def refresh_command_map_lang(self):
		tmp={}
		cmd_list = list()
		for k in self.command_map:
			if not _(k) == k:
				tmp[_(k)] = k
				cmd_list.append(self.get_purecmd_regx(_(k)))
			cmd_list.append(self.get_purecmd_regx(k))
		self.cmd_alias = tmp
		self.cmd_list = cmd_list

	def has_command(self, cmd):
		if self.get_purecmd(cmd) in self.cmd_list:
			return 1
		else:
			return 0
