import React from 'react';

interface BadgeProps {
    children: React.ReactNode;
    variant?: 'success' | 'warning' | 'error' | 'info' | 'outline';
    className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
    children,
    variant = 'info',
    className = '',
}) => {
    const variantClass = `badge-${variant}`;

    return (
        <span className={`badge ${variantClass} ${className}`.trim()}>
            {children}
        </span>
    );
};

export default Badge;
