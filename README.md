# 3D RPG Game with Enemy AI (UPBGE + Python)

A **3D third-person RPG game** built using the **Uchronia Project Blender Game Engine (UPBGE)** with Python scripting.  
The game features character combat, enemy AI with pathfinding, terrain streaming, and a database-backed save system.

The player explores a snowy terrain to **collect 8 magical keys and seal an evil force**, while fighting enemies that spawn across the map.

---

# Features

## Character System
- Third-person character controller with **WASD movement**
- Sprint, jump, slide, and attack mechanics
- Combat system with **raycast-based hit detection**
- Health, healing, and temporary stat boosts

## Enemy AI
- Enemy behavior implemented using a **finite state machine**
- States include:
  - Patrol
  - Chase
  - Attack
- Uses **A* pathfinding** to navigate terrain
- Enemies drop items when defeated

## Procedural Terrain Handling
- Large terrain with **dynamic physics mesh streaming**
- Uses **Blender Geometry Nodes** to load only nearby terrain physics
- Improves performance for large maps

## Camera System
- Third-person camera controlled by mouse movement
- Collision detection prevents camera clipping into terrain
- Smooth tracking around the player

## Game UI
- HUD displaying:
  - Health
  - Elixir count
  - Game status
- Menu system built using **UPBGE UI nodes**

## Save System
- Automatic game saves every **30 seconds**
- Uses **SQL database storage**
- Saves:
  - Player stats
  - Inventory
  - Object positions
  - Game state

## Item System
- Collectible items:
  - Keys
  - Elixirs
- Pickup detection using **proximity sensors**

---

# Tech Stack

### Game Engine
- UPBGE (Uchronia Project Blender Game Engine)

### Programming
- Python
- UPBGE Python Components

### Libraries
- `bge`
- `bpy`
- `json`
- `time`
- `textwrap`
- `uplogic.ui`

### Algorithms / Data Structures
- A* Pathfinding
- KDTree
- BVHTree
- Raycasting

### Database
- SQL database for save data

---

# Game Mechanics

## Player Objective

The player must:

1. Explore the world
2. Defeat enemies
3. Collect **8 keys**
4. Return them to the **altar**
5. Seal the evil power destroying the world

---

# Enemy AI System

Enemies operate using a **state machine**:

### Patrol
Enemy moves randomly within its spawn region using A* pathfinding.

### Chase
When the player enters detection range, the enemy generates a path toward the player.

### Attack
If close enough, the enemy attacks and deals damage.

---

# World Generation

The snowy terrain was created using **Blender landscape tools** and procedural noise.

Additional features:
- Tree and rock placement using **Geometry Nodes**
- Dynamic terrain physics mesh streaming
- HDRI sky environment

---

# Game Requirements

Minimum system requirements:

- **8 GB RAM**
- **OpenGL 4.3 compatible GPU**
- **4 GB VRAM**
- **Dual-core CPU (3 GHz or higher)**
- **1 GB free storage**

Supported platforms:
- Windows
- Linux

---

# Assets & Resources
- Some assets used in the project:
- Character models from Sketchfab
- Animations from Adobe Mixamo
- HDRI textures from PolyHaven


