import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "../api/client";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [connected, setConnected] = useState(null); // null = unknown/loading
  const [accountId, setAccountId] = useState(null);
  const [checking, setChecking] = useState(true);

  const refreshStatus = useCallback(async () => {
    try {
      const status = await api.connectionStatus();
      setConnected(status.connected);
    } catch {
      setConnected(false);
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  const connect = useCallback(async (apiKey, secretKey, paper) => {
    const result = await api.connect(apiKey, secretKey, paper);
    setConnected(result.connected);
    setAccountId(result.account_id);
    return result;
  }, []);

  const disconnect = useCallback(async () => {
    await api.disconnect();
    setConnected(false);
    setAccountId(null);
  }, []);

  return (
    <SessionContext.Provider value={{ connected, accountId, checking, connect, disconnect, refreshStatus }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
