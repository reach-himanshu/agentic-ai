import React from 'react';
import { useTheme, type ThemeType } from '../context/ThemeContext';
import { XIcon, CheckIcon } from '../components/ui';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const THEMES: { id: ThemeType; name: string; description: string; colors: string[] }[] = [
    {
        id: 'original',
        name: 'Original',
        description: 'Current modern glow aesthetic',
        colors: ['#0a0a0f', '#6366f1']
    },
    {
        id: 'midnight-orange',
        name: 'Midnight Orange',
        description: 'Bold Armanino orange on black',
        colors: ['#000000', '#DA720F']
    },
    {
        id: 'clean-professional',
        name: 'Clean Professional',
        description: 'Light trusted consulting look',
        colors: ['#F9F9F9', '#949300']
    },
    {
        id: 'slate-corporate',
        name: 'Slate Corporate',
        description: 'Balanced slate and teal',
        colors: ['#222222', '#007681']
    },
    {
        id: 'clear-light',
        name: 'Clear Light',
        description: 'WCAG AAA high-contrast light',
        colors: ['#ffffff', '#0056b3']
    },
    {
        id: 'graphite-dark',
        name: 'Graphite Dark',
        description: 'WCAG AAA high-contrast dark',
        colors: ['#121218', '#4da6ff']
    }
];

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
    const { theme, setTheme } = useTheme();

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            <div className="glass-card w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-6 border-bottom flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold">Preferences</h2>
                        <p className="text-xs text-muted">Customize your workspace</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/10 rounded-full transition-colors"
                    >
                        <XIcon size={20} />
                    </button>
                </div>

                <div className="p-6">
                    <label className="label mb-4 block">Interface Theme</label>
                    <div className="grid grid-cols-1 gap-3">
                        {THEMES.map((t) => (
                            <button
                                key={t.id}
                                onClick={() => setTheme(t.id)}
                                className={`flex items-center gap-4 p-4 rounded-xl border text-left transition-all hover:translate-x-1 ${theme === t.id
                                    ? 'border-[var(--color-accent-primary)] bg-[var(--color-accent-primary-bg)]'
                                    : 'border-white/5 bg-white/5 hover:border-white/20'
                                    }`}
                                style={{
                                    backgroundColor: theme === t.id ? 'rgba(var(--color-accent-primary-rgb), 0.1)' : undefined
                                }}
                            >
                                <div className="flex -space-x-2">
                                    {t.colors.map((c, i) => (
                                        <div
                                            key={i}
                                            className="w-8 h-8 rounded-full border border-white/20 shadow-sm"
                                            style={{ backgroundColor: c }}
                                        />
                                    ))}
                                </div>
                                <div className="flex-1">
                                    <div className="font-semibold text-sm">{t.name}</div>
                                    <div className="text-[10px] text-muted uppercase tracking-wider">{t.description}</div>
                                </div>
                                {theme === t.id && (
                                    <div className="w-5 h-5 rounded-full bg-[var(--color-accent-primary)] flex items-center justify-center">
                                        <CheckIcon size={12} className="text-white" />
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="p-6 bg-black/20 text-center">
                    <p className="text-[10px] text-muted uppercase tracking-widest">
                        Armanino Brand Guidelines © 2026
                    </p>
                </div>
            </div>
        </div>
    );
};
