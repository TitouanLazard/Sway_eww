#!/bin/python
import sys
import os
import socket
import subprocess
import json
import shutil

verbose = False
sock_path = "./sock"
eww_mode = False


CMD_QUIT="quit"
CMD_REFRESH="refresh"


def log(s):
    if verbose:
        print(s)


def error_exit(s):
    print("[-] Error: "+ s )
    sys.exit()


        
class Client():
    def __init__(self, sock_path):
        if  not os.path.exists(sock_path):
            error_exit("No deamon at this address...")
        else:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(sock_path)

    def recv(self):
        return self.sock.recv(1024)
    
    def send(self, s):
        self.sock.send(s.encode())
        
    def kill(self):
        log("Slay the daemon")
        self.send(CMD_QUIT)

    def refresh(self):
        log("Refresh")
        self.send(CMD_REFRESH)



class Workspace():
    def __init__(self, wp):
        self.name = wp["name"]
        self.focused = wp["focused"]
        self.output = wp["output"]

    def __repr__(self):
        return self.name + '@' + self.output

    def write_as_button(self):
        return f"(button :class \"button-workspace{'-focused' if self.focused else ''}\" :onclick \"swaymsg workspace {self.name} /home/titouan/.config/eww/scripts/sway_eww.py -r\" \"{self.name}\" )"
        
class Daemon():
    
    def recv(self):
        return self.current_cli.recv(1024)
    
    def send(self, s):
        self.current_cli.send(s.encode())    
        
    def quit(self, cmd):
        self.exit = True

    def refresh(self, cmd):
        self.wps = []
        ret = subprocess.run(["swaymsg", "-t", "get_workspaces"], capture_output=True, env=os.environ.copy())
        js = json.loads(ret.stdout.decode())
        
        for wp in js:
            if wp['type'] != "workspace":
                continue
            
            self.wps.append(Workspace(wp))
        if self.eww_mode:
            self.render_eww()

    def render_eww(self):
        for wp in self.wps:
            if wp.output not in self.output_files:
                self.output_files[wp.output] = [open(f"/tmp/sway/{len(self.output_files)}", "w"),""]
            self.output_files[wp.output][1] += wp.write_as_button()
        self.output_files[wp.output][1] = "(box :space-evenly false :halign 'center' :class 'workspaces' " + self.output_files[wp.output][1] + ")\n"
        for f in self.output_files:
            self.output_files[f][0].write(self.output_files[f][1])
            self.output_files[f][0].flush()
            self.output_files[f][1] = ""
            
        
    def loop(self):
        while not self.exit:
            self.current_cli,_ = self.sock.accept()
            data = self.recv().decode()
            try:
                cmd = data.split(" ")
                self.method_name[cmd[0].rstrip()](cmd)
            except Exception as e:
                log("Error" + str(e))
        self.sock.close()

    def __init__(self, sock_path, eww_mode):
        self.eww_mode = eww_mode
        self.method_name = {CMD_QUIT:self.quit, CMD_REFRESH: self.refresh}
        self.wps = []
        try:
            os.unlink(sock_path)
        except OSError:
            if os.path.exists(sock_path):
                error_exit("Socket exist already and cannot be deleted")

        self.current_cli = None
        self.sock_path = sock_path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(sock_path)
        self.sock.listen(1)
        self.exit = False
        self.output_files = {}
        
        
            
    
if __name__ == "__main__":
    if "-v" in sys.argv:
        verbose = True
    if "-s" in sys.argv:
        try:
            sock_path = sys.argv[sys.argv.index("-s")+1]
        except:
            error_exit("Missing Socket Path")
    if "-e" in sys.argv:
        eww_mode = True
        
    if "-d" in sys.argv:
        log("Preparing FS")
        if os.path.exists("/tmp/sway"):
            shutil.rmtree("/tmp/sway")
        os.mkdir("/tmp/sway")
        log("Starting swayeww as deamon")
        d = Daemon(sock_path, eww_mode)
        d.loop()
        log("Daemon Exit")
    else:
        c = Client(sock_path)
        if "-k" in sys.argv:
            c.kill()
        elif "-r" in sys.argv:
            c.refresh()
