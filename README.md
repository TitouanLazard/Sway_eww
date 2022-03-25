# Bringing Sway states informations into Elkowars Wacky Widgets

This is a simple script (shipped with yuck example configuration files) aiming to provide a way to updates eww variable to reflect on sway current states (e.g. current focus workspaces/applications).
It is not really usable "as is" in this current form, several actions might be required before being able to use it properly. You might need to:
- Modify the path to your own local eww installation.
- Modify your general eww config file

## How does it work ? 
Basically, the script start by subscribing to sways events through sway sockets.
These events are parsed and eww binary is called to update custom variables when required. 

#### You said variables...
Yes. It's pretty hackish. But it works. 
In the yuck file on this repo you will find a definition for several variables. 
Depending on your setup, you might need to add your own.

The yuck file defines a set of boolean variables named as "[MONITOR]-[WP\_Number]".
If eDP-1-1 is true, then the workspace 1 is on monitor eDP-1.

Each monitor also as a wp-[MONITOR]-visible variable. This variable contains the name of the currently displayed workspace on the MONITOR.

wp-focused variable contains the name of the currently focused workspace.

The [MONITOR]-[WP\_Number] variables are used as togglers for wp widgets.
10 wp are instanciated per workspaces widgets.
1 workspaces widget is instaciated per bar. 
A bar is displayable on each monitor.


## Futur work
Plenty of stuf still need to be done:
- Using eww ipc mechanism directly istead of popping a new eww process every time. That's urgent.
- Having a better way to handle workspaces names/numbers, to support workspaces with different names than 0-10.
- Add a way to customize eww workspace representation. 
- Adding support for "urgent" attributes on workspaces
