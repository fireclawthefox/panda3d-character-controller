# Panda3D Character Controller
An extensive character controller system to be used with the Panda3D engine

## Features
- Walking/Running
- Sprinting
- Jumping
- Climbing
- Wall run
- Ledge grab
- player stamina handling
- P3D integrated physics
- first person camera system
- third person camera system
- JSON configuration file


## Install
Install the character controller via pip

```bash
pip install panda3d-character-controller
```

## How to use
Using the character controller itself is quite easy, simply instantiate it and
call the startPlayer function. You can set it's start position and rotation
using the setStartPos and setStartHpr functions.

```python3
base.cTrav = CollisionTraverser("base collision traverser")
base.cTrav.setRespectPrevTransform(True)

# actual character setup
player = PlayerController(base.cTrav, "path/to/config.json")
# start the player
player.startPlayer()
```

### Config
Configuration of the player is done in a json file that has to be passed to the
controllers constructor.
Simply copy and tweak the config file which can be found in the data folder.
For further information see the PDF documentation.

### PDF Documentation
An extensive documentation about the character controller can be found in the
doc Folder.
