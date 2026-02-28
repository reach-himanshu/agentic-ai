import React, { useState, useEffect } from 'react';

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
    // Specialized agents - shown based on backend entitlement
    {
        id: 'onboarding',
        label: 'Client Onboarding',
        icon: '🤝',
        pills: [
            { label: 'New Client', action: 'ask', value: 'I need to onboard a new client' },
            { label: 'Onboarding Checklist', action: 'ask', value: 'Show onboarding checklist' },
            { label: 'Client Setup', action: 'ask', value: 'Set up client in D365' },
        ]
    },
    {
        id: 'sales',
        label: 'Sales',
        icon: '🏢',
        pills: [
            { label: 'Search Accounts', action: 'ask', value: 'Search for a client account' },
            { label: 'Create Opportunity', action: 'ask', value: 'Create a new opportunity' },
            { label: 'Pipeline', action: 'ask', value: 'Show my sales pipeline' },
        ]
    },
];

export type PillState =
    | { mode: 'areas' }  // Show area pills only
    | { mode: 'actions'; areaId: string }  // Show area pills + action pills
    | { mode: 'breadcrumb'; areaId: string; actionLabel: string };  // Collapsed to breadcrumb

interface HierarchicalPillsProps {
    onAction: (action: string, value: string, areaId: string, actionLabel: string) => void;
    disabled?: boolean;
    initialState?: PillState;
    /** List of area IDs to show - filters AREA_CONFIGS based on backend entitlements */
    availableAreaIds?: string[];
}

export const HierarchicalPills: React.FC<HierarchicalPillsProps> = ({
    onAction,
    disabled = false,
    initialState = { mode: 'areas' },
    availableAreaIds
}) => {
    const [pillState, setPillState] = useState<PillState>(initialState);

    // Filter areas based on backend entitlements
    const visibleAreas = availableAreaIds
        ? AREA_CONFIGS.filter(area => availableAreaIds.includes(area.id))
        : AREA_CONFIGS;

    // Sync with initialState when it changes (e.g., from parent message)
    useEffect(() => {
        if (initialState) {
            setPillState(initialState);
        }
    }, [initialState?.mode, (initialState as any)?.areaId]);

    const handleAreaClick = (areaId: string) => {
        if (disabled) return;
        setPillState({ mode: 'actions', areaId });
    };

    const handleActionClick = (area: AreaConfig, pill: NavigationPill) => {
        if (disabled) return;
        // Collapse to breadcrumb and trigger action
        setPillState({ mode: 'breadcrumb', areaId: area.id, actionLabel: pill.label });
        onAction(pill.action, pill.value, area.id, pill.label);
    };

    const handleBack = () => {
        if (disabled) return;
        setPillState({ mode: 'areas' });
    };

    // Breadcrumb view - collapsed after action taken
    if (pillState.mode === 'breadcrumb') {
        const area = visibleAreas.find(a => a.id === pillState.areaId);
        return (
            <div className="hierarchical-pills-breadcrumb">
                <span className="breadcrumb-icon">📍</span>
                <span className="breadcrumb-text">
                    {area?.icon} {area?.label} → {pillState.actionLabel}
                </span>
            </div>
        );
    }

    const selectedArea = pillState.mode === 'actions'
        ? visibleAreas.find(a => a.id === pillState.areaId)
        : null;

    return (
        <div className={`hierarchical-pills ${disabled ? 'disabled' : ''}`}>
            {/* Level 1: Area Pills */}
            <div className="hierarchical-pills-row area-level">
                {visibleAreas.map(area => (
                    <button
                        key={area.id}
                        className={`h-pill area-pill ${selectedArea?.id === area.id ? 'active' : ''}`}
                        onClick={() => handleAreaClick(area.id)}
                        disabled={disabled}
                    >
                        <span className="h-pill-icon">{area.icon}</span>
                        <span className="h-pill-label">{area.label}</span>
                    </button>
                ))}
            </div>

            {/* Level 2: Action Pills (shown when area selected) */}
            {selectedArea && (
                <div className="hierarchical-pills-row action-level">
                    {selectedArea.pills.map((pill, idx) => (
                        <button
                            key={idx}
                            className="h-pill action-pill"
                            onClick={() => handleActionClick(selectedArea, pill)}
                            disabled={disabled}
                        >
                            {pill.label}
                        </button>
                    ))}
                    <button
                        className="h-pill back-pill"
                        onClick={handleBack}
                        disabled={disabled}
                    >
                        ← Back
                    </button>
                </div>
            )}
        </div>
    );
};

export default HierarchicalPills;
