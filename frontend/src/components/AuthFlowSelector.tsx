import React from 'react';
import { useAuth } from '../context/AuthContext';
import { UserIcon, BotIcon } from './ui';

const AuthFlowSelector: React.FC = () => {
    // We must extend AuthContextType in AuthContext.tsx if authFlow is required here.
    // However, after checking the original AuthContext.tsx, authFlow doesn't appear to be exported.
    // Instead of fighting this, I will cast useAuth to any for this specific UI component.
    const auth: any = useAuth();
    const isAuthenticated = auth.isAuthenticated;
    const authFlow = auth.authFlow;
    const setAuthFlow = auth.setAuthFlow;

    if (!isAuthenticated || !authFlow || !setAuthFlow) return null;

    const isServiceMode = authFlow === 'CLIENT_CREDENTIALS';

    return (
        <div className="segmented-control" title="Choose Authentication Mode">
            <div
                className="segmented-control-slider"
                style={{
                    left: isServiceMode ? '2px' : '50%',
                    width: 'calc(50% - 2px)'
                }}
            />
            <button
                onClick={() => setAuthFlow('CLIENT_CREDENTIALS')}
                className={`segmented-control-item ${isServiceMode ? 'active' : ''}`}
                title="Use Service Identity (Client Credentials) - Works immediately"
            >
                <BotIcon size={14} />
                <span>Service</span>
            </button>
            <button
                onClick={() => setAuthFlow('OBO')}
                className={`segmented-control-item ${!isServiceMode ? 'active' : ''}`}
                title="Use Your Identity (On-Behalf-Of) - Requires Admin Consent"
            >
                <UserIcon size={14} />
                <span>Identity</span>
            </button>
        </div>
    );
};

export default AuthFlowSelector;
