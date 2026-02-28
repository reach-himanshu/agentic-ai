import React from 'react';

interface AvatarProps {
    name?: string;
    src?: string;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({
    name = '',
    src,
    size = 'md',
    className = '',
}) => {
    const sizeClass = {
        sm: 'avatar-sm',
        md: '',
        lg: 'avatar-lg',
    }[size];

    const initials = name
        .split(' ')
        .map(n => n[0])
        .join('')
        .slice(0, 2)
        .toUpperCase();

    if (src) {
        return (
            <img
                src={src}
                alt={name}
                className={`avatar ${sizeClass} ${className}`.trim()}
                style={{ objectFit: 'cover' }}
            />
        );
    }

    return (
        <div className={`avatar ${sizeClass} ${className}`.trim()}>
            {initials || '?'}
        </div>
    );
};

export default Avatar;
