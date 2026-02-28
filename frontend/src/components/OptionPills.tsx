import React from 'react';

export interface OptionPill {
    label: string;
    action: string;
    value: string;
    icon?: string;
}

export interface OptionPillsProps {
    options: OptionPill[];
    onSelect: (option: OptionPill) => void;
    disabled?: boolean;
}

export const OptionPills: React.FC<OptionPillsProps> = ({ options, onSelect, disabled = false }) => {
    return (
        <div className={`flex flex-wrap gap-2 mt-3 animate-in fade-in slide-in-from-bottom-2 duration-500 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
            {Array.isArray(options) && options.map((option, index) => (
                <button
                    key={`${option.value}-${index}`}
                    onClick={() => onSelect(option)}
                    className="px-4 py-2 rounded-full text-xs font-semibold transition-all border cursor-pointer hover:scale-105 active:scale-95 flex items-center gap-2"
                    style={{
                        backgroundColor: 'rgba(var(--color-accent-primary-rgb), 0.1)',
                        borderColor: 'rgba(var(--color-accent-primary-rgb), 0.3)',
                        color: 'var(--color-accent-primary)',
                        backdropFilter: 'blur(10px)',
                    }}
                >
                    {option.label}
                </button>
            ))}
        </div>
    );
};
