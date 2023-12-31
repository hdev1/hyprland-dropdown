#!/usr/bin/env python3

import sys
import os
import json
import subprocess
from pathlib import Path
import json
import argparse
# Argparse

parser = argparse.ArgumentParser(
                    prog='hyprland-dropdown',
                    description='Make anything a scratchpad on Hyprland!')

parser.add_argument('-a', '--autostart',  help='auto-start applications in hidden workspace', action='store_true')
parser.add_argument('-t', '--toggle',  help='toggle application by id')
parser.add_argument('-l', '--lock', action='store_true', help='toggle lock active (defined) application')
parser.add_argument('-r', '--reload', action='store_true')
parser.add_argument('-c', '--config', help='custom config path')
args = parser.parse_args()

# Create config if it doesn't exist
script_path = os.path.dirname(os.path.realpath(__file__))
if args.config:
    config_path = args.config
else:
    config_path = os.path.join(script_path, "config.json")
    
config_path = os.path.expanduser(config_path)


if not os.path.exists(config_path):
    config = {
        "windows": [
            {
                "id": "terminal",
                "class": "kitty",
                "launcher": "kitty",
                "keybind": "$mainMod,T"
            },
        ],
        "keybinds": {
            "locking": [
                "$mainMod,L",
                "$mainMod,mouse:274"    
            ]
        },
        "hyprland_config": f"{Path.home()}/.config/hypr/extra_keybinds.conf",
    }
    config_text = json.dumps(config)
    with open(config_path, "w") as f:
        f.write(config_text)

config = json.load(open(config_path))

# Sys util functions
def exec_in_bg(command):
    return subprocess.Popen(command.split(" "))

def exec(command):
    return os.system(command)

def get_command_output(command):
    result = subprocess.run(command.split(" "), stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

def get_command_output_json(command):
    return json.loads(get_command_output(command))


def get_config_by_id(id):
    matched_config = [c for c in config['windows'] if c['id'] == id][0]
    return matched_config

def get_config_by_class(cls):
    matched_configs = [c for c in config['windows'] if c['class'] == cls]
    if len(matched_configs) == 0:
        return None
    
    return matched_configs[0]


def get_clients():
    return get_command_output_json("hyprctl clients -j")
    

def get_active_client_state():
    return get_command_output_json("hyprctl activewindow -j")

def get_target_client_addresses(id):
    client_config = get_config_by_id(id)
    clients = get_clients()
    matched_clients = [c['address'] for c in clients if c['class'] == client_config['class']]

    return matched_clients

def center_window(window):
    # Bad hacky hack, works for some reason
    for i in range(0,2):
        exec(f'hyprctl --batch "dispatch focuswindow {window}; dispatch resizewindowpixel exact 75% 75%,{window}; dispatch centerwindow;"')

def tile_window(window, no_lock=False):
    exec(f'hyprctl dispatch centerwindow {window}')
    if not no_lock:
        exec(f'hyprctl dispatch togglefloating {window}')
    exec(f'hyprctl setprop {window} dimaround 0')


def lock_client(active_client_state, no_lock=False):
    window = f"address:{active_client_state['address']}"
    print(window)

    if active_client_state['floating']:
        tile_window(window, no_lock)
    else:
        # exec(f'hyprctl setprop {window} dimaround 1')
        exec(f'hyprctl dispatch togglefloating {window}')

        if not no_lock:
            center_window(window)

def lock_active(no_lock=False):
    active_client_state = get_active_client_state()
    active_client_config = get_config_by_class(active_client_state['class'])

    if active_client_config == None:
        return
    
    lock_client(active_client_state, no_lock=no_lock)

def get_focused_monitor_and_workspace():
    monitors = get_command_output_json('hyprctl monitors -j')
    focused_monitor = [m for m in monitors if m['focused']][0]
    return focused_monitor['id'], focused_monitor['activeWorkspace']['id']

def toggle(id, no_activate=False):
    client_config = get_config_by_id(id)
    target_clients = get_target_client_addresses(id)
    focused_monitor_id, focused_workspace_id = get_focused_monitor_and_workspace()
    active_client_state = get_active_client_state()
    all_clients = get_clients()

    # Not running? Launch new instance
    if len(target_clients) == 0:
        if no_activate:
            return
        
        exec_in_bg(client_config['launcher'])
        return

    # Get all clients that match class; capture all of the subwindows
    for client_state in all_clients:
        window = f"address:{client_state['address']}"

        if not client_state['address'] in target_clients:
            if client_state['floating'] and get_config_by_class(client_state['class']) != None:
                exec(f'hyprctl --batch "dispatch movetoworkspacesilent name:hidden,{window}; dispatch cyclenext; dispatch nodim"')
            continue
        
        # Unlock and center/float window
        lock_client(client_state, no_lock=True)

        # Move window to current workspace
        if client_state['workspace']['id'] == -1337 or focused_monitor_id != client_state['monitor'] or focused_workspace_id != client_state['workspace']['id']:
            if no_activate:
                continue
            
            exec(f'hyprctl --batch "dispatch movetoworkspacesilent e+0,{window};"')
            center_window(window)
            continue
        
        if not no_activate and not active_client_state['address'] == client_state['address']:
            active_client_config = get_config_by_class(active_client_state['class'])
            if active_client_state['floating'] == True and active_client_config != None:
                toggle(active_client_config['id'], no_activate=True)

        exec(f'hyprctl --batch "dispatch movetoworkspacesilent name:hidden,{window}; dispatch cyclenext; dispatch nodim"')
        # exec(f'hyprctl setprop {window} dimaround 1')


def reload():
    rules = []
    command = f"python {Path(__file__).resolve()}"

    for window in config['windows']:
        rules.append(f"bind={window['keybind']},exec,{command} --toggle {window['id']}")
        # rules.append(f"windowrulev2 = nofullscreenrequest,class:{window['class']}")
        rules.append(f"windowrulev2 = float,class:{window['class']}")
        rules.append(f"windowrulev2 = size 75% 75%,class:{window['class']}")
        rules.append(f"windowrulev2 = move 30 50, class:{window['class']}")
        rules.append(f"windowrulev2 = dimaround, class:{window['class']}")
        rules.append(f"windowrulev2 = center, class:{window['class']}")
    
    # Rules for locking windows
    for keybind in config['keybinds']['locking']:
        rules.append(f'bind = {keybind},exec,{command} --lock')


    res = '\n'.join(rules)
    open(config['hyprland_config'], "w").write(res)

def autostart():
    clients = get_clients()
    for window in config['windows']:
        # Check if instance is already running
        instance_running = False
        for client in clients:
            if client['class'] == window['class']:
                # Instance already running
                instance_running = True
                break
        
        if not instance_running:
            os.system(f"hyprctl dispatch -- exec [workspace hidden silent] {window['launcher']}")

if args.reload:
    reload()

if args.lock:
    lock_active()

if args.toggle:
    toggle(args.toggle)

if args.autostart:
    autostart()