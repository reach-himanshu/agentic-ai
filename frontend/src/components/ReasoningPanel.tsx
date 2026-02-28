import React, { useState } from 'react';
import './ReasoningPanel.css';

export interface ReasoningStep {
    id?: string;
    type: 'reasoning';
    stage: string;
    tool?: string;
    status: 'pending' | 'in_progress' | 'complete' | 'error';
    message: string;
    details?: Record<string, unknown>;
}

interface ReasoningPanelProps {
    steps: ReasoningStep[];
    isProcessing?: boolean;
}

// Map stages to icons and labels
const STAGE_CONFIG: Record<string, { icon: string; label: string }> = {
    intent_detection: { icon: '🎯', label: 'Intent Detection' },
    security_check: { icon: '🔒', label: 'Security Check' },
    tool_selection: { icon: '🔌', label: 'Tool Selection' },
    tool_execution: { icon: '⚙️', label: 'Tool Execution' },
    data_processing: { icon: '📊', label: 'Data Processing' },
    ui_generation: { icon: '🎨', label: 'UI Generation' },
    orchestration: { icon: '🤖', label: 'Agent Orchestration' },
    confirmation: { icon: '✋', label: 'Awaiting Confirmation' },
};

// Status indicators
const STATUS_ICON: Record<string, string> = {
    pending: '⏳',
    in_progress: '⚙️',
    complete: '✅',
    error: '❌',
};

const ReasoningPanel: React.FC<ReasoningPanelProps> = ({ steps, isProcessing }) => {
    const [expanded, setExpanded] = useState(false);

    if (steps.length === 0 && !isProcessing) {
        return null;
    }

    const completedCount = steps.filter(s => s.status === 'complete').length;
    const hasErrors = steps.some(s => s.status === 'error');

    return (
        <div className={`reasoning-panel ${expanded ? 'expanded' : 'collapsed'}`}>
            <button
                className="reasoning-toggle"
                onClick={() => setExpanded(!expanded)}
            >
                <span className="toggle-icon">{expanded ? '▼' : '▶'}</span>
                <span className="toggle-label">
                    Reasoning {isProcessing && '(processing...)'}
                </span>
                <span className={`step-count ${hasErrors ? 'has-errors' : ''}`}>
                    {completedCount}/{steps.length} steps
                </span>
            </button>

            {expanded && (
                <div className="reasoning-steps">
                    {steps.map((step, index) => {
                        const config = STAGE_CONFIG[step.stage] || { icon: '📋', label: step.stage };
                        const statusIcon = STATUS_ICON[step.status] || '⏳';

                        return (
                            <div
                                key={step.id || index}
                                className={`reasoning-step status-${step.status}`}
                            >
                                <div className="step-header">
                                    <span className="step-icon">{config.icon}</span>
                                    <span className="step-label">{config.label}</span>
                                    <span className="step-status">{statusIcon}</span>
                                </div>
                                <div className="step-message">{step.message}</div>
                                {step.tool && (
                                    <div className="step-tool">
                                        <code>{step.tool}</code>
                                    </div>
                                )}
                                {step.details && Object.keys(step.details).length > 0 && (
                                    <div className="step-details">
                                        {Object.entries(step.details).map(([key, value]) => (
                                            <span key={key} className="detail-item">
                                                <span className="detail-key">{key}:</span>
                                                <span className="detail-value">{String(value)}</span>
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                    {isProcessing && (
                        <div className="reasoning-step status-in_progress">
                            <div className="step-header">
                                <span className="step-icon">⏳</span>
                                <span className="step-label">Processing</span>
                                <span className="step-status pulsing">⚙️</span>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ReasoningPanel;
