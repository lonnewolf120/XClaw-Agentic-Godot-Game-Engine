# AI Autonomous Agent (for Godot 4.0+)

**AI Autonomous Agent** is a powerful plugin that embeds an autonomous coding agent directly into the Godot Editor. Unlike simple chat wrappers, this agent has **agency**: it can read your project files, write code, list directories, and even check for syntax errors in your logs autonomously to complete complex tasks.

## Features

*   **Agency**: The agent can plan and execute multi-step tasks.
*   **File System Access**: Can list directories and read any file in your project.
*   **Code Writing**: Can create new scripts or modify existing ones.
*   **Scene Editing**: Can create and modify (.tscn) scenes, including nodes, properties, and hierarchy.
*   **Syntax Checking**: Automatically verifies code for errors before finishing a task.
*   **Context Aware**: Knows it is working inside Godot and uses GDScript best practices.

## ⚠️ Important

*   **Full Access**: The agent has **complete control** over your project's file system, including the ability to **delete files and folders** if it deems necessary. **Always use version control (Git)** to safeguard your work.
*   **Model Recommendation**: To get the best results, use advanced APIs capable of complex reasoning ("thinking"). Simpler models may act "dumb" or fail to use tools correctly. We highly recommend using **Gemini 2.5 Pro**, which was used during testing.

## Installation and Use

1.  Copy the `ai_autonomous_agent` folder into your project's `addons/` directory.
2.  Enable the plugin in **Project > Project Settings > Plugins**.
3.  Open the **AI Agent** bottom panel.
4.  Configure your LLM provider and your API Key.
5.  Click **"New Agent"** in the bottom pannel to create your agent.
6.  Summon your agent.
7.  Type your request (e.g., *"Create a player controller with double jump"*).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Based on the **AI Assistant Hub** plugin originally created by **[Flamx Games](https://github.com/FlamxGames/godot-ai-assistant-hub)**.

---

**Author:** Vitor Zanatta Walter
