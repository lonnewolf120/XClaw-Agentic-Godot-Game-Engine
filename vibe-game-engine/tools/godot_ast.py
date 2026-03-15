from __future__ import annotations
import uuid
from typing import Dict, List, Optional, Any

class TscnNode:
    """Represents a Godot Scene Node for deterministic fast generation."""
    def __init__(self, name: str, type_name: str, parent: str = "", properties: Dict[str, Any] = None):
        self.name = name
        self.type_name = type_name
        self.parent = parent
        self.properties = properties or {}
    
    def serialize(self) -> str:
        header = f'[node name="{self.name}" type="{self.type_name}"'
        if self.parent:
            header += f' parent="{self.parent}"'
        header += "]\n"
        
        props_str = ""
        for k, v in self.properties.items():
            if isinstance(v, str):
                # Simple string quoting representation; real implementation would handle Vector3, etc.
                props_str += f'{k} = "{v}"\n'
            elif isinstance(v, bool):
                props_str += f'{k} = {"true" if v else "false"}\n'
            else:
                props_str += f'{k} = {v}\n'
        
        return header + props_str

class GodotSceneBuilder:
    """
    Cost-saving programmatic builder for Godot scenes.
    Instead of burning LLM tokens to meticulously craft .tscn spacing, 
    the system builds valid Godot scenes programmatically.
    """
    def __init__(self):
        self.nodes: List[TscnNode] = []
        self.ext_resources: List[Dict[str, str]] = []
        # Fallback empty uid
        self.uid = f"uid://{uuid.uuid4().hex[:12]}" 

    def add_ext_resource(self, path: str, resource_type: str = "Script") -> str:
        res_id = f"{len(self.ext_resources) + 1}_xxxxx"
        self.ext_resources.append({
            "path": path,
            "type": resource_type,
            "id": res_id
        })
        return f'ExtResource("{res_id}")'

    def add_node(self, name: str, type_name: str, parent: str = "", properties: Dict[str, Any] = None) -> TscnNode:
        node = TscnNode(name, type_name, parent, properties)
        self.nodes.append(node)
        return node

    def build_tscn(self) -> str:
        """Compiles the scene into a valid .tscn raw string."""
        lines = []
        lines.append(f'[gd_scene load_steps={len(self.ext_resources)+1} format=3 uid="{self.uid}"]\n')
        
        # Write external resources
        for res in self.ext_resources:
            lines.append(f'[ext_resource type="{res["type"]}" path="{res["path"]}" id="{res["id"]}"]\n')
        
        lines.append("")
        
        # Write nodes
        for node in self.nodes:
            lines.append(node.serialize())
            
        return "\n".join(lines)


def build_starter_platformer() -> str:
    """Pre-set standard platformer scaffold. Zero AI cost."""
    builder = GodotSceneBuilder()
    
    # Root Node
    builder.add_node("World", "Node3D")
    
    # Environment
    builder.add_node("DirectionalLight3D", "DirectionalLight3D", "World", {
        "transform": "Transform3D(-0.866025, -0.433013, 0.25, 0, 0.5, 0.866025, -0.5, 0.75, -0.433013, 0, 0, 0)",
        "shadow_enabled": True
    })
    
    # Generic Floor
    builder.add_node("Floor", "StaticBody3D", "World")
    builder.add_node("CollisionShape3D", "CollisionShape3D", "World/Floor")
    builder.add_node("MeshInstance3D", "MeshInstance3D", "World/Floor")
    
    # Player Script Binding
    script_ref = builder.add_ext_resource("res://scripts/player.gd", "Script")
    builder.add_node("Player", "CharacterBody3D", "World", {
        "script": script_ref,
        "transform": "Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2, 0)"
    })
    builder.add_node("CollisionShape3D", "CollisionShape3D", "World/Player")
    builder.add_node("Camera3D", "Camera3D", "World/Player", {
        "transform": "Transform3D(1, 0, 0, 0, 0.965926, 0.258819, 0, -0.258819, 0.965926, 0, 2.5, 5)"
    })

    return builder.build_tscn()
