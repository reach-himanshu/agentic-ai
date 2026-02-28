import React from 'react';
import { useAuth } from '../context/AuthContext';
import { UserIcon, BotIcon } from './ui';

const AuthFlowSelector: React.FC = () => {
    const { authFlow, setAuthFlow, isAuthenticated } = useAuth();

    if (!isAuthenticated) return null;

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
