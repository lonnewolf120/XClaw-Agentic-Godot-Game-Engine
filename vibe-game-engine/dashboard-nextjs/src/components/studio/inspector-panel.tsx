import React from 'react';

export function InspectorPanel({ nodes = [] }: { nodes?: any[] }) {
  return (
    <div className="flex flex-col h-full bg-gray-900 text-gray-200">
      <div className="p-3 border-b border-gray-800 bg-gray-800 font-semibold text-xs uppercase tracking-wider">
        Scene Hierarchy
      </div>
      <div className="p-4 flex-1 overflow-auto">
        {nodes.length === 0 ? (
          <div className="text-gray-500 italic text-center mt-4">No nodes loaded</div>
        ) : (
          <ul className="space-y-1">
            {nodes.map((node, i) => (
              <li key={i} className="text-sm font-mono flex items-center space-x-2 p-1 hover:bg-gray-800 rounded cursor-pointer transition-colors">
                <span className="text-blue-400">❖</span>
                <span>{node.name}</span>
                {node.type && <span className="text-gray-500 text-xs ml-2">({node.type})</span>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
