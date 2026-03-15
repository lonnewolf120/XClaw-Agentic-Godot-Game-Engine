import React from 'react';

export function DiffPanel({ files = [] }: { files?: any[] }) {
  return (
    <div className="flex flex-col h-full bg-gray-900 text-gray-100 p-4">
      <h2 className="text-sm font-semibold mb-4 text-gray-300">File Changes</h2>
      <div className="flex-1 overflow-auto">
        {files.length === 0 ? (
          <div className="text-gray-500 text-sm flex items-center justify-center h-full">
            No changes detected
          </div>
        ) : (
          <div className="space-y-4">
            {files.map((file, index) => (
              <div key={index} className="border border-gray-700 rounded-md">
                <div className="bg-gray-800 px-3 py-2 text-xs font-mono border-b border-gray-700 font-medium">
                  {file.path}
                </div>
                <div className="p-2 font-mono text-xs overflow-x-auto">
                  {/* Simplistic diff visualization */ }
                  <div className="text-green-400">++ {file.added} additions</div>
                  <div className="text-red-400">-- {file.deleted} deletions</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
