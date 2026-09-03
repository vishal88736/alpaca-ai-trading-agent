import { createContext, useCallback, useContext, useState } from "react";

const ToastContext = createContext(null);

let idCounter = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (message, variant = "info") => {
      setToasts((prev) => {
        // Prevent duplicate messages
        if (prev.some((t) => t.message === message)) {
          return prev;
        }
        const id = ++idCounter;
        setTimeout(() => dismiss(id), 4000);
        return [...prev.slice(-2), { id, message, variant }];
      });
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div
        style={{
          position: "fixed",
          bottom: 20,
          right: 20,
          display: "flex",
          flexDirection: "column",
          gap: 10,
          zIndex: 1000,
          maxWidth: 360,
        }}
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className="card"
            role="status"
            style={{
              padding: "12px 16px",
              fontSize: 13,
              borderLeft: `3px solid ${
                t.variant === "error" ? "var(--sell)" : t.variant === "success" ? "var(--buy)" : "var(--accent)"
              }`,
            }}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
