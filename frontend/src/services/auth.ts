// Mock Authentication Service for Entra ID Simulation
// In production, this would use @azure/msal-browser or similar

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
}

// Mock users for demo purposes
const MOCK_USERS: Record<string, User> = {
    'admin@contoso.com': {
        id: '1',
        email: 'admin@contoso.com',
        name: 'Alex Admin',
        roles: ['APP_ROLE_ADMIN', 'APP_ROLE_SALES'],
    },
    'sales@contoso.com': {
        id: '2',
        email: 'sales@contoso.com',
        name: 'Sarah Sales',
        roles: ['APP_ROLE_SALES'],
    },
    'viewer@contoso.com': {
        id: '3',
        email: 'viewer@contoso.com',
        name: 'Victor Viewer',
        roles: ['APP_ROLE_VIEWER'],
    },
    'user@contoso.com': {
        id: '4',
        email: 'user@contoso.com',
        name: 'General User',
        roles: ['APP_ROLE_USER'],
    },
};

// Map emails to backend mock tokens
const EMAIL_TO_TOKEN: Record<string, string> = {
    'admin@contoso.com': 'mock-admin-token',
    'sales@contoso.com': 'mock-sales-token',
    'viewer@contoso.com': 'mock-viewer-token',
    'user@contoso.com': 'mock-user-token',
};

// Generate a mock JWT-like token (not a real JWT, just for demo)
const generateMockToken = (user: User): string => {
    // For POC, return the hardcoded token the backend expects
    if (EMAIL_TO_TOKEN[user.email]) {
        return EMAIL_TO_TOKEN[user.email];
    }
    const payload = {
        sub: user.id,
        email: user.email,
        name: user.name,
        roles: user.roles,
        iat: Date.now(),
        exp: Date.now() + 3600000, // 1 hour expiry
    };
    return btoa(JSON.stringify(payload));
};

// Parse mock token
export const parseToken = (token: string): User | null => {
    try {
        const payload = JSON.parse(atob(token));
        if (payload.exp < Date.now()) {
            return null; // Token expired
        }
        return {
            id: payload.sub,
            email: payload.email,
            name: payload.name,
            roles: payload.roles,
        };
    } catch {
        return null;
    }
};

// Storage keys
const TOKEN_KEY = 'agent_ui_token';
const USER_KEY = 'agent_ui_user';
const MODEL_KEY = 'agent_ui_model';

// Get stored auth state
export const getStoredAuth = (): AuthState => {
    const token = localStorage.getItem(TOKEN_KEY);
    const userJson = localStorage.getItem(USER_KEY);
    const modelId = localStorage.getItem(MODEL_KEY) || undefined;

    if (token && userJson) {
        const user = parseToken(token);
        if (user) {
            return {
                isAuthenticated: true,
                user,
                accessToken: token,
                isLoading: false,
                selectedModelId: modelId,
            };
        }
    }

    return {
        isAuthenticated: false,
        user: null,
        accessToken: null,
        isLoading: false,
        selectedModelId: modelId,
    };
};

// Sign in with mock Entra ID
export const signInWithEntraId = async (email?: string, modelId?: string): Promise<AuthState> => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Use provided email or default to admin
    const userEmail = email || 'admin@contoso.com';
    const user = MOCK_USERS[userEmail];

    if (!user) {
        throw new Error('User not found');
    }

    const token = generateMockToken(user);

    // Store in localStorage (in production, use secure storage)
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    if (modelId) {
        localStorage.setItem(MODEL_KEY, modelId);
    }

    return {
        isAuthenticated: true,
        user,
        accessToken: token,
        isLoading: false,
        selectedModelId: modelId
    };
};

// Sign out
export const signOut = (): AuthState => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(MODEL_KEY);

    return {
        isAuthenticated: false,
        user: null,
        accessToken: null,
        isLoading: false,
    };
};

// Check if user has a specific role
export const hasRole = (user: User | null, role: string): boolean => {
    return user?.roles.includes(role) ?? false;
};

// Check if user has any of the specified roles
export const hasAnyRole = (user: User | null, roles: string[]): boolean => {
    return roles.some(role => hasRole(user, role));
};

export default {
    getStoredAuth,
    signInWithEntraId,
    signOut,
    hasRole,
    hasAnyRole,
    parseToken,
};
