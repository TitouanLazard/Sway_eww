#!/bin/python
import sys
import os
import socket
import subprocess
import json
import shutil
import struct

MAX_LENGTH_APPNAME=64

verbose = False
sock_path = "./sock"

ipc_magic='i3-ipc';
subscribe_type = 0x02
get_outputs = 0x03
get_workspaces = 0x01
header_length = 14
eww = "/home/titouan/Working_Dir/eww/target/release/eww"

def log(s):
    if verbose:
        print(s)


def error_exit(s):
    print("[-] Error: "+ s )
    sys.exit()


class Daemon():

   
    def update_varname(self, current_name):
        subprocess.run([eww, "update", f"sway_currentapp={current_name}"])

    def show_workspace(self, output, num):
        subprocess.run([eww, "update", f"{output}-{num}=true"])

    def hide_workspace(self, output, num):
        subprocess.run([eww, "update", f"{output}-{num}=false"])

    def set_focus_workspace(self, num):
        subprocess.run([eww, "update", f"wp-focused={num}"])

    def set_visible_workspace(self, output, num):
        subprocess.run([eww, "update", f"wp-{output}-visible={num}"])

    def set_visible_bar(self, output):
        subprocess.run([eww, "open", f"main_bar_{output}"])

    
        
    def update(self, data):        
        i = json.loads(data.decode())
        if "change" in i:
            if i["change"] == "focus":
            
                if "container" in i:
                    # change focused window
                    n = i["container"]["name"]
                    if len(n) > MAX_LENGTH_APPNAME:
                        n = n[:MAX_LENGTH_APPNAME]+"..."
                    self.update_varname(n)
                elif "current" in i:
                    self.set_focus_workspace(i["current"]["name"])
                    if i["current"]["name"] !=  self.outputs[i["current"]["output"]]:
                        self.outputs[i["current"]["output"]] = i["current"]["name"]
                        self.set_visible_workspace(i["current"]["output"], i["current"]["name"])
                else:
                    print(json.dumps(i, indent=4))
            elif i["change"] == "move":
                # Moving window to other workspace
                print(json.dumps(i, indent=4))
            elif i["change"] == "init":
                # Creating a new workspace
                if (i["current"]["output"] not in self.outputs):
                   self.outputs[i["current"]["output"]] = i["current"]["name"]
                   self.set_visible_bar(i["current"]["output"])
                self.show_workspace(i["current"]["output"],i["current"]["num"])

            elif i["change"] == "empty":
                self.hide_workspace(i["current"]["output"],i["current"]["num"])
            elif i["change"] == "move":
                if "old" in i: # monitor_unplugged
                    self.initial_state()
            elif i["change"] == "title":
                n = i["container"]["name"]
                if len(n) > MAX_LENGTH_APPNAME:
                    n = n[:MAX_LENGTH_APPNAME]+"..."
                self.update_varname(n)

            elif i["change"] == "urgent":
                pass
            else:
                print(i["change"])
            
    def loop(self):
        while not self.exit:
            data = self.sock.recv(header_length) 
            size, t = struct.unpack_from("<II", data, offset=len(ipc_magic))
            data = self.sock.recv(size)
            self.update(data)
        self.sock.close()

    def init_sock_subscription(self):
        log("Initialize log subscription")
        payload = "['workspace','window']"
        mess_type = struct.pack("<I", subscribe_type)
        size = len(payload)
        header = ipc_magic.encode()
        buf = ipc_magic.encode() + struct.pack("<I",size) + mess_type
        self.sock.send(buf)
        self.sock.send(payload.encode())
        data = self.sock.recv(header_length) 
        size, t = struct.unpack_from("<II", data, offset=len(ipc_magic))
        data = self.sock.recv(size)
        

    def initial_state(self):
        header = ipc_magic.encode()
        mess_type = struct.pack("<I", get_outputs)
        buf = ipc_magic.encode() + struct.pack("<I",0) + mess_type
        self.sock.send(buf)
        data = self.sock.recv(header_length) 
        size, t = struct.unpack_from("<II", data, offset=len(ipc_magic))
        data = self.sock.recv(size)
        js = json.loads(data.decode())
        print(json.dumps(js,indent=4))
        self.outputs = {o['name']:int(o['current_workspace']) if o['current_workspace'] else "11" for o in js}
        for i in self.outputs:
            self.set_visible_bar(i)

        header = ipc_magic.encode()
        mess_type = struct.pack("<I", get_workspaces)
        buf = ipc_magic.encode() + struct.pack("<I",0) + mess_type
        self.sock.send(buf)
        data = self.sock.recv(header_length) 
        size, t = struct.unpack_from("<II", data, offset=len(ipc_magic))
        data = self.sock.recv(size)
        js = json.loads(data.decode())

        index = 0
       
        for wp in js:
            self.show_workspace(wp["output"],wp['num'])
            
    def __init__(self, sock_path=None):
        self.exit = False
        self.workspaces = []
        self.outputs = {}
        if sock_path == None:
            sock_path = os.getenv("SWAYSOCK")
        if sock_path == None:
            error_exit("Cannot find sway socket")
        self.sock_path = sock_path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(sock_path)

        self.initial_state()
        self.init_sock_subscription()
        #print(self.outputs)
    
if __name__ == "__main__":
    sock_path = None
    if "-v" in sys.argv:
        verbose = True
    if "-s" in sys.argv:
        try:
            sock_path = sys.argv[sys.argv.index("-s")+1]
        except:
            error_exit("Missing Socket Path")

    if "-d" in sys.argv:
        log("Preparing FS")
        log("Starting swayeww as deamon")
        d = Daemon(sock_path=sock_path)
        d.loop()
        log("Daemon Exit")
