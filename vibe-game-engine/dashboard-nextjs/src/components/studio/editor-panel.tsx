import React, { useState } from 'react';

export function EditorPanel({ fileContent = '', fileName = 'No file selected' }: { fileContent?: string; fileName?: string }) {
  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] text-gray-300">
      <div className="flex items-center justify-between px-4 py-2 bg-[#2d2d2d] border-b border-[#3e3e42]">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono">{fileName}</span>
        </div>
      </div>
      <div className="flex-1 overflow-auto p-4 font-mono text-sm leading-relaxed whitespace-pre-wrap">
        {fileContent ? (
          <code>{fileContent}</code>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500 italic">
            Select a file to view source
          </div>
        )}
      </div>
    </div>
  );
}
