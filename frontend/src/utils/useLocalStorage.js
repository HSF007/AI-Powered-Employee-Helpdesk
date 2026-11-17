import { useEffect, useState } from "react";

// Remembers small UI values (employee contact, staff name) between visits.
export function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(key);
      return stored !== null ? JSON.parse(stored) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* storage unavailable - value just won't persist */
    }
  }, [key, value]);

  return [value, setValue];
}