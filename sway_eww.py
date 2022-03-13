#!/bin/python
import sys
import os
import socket
import subprocess
import json
import shutil
import struct

verbose = False
sock_path = "./sock"

ipc_magic='i3-ipc';
subscribe_type = 0x02
get_outputs = 0x03
get_workspaces = 0x01
header_length = 14

def log(s):
    if verbose:
        print(s)


def error_exit(s):
    print("[-] Error: "+ s )
    sys.exit()




class Workspace():
    def __init__(self, wp_json, daemon):
        self.num = wp_json["num"]
        self.daemon = daemon
        self.output = wp_json["output"]
        self.daemon.outputs[self.output] = self.num
        
        
    def __repr__(self):
        return str(self.num) + '@' + self.output + (("-focused") if self.daemon.focused_wp==self.num else "-not_focused") + (" - VISIBLE" if self.daemon.outputs[self.output] == self.num else " - NOT VISIBLE" )


    
class Daemon():

    def update(self, data):        
        i = json.loads(data.decode())
        if "change" in i:
            if i["change"] == "focus":
            
                if "container" in i:
                    # change focused window
                    self.current_name = i["container"]["name"]
                elif "current" in i:
                    # change focused workspace
                    self.focused_wp = int(i["current"]["name"])
                    self.outputs[i["current"]["output"]] = int(i["current"]["name"])
                else:
                    print(json.dumps(i, indent=4))
            elif i["change"] == "move":
                # Moving window to other workspace
                print(json.dumps(i, indent=4))
            elif i["change"] == "init":
                # Creating a new workspace
                self.workspaces.append(Workspace(i["current"], self))
            elif i["change"] == "empty":
                # Closing an empty workspace
                for wp in range(len(self.workspaces)):
                    if self.workspaces[wp].num == i["current"]["num"]:
                        self.workspaces.remove(self.workspaces[wp])
                    
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
        self.outputs = {o['name']:int(o['current_workspace']) for o in js}


        header = ipc_magic.encode()
        mess_type = struct.pack("<I", get_workspaces)

        buf = ipc_magic.encode() + struct.pack("<I",0) + mess_type
        self.sock.send(buf)
        data = self.sock.recv(header_length) 
        size, t = struct.unpack_from("<II", data, offset=len(ipc_magic))
        data = self.sock.recv(size)
        js = json.loads(data.decode())
        
        for wp in js:
            print(wp)
            self.workspaces.append(Workspace(wp,self))
            if(wp["focused"]):
                self.focused_wp = wp['num']
            
            
    def __init__(self, sock_path=None):
        self.exit = False
        self.workspaces = []
        self.outputs = []
        if sock_path == None:
            sock_path = os.getenv("SWAYSOCK")
        if sock_path == None:
            error_exit("Cannot find sway socket")
        self.sock_path = sock_path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(sock_path)
        self.init_sock_subscription()
        self.initial_state()
            
    
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
