import React from 'react';

interface SpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
    size = 'md',
    className = '',
}) => {
    const sizeClass = size === 'lg' ? 'spinner-lg' : '';

    return <div className={`spinner ${sizeClass} ${className}`.trim()} />;
};

export default Spinner;
