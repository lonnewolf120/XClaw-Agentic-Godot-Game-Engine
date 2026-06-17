/**************************************************************************/
/*  editor_ai_actions.h                                                   */
/**************************************************************************/
/*                         This file is part of:                          */
/*                             GODOT ENGINE                               */
/*                        https://godotengine.org                         */
/**************************************************************************/

#ifndef EDITOR_AI_ACTIONS_H
#define EDITOR_AI_ACTIONS_H

#include "core/object/class_db.h"
#include "core/object/object.h"

class Node;

class EditorAIActions : public Object {
	GDCLASS(EditorAIActions, Object);

	static EditorAIActions *singleton;

protected:
	static void _bind_methods();

public:
	static EditorAIActions *get_singleton();

	void begin_transaction(const String &p_name);
	Array apply_action_batch(const Array &p_batch);
	Array preview_action_batch(const Array &p_batch);
	void rollback_transaction();
	void commit_transaction();

	// Semantic mutation hooks
	Dictionary create_node(const String &p_parent_path, const String &p_type, const String &p_name);
	Dictionary remove_node(const String &p_node_path);
	void reparent_node(const String &p_node_path, const String &p_new_parent_path);
	Dictionary rename_node(const String &p_node_path, const String &p_new_name);
	Dictionary set_property(const String &p_node_path, const String &p_property, const Variant &p_value);
	void attach_script(const String &p_node_path, const String &p_script_path);
	void connect_signal(const String &p_source_path, const String &p_signal, const String &p_target_path, const String &p_method);
	Node *instantiate_packed_scene(const String &p_parent_path, const String &p_scene_path, const String &p_name);

	// Diagnostics API
	Array get_script_diagnostics(const String &p_script_path);

	// Probe Report
	Dictionary run_runtime_probe(int p_frame_count);

	EditorAIActions();
	~EditorAIActions();
};

#endif // EDITOR_AI_ACTIONS_H
