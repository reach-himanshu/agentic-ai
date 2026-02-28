import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button, MicrosoftIcon, SparklesIcon } from '../components/ui';

// Check dev mode from environment
const isDevModeEnabled = import.meta.env.VITE_DEV_MODE === 'true';

export const Login: React.FC = () => {
    const { signIn, signInDev, isLoading } = useAuth();
    const [error, setError] = useState<string | null>(null);

    const handleSignIn = async () => {
        setError(null);
        try {
            await signIn();
        } catch (err) {
            setError('Failed to sign in. Please try again.');
        }
    };

    const handleDevSignIn = () => {
        setError(null);
        signInDev();
    };

    return (
        <div className="login-container">
            <div className="login-card fade-in">
                {/* Logo */}
                <div className="login-logo">
                    <div className="login-logo-icon">
                        <SparklesIcon size={24} />
                    </div>
                    <span className="login-title">Ops IQ</span>
                </div>

                <p className="login-subtitle">
                    Your AI-powered assistant
                </p>

                {/* Error Message */}
                {error && (
                    <div
                        className="p-3 mb-4 rounded-lg text-sm"
                        style={{
                            background: 'var(--color-error-bg)',
                            color: 'var(--color-error)',
                            border: '1px solid var(--color-error)'
                        }}
                    >
                        {error}
                    </div>
                )}

                {/* Sign In Button */}
                <Button
                    variant="primary"
                    size="lg"
                    onClick={handleSignIn}
                    disabled={isLoading}
                    isLoading={isLoading}
                    leftIcon={!isLoading && <MicrosoftIcon size={20} />}
                    className="w-full"
                    style={{ width: '100%' }}
                >
                    {isLoading ? 'Signing in...' : 'Sign in with Entra ID'}
                </Button>

                {/* Dev Mode Login */}
                {isDevModeEnabled && (
                    <>
                        <div className="login-divider" style={{ margin: '16px 0' }}>
                            <span>or</span>
                        </div>
                        <Button
                            variant="secondary"
                            size="lg"
                            onClick={handleDevSignIn}
                            className="w-full"
                            style={{
                                width: '100%',
                                background: 'linear-gradient(135deg, #10b981, #059669)',
                                border: 'none',
                                color: 'white'
                            }}
                        >
                            🚀 Dev Login (Skip Auth)
                        </Button>
                    </>
                )}

                <div className="login-divider">
                    <span>Enterprise Secure</span>
                </div>

                {/* Info text */}
                <p
                    className="text-center text-xs"
                    style={{ color: 'var(--color-text-muted)' }}
                >
                    {isDevModeEnabled
                        ? 'Dev mode enabled. Use Dev Login to bypass authentication.'
                        : 'Secure authentication provided by Microsoft Entra ID.'}
                </p>
            </div>
        </div>
    );
};

export default Login;

