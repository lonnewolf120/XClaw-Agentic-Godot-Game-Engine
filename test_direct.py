import asyncio
import os
import sys

sys.path.append(os.path.abspath("vibe-game-engine"))
from api.plugin_bridge import create_proposal, ProposalRequest, NodeContext

async def main():
    req = ProposalRequest(
        prompt="Create a Label under selected node and set text/visibility",
        selection=[NodeContext(name="Root", path=".", **{"class": "Node3D"})],
        current_scene_path="res://main.tscn"
    )
    res = await create_proposal(req)
    print("PROPOSAL:", res)

if __name__ == "__main__":
    asyncio.run(main())
