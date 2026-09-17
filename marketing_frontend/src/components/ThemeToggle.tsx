import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../lib/ThemeContext';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="p-2.5 rounded-full bg-bg-surface precision-border hover:bg-bg-elevated transition-colors relative overflow-hidden group shadow-sm"
      aria-label="Toggle theme"
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={theme}
          initial={{ y: 20, opacity: 0, rotate: -90 }}
          animate={{ y: 0, opacity: 1, rotate: 0 }}
          exit={{ y: -20, opacity: 0, rotate: 90 }}
          transition={{ duration: 0.25, ease: "anticipate" }}
          className="text-brand-indigo"
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </motion.div>
      </AnimatePresence>
      <div className="absolute inset-0 bg-brand-indigo/5 scale-0 group-hover:scale-100 transition-transform rounded-full" />
    </button>
  );
};
