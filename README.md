# hyprland-dropdown

Make any application dropdown/scratchpad on Hyprland. Features:  
* Works with any application, customizable per application class
* Centers and floats configured applications
* Locking; tiling and untiling of scratchpad application
* Automatically launch application if it's not running
* Multi-monitor awareness
    * switching of dropdown window to active monitor when it's already open
    * maximum of 1 scratchpad application per monitor
* Multi-workspace awareness
    * when toggling application on workspace X, switching to workspace Y and toggling application again, it switches instantly to workspace Y

## Installation
Set `hyprland_config` in `config.json` to a config file loaded into your main `hyprland.conf` using the `source` command.  
```
source=~/.config/hypr/extra_keybinds.conf
```

## Usage
```
usage: hyprland-dropdown [-h] [-t TOGGLE] [-l] [-r] [-c CONFIG]

Make anything a scratchpad on Hyprland!

optional arguments:
  -h, --help            show this help message and exit
  -t TOGGLE, --toggle TOGGLE
                        toggle application by id
  -l, --lock            toggle lock active (defined) application
  -r, --reload
  -c CONFIG, --config CONFIG
                        custom config path
```


## Tips and Tricks

* Use `hyprctl clients` to find out the classes for the running applications