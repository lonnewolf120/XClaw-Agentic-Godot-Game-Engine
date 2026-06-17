/**
 * JoinGameDialog.tsx — Modal overlay for entering a username and selecting
 * a character class (Wizard or Paladin) before joining the game.
 */

import React, { useState, Suspense } from 'react';

interface JoinGameDialogProps {
  onJoin: (username: string, characterClass: string) => void;
}

export const JoinGameDialog: React.FC<JoinGameDialogProps> = ({ onJoin }) => {
  const [username, setUsername] = useState('Adventurer');
  const [characterClass, setCharacterClass] = useState('Wizard');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const finalUsername = username.trim() || `Player${Math.floor(Math.random() * 1000)}`;
    onJoin(finalUsername, characterClass);
  };

  return (
    <div style={styles.overlay}>
      <form style={styles.dialog} onSubmit={handleSubmit}>
        <h2>Join Game</h2>
        <div style={styles.inputGroup}>
          <label htmlFor="username" style={styles.label}>Character Name:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            maxLength={16} // Limit username length
            style={styles.input}
          />
        </div>
        <div style={styles.inputGroup}>
          <label htmlFor="characterClass" style={styles.label}>Class:</label>
          <select
            id="characterClass"
            value={characterClass}
            onChange={(e) => setCharacterClass(e.target.value)}
            style={styles.select}
          >
            <option value="Wizard">Wizard</option>
            <option value="Paladin">Paladin</option>
            {/* Add more classes later */}
          </select>
        </div>
        <button type="submit" style={styles.button}>Join Game</button>
      </form>
    </div>
  );
};

// Styles for the dialog
const styles: { [key: string]: React.CSSProperties } = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  dialog: {
    backgroundColor: '#2a2a3a',
    padding: '30px',
    borderRadius: '8px',
    border: '1px solid #444',
    boxShadow: '0 5px 15px rgba(0, 0, 0, 0.5)',
    color: '#eee',
    width: '350px',
    textAlign: 'center',
  },
  inputGroup: {
    marginBottom: '20px',
    textAlign: 'left',
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    color: '#aaa',
    fontSize: '14px',
  },
  input: {
    width: 'calc(100% - 20px)',
    padding: '10px',
    border: '1px solid #555',
    borderRadius: '4px',
    backgroundColor: '#333',
    color: '#eee',
    fontSize: '16px',
  },
  select: {
     width: '100%',
     padding: '10px',
     border: '1px solid #555',
     borderRadius: '4px',
     backgroundColor: '#333',
     color: '#eee',
     fontSize: '16px',
  },
  button: {
    padding: '12px 25px',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: '#4a90e2',
    color: 'white',
    fontSize: '16px',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
  },
};

// Add hover effect dynamically if needed, or use CSS classes
// button:hover style: { backgroundColor: '#357abd' }
