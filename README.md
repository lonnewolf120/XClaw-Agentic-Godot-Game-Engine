# Vibe Coding Starter Pack: 3D Multiplayer

A lightweight 3D web-based multiplayer starter kit using Three.js, React, and SpacetimeDB. Perfect for building your own multiplayer games or interactive experiences with modern AI coding tools like Cursor and Claude Code.

[Demo Video](https://x.com/majidmanzarpour/status/1909810088426021192)

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | [SpacetimeDB](https://spacetimedb.com) (Rust) | 2.0.1 |
| Frontend | React | 19 |
| 3D Rendering | Three.js / React Three Fiber | 0.175 / 9.x |
| 3D Helpers | @react-three/drei | 10.x |
| Language | TypeScript | 5.7 |
| Build Tool | Vite | 6.x |

## Project Structure

```
├── client/                  # React + Three.js frontend
│   ├── public/models/       # FBX character models (Wizard, Paladin)
│   ├── src/
│   │   ├── components/      # GameScene, Player, DebugPanel, PlayerUI, JoinGameDialog
│   │   ├── generated/       # Auto-generated SpacetimeDB TypeScript bindings
│   │   ├── App.tsx          # Connection, input handling, game loop
│   │   └── simulation.ts    # Bot load-testing tool
│   └── package.json
├── server/                  # SpacetimeDB Rust module
│   └── src/
│       ├── lib.rs           # Tables, reducers, lifecycle handlers
│       ├── player_logic.rs  # Server-side movement calculation
│       └── common.rs        # Shared types (Vector3, InputState), constants
├── setup.sh                 # One-command setup script
├── CLAUDE.md                # AI assistant project context
└── README.md
```

## Features

- **3D Multiplayer Foundation**: Connected players see and interact with each other in real-time
- **Server-Authoritative Design**: SpacetimeDB Rust module handles all game state with client-side prediction
- **Character System**: Two character classes (Wizard & Paladin) with 14+ animations each
- **Modern Tech Stack**: React 19, TypeScript, Three.js, SpacetimeDB 2.0, Vite
- **Debug Tools**: Built-in debug panel to monitor game state, player positions, and animations
- **Load Testing**: Built-in simulation tool to spawn up to 100+ bot players
- **AI-Friendly**: Structured for effective use with AI coding assistants (Cursor rules + CLAUDE.md included)

## Getting Started

### Prerequisites

- **Rust** 1.93+ with `wasm32-unknown-unknown` target
- **Node.js** 22+ (via nvm)
- **SpacetimeDB CLI** 2.x

### Quick Start

```bash
git clone https://github.com/majidmanzarpour/vibe-coding-starter-pack-3d-multiplayer
cd vibe-coding-starter-pack-3d-multiplayer
sh setup.sh
```

Or install manually:

```bash
# 1. Install Rust (if needed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustup target add wasm32-unknown-unknown

# 2. Install Node.js via nvm (if needed)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
nvm install 22 && nvm use 22

# 3. Install SpacetimeDB CLI
curl -sSf https://install.spacetimedb.com | sh
export PATH="$HOME/.local/bin:$PATH"

# 4. Install dependencies and build
cd client && npm install && cd ..
cd server && spacetime build
spacetime generate --lang typescript --out-dir ../client/src/generated
```

### Running the Game

You need three terminals:

```bash
# Terminal 1: Start SpacetimeDB server
cd server
spacetime start

# Terminal 2: Publish the game module
cd server
spacetime publish vibe-multiplayer

# Terminal 3: Start the client dev server
cd client
npm run dev
```

Open http://localhost:5173 in your browser, enter a name, pick a class, and join.

### Regenerating Bindings

When you change server schema or reducers:

```bash
cd server
spacetime build
spacetime generate --lang typescript --out-dir ../client/src/generated
spacetime publish vibe-multiplayer
```

## Controls

| Key | Action |
|-----|--------|
| W, A, S, D | Move |
| Shift | Sprint |
| Space | Jump |
| Left Click | Attack |
| Mouse | Look / Camera direction |
| Mouse Wheel | Zoom |
| C | Toggle camera mode (Follow / Orbital) |

## Simulation / Load Testing

Spawn bot players to stress-test the server and see multiplayer in action:

```bash
cd client

# Default: 10 bots for 10 seconds
npm run simulate

# Custom: 50 bots for 30 seconds
npm run simulate -- 50 30
```

Open the browser client while bots are running to see them walking around the 3D scene.

## Architecture

```
Browser Client                    SpacetimeDB Server
┌─────────────────┐              ┌──────────────────┐
│  React + R3F    │   WebSocket  │  Rust WASM Module │
│  Three.js       │◄────────────►│  Tables + Reducers│
│  Input → Game   │  (ws://3000) │  Player Logic     │
│  Loop (20Hz)    │              │  Game Tick (1Hz)  │
└─────────────────┘              └──────────────────┘
```

- **Client** sends player input at 20Hz via `updatePlayerInput` reducer
- **Server** validates and updates state; changes auto-sync to all subscribed clients
- **Client-side prediction** provides responsive movement while awaiting server confirmation

## Customization

### Character Models

The included character models (Wizard & Paladin) can be:
1. Used as-is for a fantasy game
2. Replaced with your own models (vehicles, animals, robots, etc.)
3. Enhanced with additional animations

See `client/src/README_3D_MODELS.md` for details on working with the models.

### Game Mechanics

This starter provides the multiplayer foundation — now add your own game mechanics:
- Combat systems and projectiles
- Physics interactions
- Collectible items and inventory
- Levels and terrain
- Vehicles or special movement modes
- Game-specific objectives and scoring

## Development with AI Tools

This project is organized to work well with AI coding tools like [Claude Code](https://claude.ai/claude-code) and [Cursor](https://cursor.com):

1. **CLAUDE.md** included at the project root — gives Claude Code full context on architecture, SpacetimeDB v2 API patterns, and project conventions
2. **Cursor rules** in `.cursor/rules/techguide.mdc` — always-on technical guide for Cursor's AI features
3. Clear component separation and modular architecture make it easy to describe changes
4. TypeScript types and generated bindings help AI understand the codebase structure
5. Comments explain important technical patterns (client-side prediction, stale closure avoidance, etc.)

## About SpacetimeDB

This project is built on [SpacetimeDB](https://spacetimedb.com), a distributed database and serverless application framework designed for multiplayer games. SpacetimeDB provides:

- **Real-time Sync**: Database changes automatically push to connected clients
- **TypeScript Bindings**: Type-safe client code generated from your Rust server module
- **Server-Authoritative**: All game logic runs in the secure server environment
- **Game-Oriented**: Built with multiplayer patterns (subscriptions, reducers, identity) in mind

## License

MIT License — see [LICENSE](LICENSE) for details. Free to use, modify, and distribute for any purpose, including commercial applications.

## Acknowledgments

This starter pack is maintained by [Majid Manzarpour](https://x.com/majidmanzarpour) and is free to use for any project.
