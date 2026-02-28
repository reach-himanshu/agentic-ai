import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useMsal, useAccount } from "@azure/msal-react";
import { loginRequest, tokenRequest } from "../authConfig";
import { agentSocket } from '../services/agentSocket';

// Dev mode check - set VITE_DEV_MODE=true in .env to enable
const isDevMode = import.meta.env.VITE_DEV_MODE === 'true';

export interface User {
    id: string;
    email: string;
    name: string;
    roles: string[];
    avatar?: string;
}

export interface AuthState {
    isAuthenticated: boolean;
    user: User | null;
    accessToken: string | null;
    isLoading: boolean;
    selectedModelId?: string;
    isDevMode?: boolean;
}

interface AuthContextType extends AuthState {
    signIn: (email?: string, modelId?: string) => Promise<void>;
    signInDev: () => void;
    signOut: () => void;
    hasRole: (role: string) => boolean;
    hasAnyRole: (roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Mock user for dev mode
const DEV_USER: User = {
    id: 'dev-user-001',
    email: 'dev@localhost',
    name: 'Dev User',
    roles: ['admin', 'user'],
};

const DEV_TOKEN = 'MOCK_TOKEN_DEV_MODE';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { instance, accounts, inProgress } = useMsal();
    const account = useAccount(accounts[0] || null);

    const [selectedModelId, setSelectedModelId] = useState<string | undefined>(() => {
        return localStorage.getItem('agent_ui_model') || undefined;
    });

    // Dev mode state
    const [devModeActive, setDevModeActive] = useState<boolean>(() => {
        return localStorage.getItem('agent_ui_dev_mode') === 'true';
    });

    const [accessToken, setAccessToken] = useState<string | null>(() => {
        // Restore dev token if dev mode was active
        if (localStorage.getItem('agent_ui_dev_mode') === 'true') {
            return DEV_TOKEN;
        }
        return null;
    });

    const isAuthenticated = !!account || devModeActive;
    const isLoading = inProgress !== "none";

    // Reconstruct user object from MSAL account or dev mode mock
    const user: User | null = devModeActive ? DEV_USER : (account ? {
        id: account.localAccountId,
        email: account.username,
        name: account.name || account.username,
        roles: (account.idTokenClaims?.roles as string[]) || [],
    } : null);

    // Handle dev mode socket auth
    useEffect(() => {
        if (devModeActive) {
            agentSocket.setAuthInfo(DEV_TOKEN, selectedModelId, 'DEV', DEV_USER.name, DEV_USER.roles);
        }
    }, [devModeActive, selectedModelId]);


    // Handle token acquisition and socket updates for MSAL
    useEffect(() => {
        if (!!account && user) {
            instance.acquireTokenSilent({
                ...tokenRequest,
                account: account
            }).then(response => {
                setAccessToken(response.accessToken);
                // Auth flow is now managed per-service in the backend, we pass 'OBO' as default hint
                agentSocket.setAuthInfo(response.accessToken, selectedModelId, 'OBO', user.name, user.roles);
            }).catch(error => {
                console.error("Token acquisition failed:", error);
            });
        }
    }, [account, instance, selectedModelId, user, accessToken]);

    const signIn = useCallback(async (email?: string, modelId?: string) => {
        if (modelId) {
            setSelectedModelId(modelId);
            localStorage.setItem('agent_ui_model', modelId);
        }

        try {
            await instance.loginPopup({
                ...loginRequest,
                loginHint: email
            });
        } catch (error) {
            console.error("Login failed:", error);
            throw error;
        }
    }, [instance]);

    // Dev mode login - bypasses MSAL entirely
    const signInDev = useCallback(() => {
        setDevModeActive(true);
        setAccessToken(DEV_TOKEN);
        localStorage.setItem('agent_ui_dev_mode', 'true');
        agentSocket.setAuthInfo(DEV_TOKEN, selectedModelId, 'DEV', DEV_USER.name, DEV_USER.roles);
    }, [selectedModelId]);

    const signOut = useCallback(() => {
        // Handle dev mode logout
        if (devModeActive) {
            setDevModeActive(false);
            localStorage.removeItem('agent_ui_dev_mode');
        }
        if (!!account) {
            instance.logoutPopup().catch(e => console.error(e));
        }
        setAccessToken(null);
        localStorage.removeItem('agent_ui_model');
        localStorage.removeItem('agent_ui_auth_flow');
        localStorage.removeItem('agent_ui_mock_user');
        localStorage.removeItem('agent_ui_mock_token');
    }, [instance, account, devModeActive]);

    const hasRole = useCallback((role: string): boolean => {
        return user?.roles.includes(role) ?? false;
    }, [user]);

    const hasAnyRole = useCallback((roles: string[]): boolean => {
        return roles.some(role => user?.roles.includes(role));
    }, [user]);

    const value: AuthContextType = {
        isAuthenticated,
        user,
        accessToken,
        isLoading,
        selectedModelId,
        isDevMode,
        signIn,
        signInDev,
        signOut,
        hasRole,
        hasAnyRole,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
