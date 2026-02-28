import React from 'react';

export interface NavigationPill {
    label: string;
    action: string;
    value: string;
    icon?: string;
}

export interface AreaConfig {
    id: string;
    label: string;
    icon: string;
    pills: NavigationPill[];
}

// Define available areas with their contextual pills
const AREA_CONFIGS: AreaConfig[] = [
    {
        id: 'knowledge_hub',
        label: 'Knowledge Hub',
        icon: '📚',
        pills: [
            { label: 'Search Policies', action: 'ask', value: 'Search company policies' },
            { label: 'Find Documents', action: 'ask', value: 'Help me find a document' },
        ]
    },
    {
        id: 'it_support',
        label: 'IT Support',
        icon: '🛠️',
        pills: [
            { label: 'Report Issue', action: 'ask', value: 'I need to report an IT issue' },
            { label: 'My Tickets', action: 'ask', value: 'Show my open IT tickets' },
            { label: 'Check Status', action: 'ask', value: 'Check status of a ticket' },
            { label: 'My Approvals', action: 'ask', value: 'Show my pending approvals' },
        ]
    },
    {
        id: 'hr',
        label: 'HR',
        icon: '👥',
        pills: [
            { label: 'My Timesheet', action: 'ask', value: 'Show my timesheet for this week' },
            { label: 'Log Time', action: 'ask', value: 'I need to log my time' },
            { label: 'PTO Balance', action: 'ask', value: 'What is my PTO balance?' },
            { label: 'HR Policy', action: 'ask', value: 'Find HR policy information' },
        ]
    },
];

interface NavigationPillsProps {
    currentArea: string | null;
    onAreaSelect: (areaId: string) => void;
    onActionSelect: (action: string, value: string) => void;
    onBack: () => void;
    disabled?: boolean;
}

export const NavigationPills: React.FC<NavigationPillsProps> = ({
    currentArea,
    onAreaSelect,
    onActionSelect,
    onBack,
    disabled = false,
}) => {
    const selectedAreaConfig = AREA_CONFIGS.find(a => a.id === currentArea);

    return (
        <div className={`navigation-pills-container ${disabled ? 'disabled' : ''}`}>
            {/* Level 1: Area Pills */}
            <div className="navigation-pills-row area-pills">
                {AREA_CONFIGS.map(area => (
                    <button
                        key={area.id}
                        className={`nav-pill area-pill ${currentArea === area.id ? 'active' : ''}`}
                        onClick={() => !disabled && onAreaSelect(area.id)}
                        disabled={disabled}
                    >
                        <span className="nav-pill-icon">{area.icon}</span>
                        <span className="nav-pill-label">{area.label}</span>
                    </button>
                ))}
            </div>

            {/* Level 2: Action Pills (shown when area is selected) */}
            {selectedAreaConfig && (
                <div className="navigation-pills-row action-pills">
                    {selectedAreaConfig.pills.map((pill, idx) => (
                        <button
                            key={idx}
                            className="nav-pill action-pill"
                            onClick={() => !disabled && onActionSelect(pill.action, pill.value)}
                            disabled={disabled}
                        >
                            {pill.label}
                        </button>
                    ))}
                    <button
                        className="nav-pill back-pill"
                        onClick={() => !disabled && onBack()}
                        disabled={disabled}
                    >
                        ← Back
                    </button>
                </div>
            )}
        </div>
    );
};

export default NavigationPills;
