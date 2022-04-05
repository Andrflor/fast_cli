#!/usr/bin/env python
import re
import os
import sys
import json
import time
import codecs
import signal
import requests
from bs4 import BeautifulSoup
from collections import deque

queue = deque([], 3)
script_name = "Fast cli"


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def display_title(title):
    print(title + " by " + bcolors.OKBLUE + "@Kensai" + bcolors.ENDC)


class ArgumentParser:
    def __init__(self, cmd_name, options):
        self.name = cmd_name
        self.options = options
        self.optional = {}
        self.args = []
        self.count = 0

    def parse(self):
        if len(sys.argv) == 1:
            return self.help(self.options)
        nextArg = ""
        for i in range(len(sys.argv)):
            elt = sys.argv[i]
            if elt[:2] == "--":
                self.optional[elt[2:]] = []
                nextArg = elt[2:]
            elif elt[0] == "-":
                self.optional[elt[1:]] = []
                nextArg = elt[1:]
            elif elt != sys.argv[0]:
                if nextArg == "":
                    self.args.append(elt)
                else:
                    self.optional[nextArg].append(elt)
        current = self.args[self.count]
        if current in self.options.keys():
            options = self.options[current]
        else:
            return self.help(self.options)
        while True:
            self.count += 1
            if type(options) is dict:
                if current in options.keys():
                    current = self.args[self.count]
                    options = options[current]
                else:
                    if len(self.args) <= self.count:
                        return self.help(options)
                    else:
                        current = self.args[self.count]
                        if current in options.keys():
                            options = options[current]
                        else:
                            return self.help(options)
            else:
                args = self.args[self.count:]
                if len(args) != 0 and args[0] == "help":
                    return self.help(options)
                cmd = [script_name, self.name] + self.args[:self.count]
                if type(options[-1]) is str:
                    return self.help(options)
                cmd_return = options[-1](*args, **self.optional)
                if cmd_return is None:
                    return
                elif type(cmd_return) is str:
                    print(
                        bcolors.WARNING + "Command {0} for {1} failed...".format(" ".join(cmd), " ".join(args)))
                    print(cmd_return)
                    print(bcolors.ENDC)
                    print("To get help: {0} help".format(" ".join(cmd)))
                    return
                else:
                    return self.help(options)

    def help(self, options):
        self.subs = self.args[:self.count]
        display_title("Fast cli")
        if type(options) is dict:
            if not "help" in options.keys():
                options["help"] = "This message"
            print("Usage: {0} {2}{{{1}}}".format(
                self.name, "|".join(options.keys()), " ".join(self.subs)))
        else:
            args = []
            for elt in options[1:]:
                if type(elt) != str:
                    break
                if "<" == elt[0]:
                    args.append(elt)
                if "[--" == elt[:3]:
                    break
            print("Usage: {0} {1} {3} {2}".format(script_name,
                  self.name, " ".join(args), " ".join(self.subs)))
            print("    {0}".format(options[0]))
            if " [--" in " ".join(options[:-1]):
                print()
                print("Options:")
                length = 0
                for elt in options:
                    if type(elt) != str:
                        break
                    if "[--" in elt:
                        to_print = "    {0}".format(
                            elt.replace("[", "").replace("]", ""))
                        length = len(to_print)+1
                        print(to_print)
                    elif length != 0:
                        if elt[0] == "<" and elt[-1] == ">":
                            print(f"\033[F\033[{length}G "+elt)
                            length += len(elt)+1
                        else:
                            print("        {0}".format(elt))
                return
            else:
                return
        print()
        print("  Options")
        maxsize = max([len(cmd) for cmd in options.keys()])
        if maxsize < 4:
            maxsize = 4
        for cmd, option in options.items():
            if type(option) is dict:
                print("    {0}:{1}{2}".format(
                    cmd, (maxsize-len(cmd)+1) * " ", option["help"][0]))
            elif type(option) is list and cmd != "help":
                print("    {0}:{1}{2}".format(
                    cmd, (maxsize-len(cmd)+1) * " ", option[0]))
        print("    help:{0}This message".format((maxsize-3) * " "))
        print()
        print("For more usage info type: {0}{1} subcommand help".format(
            self.name, " ".join(self.subs)))


class Killer:
    now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit)

    def exit(self, signum, frame):
        self.now = True
        quit()


def quit():
    sys.stdout.write("\x1b[2K")
    sys.stdout.write("\n")
    sys.stdout.write("Program exits on user demand\n")
    sys.exit()


killer = Killer()


def get_path(path):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data", path))


def printing(a, b, c):
    if killer.now:
        quit()

    for _ in range(len(queue)):
        sys.stdout.write("\x1b[1A\x1b[2K")

    queue.append(a)
    queue.append(b)
    queue.append(c)

    for i in range(len(queue)):
        sys.stdout.write(queue[i] + "\n")


def report_progress(job, current, total, name):

    progress_percent = current / total * 100
    total_percent = int((current / total) * 100)

    progress = "Total progress: [{1:33}] {0:.2f}%".format(progress_percent, "#" * int(progress_percent / 3),
                                                          total_percent)
    job_spacing = len(progress) - len(str(total)) - \
        len(str(current)) - len(job) - 1
    job_running = "{0}{1}{2}/{3}".format(job,
                                         " " * job_spacing, current, total)

    process = "Processing:{0}{1}"
    name_spacing = len(progress) - len(process) - len(name) + 6
    process_name = process.format(" " * name_spacing, name)
    printing(job_running, progress, process_name)


def get_text(url):
    return requests.get(url).text


def get_json(url):
    return requests.get(url).json()


def get_soup(url):
    return BeautifulSoup(get_text(url), 'html.parser')


def load_unicode(filename):
    f = codecs.open(filename, encoding='ISO-8859-1')
    return repr(f.readline())


def load_soup(filename):
    with open(get_path(filename), "r") as f:
        cnt = f.read()
    return BeautifulSoup(cnt, 'html.parser')


def load_json(filename):
    with open(get_path(filename), "r") as f:
        cnt = f.read()
    return json.loads(cnt)


def dump_json(filename, obj):
    json_string = json.dumps(obj, sort_keys=True,  ensure_ascii=False)
    dump_file(filename, json_string)


def load_file(filename, strip=True):
    with open(get_path(filename), "r", encoding='utf-8') as f:
        cnt = f.readlines()
    if not strip:
        return [x.replace("\n", "") for x in cnt]
    return [x.strip() for x in cnt]


def dump_file(filename, string):
    with open(get_path(filename), "w") as f:
        f.write(string)


def arg_parse(cmd_name, options):
    ArgumentParser(cmd_name, options).parse()
