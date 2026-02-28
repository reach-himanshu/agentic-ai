import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    helperText?: string;
}

export const Input: React.FC<InputProps> = ({
    label,
    error,
    helperText,
    className = '',
    id,
    ...props
}) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
        <div className="input-wrapper">
            {label && (
                <label htmlFor={inputId} className="label">
                    {label}
                </label>
            )}
            <input
                id={inputId}
                className={`input ${error ? 'input-error' : ''} ${className}`.trim()}
                {...props}
            />
            {(error || helperText) && (
                <p className={`helper-text ${error ? 'helper-text-error' : ''}`}>
                    {error || helperText}
                </p>
            )}
        </div>
    );
};

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
    label?: string;
    error?: string;
    helperText?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
    label,
    error,
    helperText,
    className = '',
    id,
    ...props
}) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
        <div className="input-wrapper">
            {label && (
                <label htmlFor={inputId} className="label">
                    {label}
                </label>
            )}
            <textarea
                id={inputId}
                className={`input textarea ${error ? 'input-error' : ''} ${className}`.trim()}
                {...props}
            />
            {(error || helperText) && (
                <p className={`helper-text ${error ? 'helper-text-error' : ''}`}>
                    {error || helperText}
                </p>
            )}
        </div>
    );
};

export default Input;
