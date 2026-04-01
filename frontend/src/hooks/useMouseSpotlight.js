import { useState, useCallback } from 'react';

export function useMouseSpotlight() {
  const [pos, setPos] = useState({ x: 0, y: 0 });

  const onMouseMove = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }, []);

  const spotlightStyle = {
    background: `radial-gradient(300px circle at ${pos.x}px ${pos.y}px, rgba(94,106,210,0.12), transparent)`,
  };

  return { onMouseMove, spotlightStyle };
}
