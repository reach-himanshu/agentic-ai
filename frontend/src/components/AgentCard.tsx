/**
 * AgentCard Component - Display available agents for selection
 */

import React from 'react';
import type { AgentInfo } from '../services/agentService';

interface AgentCardProps {
    agent: AgentInfo;
    isSelected?: boolean;
    isLocked?: boolean;
    onSelect?: (agentId: string) => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({
    agent,
    isSelected = false,
    isLocked = false,
    onSelect,
}) => {
    const handleClick = () => {
        if (!isLocked && onSelect) {
            onSelect(agent.id);
        }
    };

    return (
        <div
            className={`agent-card ${isSelected ? 'agent-card--selected' : ''} ${isLocked ? 'agent-card--locked' : ''}`}
            onClick={handleClick}
            role="button"
            tabIndex={isLocked ? -1 : 0}
            aria-disabled={isLocked}
        >
            <div className="agent-card__icon">{agent.icon}</div>
            <div className="agent-card__content">
                <h3 className="agent-card__name">{agent.name}</h3>
                <p className="agent-card__description">{agent.description}</p>
                <div className="agent-card__systems">
                    {agent.systems.map((system) => (
                        <span key={system} className="agent-card__system-tag">
                            {system}
                        </span>
                    ))}
                </div>
                {isLocked && agent.reason && (
                    <p className="agent-card__locked-reason">🔒 {agent.reason}</p>
                )}
            </div>
            {isSelected && !isLocked && (
                <div className="agent-card__selected-indicator">✓</div>
            )}
        </div>
    );
};

interface AgentSelectorProps {
    availableAgents: AgentInfo[];
    lockedAgents?: AgentInfo[];
    selectedAgentId?: string;
    onSelectAgent: (agentId: string) => void;
    showLocked?: boolean;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
    availableAgents,
    lockedAgents = [],
    selectedAgentId,
    onSelectAgent,
    showLocked = false,
}) => {
    return (
        <div className="agent-selector">
            <h2 className="agent-selector__title">Available Agents</h2>
            <div className="agent-selector__grid">
                {availableAgents.map((agent) => (
                    <AgentCard
                        key={agent.id}
                        agent={agent}
                        isSelected={agent.id === selectedAgentId}
                        onSelect={onSelectAgent}
                    />
                ))}
            </div>

            {showLocked && lockedAgents.length > 0 && (
                <>
                    <h3 className="agent-selector__locked-title">
                        Locked Agents
                        <span className="agent-selector__locked-hint">
                            Contact your manager for access
                        </span>
                    </h3>
                    <div className="agent-selector__grid agent-selector__grid--locked">
                        {lockedAgents.map((agent) => (
                            <AgentCard
                                key={agent.id}
                                agent={agent}
                                isLocked
                            />
                        ))}
                    </div>
                </>
            )}
        </div>
    );
};

export default AgentCard;
