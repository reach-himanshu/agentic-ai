import React from 'react';
import { BotIcon, Avatar } from './ui';
import { APP_CONFIG } from '../config';
import { DataCard } from './DataCard';
import { DynamicForm } from './DynamicForm';
import { HierarchicalPills } from './HierarchicalPills';
import type { User } from '../context/AuthContext';
import { Loader2, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';

// Helper to parse timestamps, treating naive (no timezone) as UTC
const parseTimestamp = (timestamp: Date | string): Date => {
    if (timestamp instanceof Date) return timestamp;
    // If string doesn't include timezone info (+, Z, or offset), assume UTC
    const str = String(timestamp);
    if (!str.match(/[Z+\-]\d/)) {
        // No timezone info - append Z to treat as UTC
        return new Date(str + 'Z');
    }
    return new Date(str);
};

declare global {
    namespace JSX {
        interface IntrinsicElements {
            'md-block': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement>;
        }
    }
}
export type MessageType = 'user' | 'assistant' | 'system' | 'assistant_data' | 'assistant_manifest';

export interface Message {
    id: string;
    type: MessageType;
    content: string;
    timestamp: Date;
    data?: any[];                // Legacy fallback for assistant_data
    manifest?: {                // For structured UI Manifests
        componentType: 'table' | 'form' | 'hero' | 'pills' | 'markdown';
        payload: any;
    };
    component?: React.ReactNode;  // For direct component injection
    thinkingSteps?: { id: string, label: string, startTime: number, duration?: number, completed: boolean }[];
    isThinking?: boolean;        // True when this is a live "processing" placeholder
    liveThinkingSteps?: { id: string, label: string, startTime: number, duration?: number, completed: boolean }[];
    pillState?: { mode: 'areas' } | { mode: 'actions'; areaId: string } | { mode: 'breadcrumb'; areaId: string; actionLabel: string };
}

interface ChatMessageProps {
    message: Message;
    user?: User | null;
    readOnly?: boolean;
}

// Helper to safely render potentially complex objects (e.g., ServiceNow display objects or LLM hallucinations)
const SafeRender: React.FC<{ value: any }> = ({ value }) => {
    if (value === null || value === undefined) return null;

    let content = "";
    if (typeof value === 'object') {
        // Handle common structured response patterns
        if (value.text) content = value.text;
        else if (value.display_value) content = value.display_value;
        else content = JSON.stringify(value);
    } else {
        content = String(value);
    }

    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore - md-block is a web component
    return <md-block>{content}</md-block>;
};

const CollapsibleThinkingSteps: React.FC<{ steps: NonNullable<Message['thinkingSteps']> }> = ({ steps }) => {
    const [isExpanded, setIsExpanded] = React.useState(false);
    const completedCount = steps.filter(s => s.completed).length;
    const isComplete = completedCount === steps.length;

    // Calculate total duration from all steps
    const totalDuration = steps.reduce((sum, step) => sum + (step.duration || 0), 0);

    // Caption: "Thinking..." while active, "Thought for X s" when complete
    const caption = isComplete
        ? `Thought for ${totalDuration.toFixed(1)}s`
        : `Thinking...`;

    return (
        <div className={`thinking-steps-accordion mb-2 ${isExpanded ? 'expanded' : 'collapsed'}`}>
            <div
                className="thinking-accordion-header"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-2 flex-1">
                    <CheckCircle2 size={14} className="text-success" />
                    <span className="text-xs text-muted">
                        {caption}
                    </span>
                </div>
                {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </div>

            {isExpanded && (
                <div className="thinking-steps-list">
                    {steps.map((step, idx) => (
                        <div key={step.id || idx} className={`thinking-step-item ${step.completed ? 'completed' : 'active'}`}>
                            <div className="step-icon">
                                {step.completed ? (
                                    <CheckCircle2 size={12} className="text-success" />
                                ) : (
                                    <Loader2 className="animate-spin text-accent" size={12} />
                                )}
                            </div>
                            <span className="step-label">{step.label}</span>
                            {step.completed && step.duration !== undefined && (
                                <span className="step-duration">{step.duration.toFixed(1)}s</span>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, user, readOnly }) => {
    const { type, content, component, data, manifest, thinkingSteps, isThinking, liveThinkingSteps } = message;

    if (type === 'system') {
        return (
            <div className="message message-system">
                <SafeRender value={content} />
            </div>
        );
    }

    const isUser = type === 'user';

    // Determine which thinking steps to show (live or finalized)
    const stepsToShow = isThinking ? liveThinkingSteps : thinkingSteps;

    return (
        <div className={`message-container ${isUser ? 'message-container-user' : 'message-container-assistant'}`}>
            <div className="message-avatar">
                {isUser ? (
                    <Avatar name={user?.name || 'User'} size="sm" />
                ) : (
                    <div className="agent-avatar">
                        <BotIcon size={16} />
                    </div>
                )}
            </div>

            <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
                {!isUser ? (
                    <div className="message-header">
                        {APP_CONFIG.appName}
                    </div>
                ) : (
                    <div className="message-header user-label">
                        {user?.name || 'You'}
                    </div>
                )}
                <div className="message-content">
                    {/* Live processing indicator */}
                    {isThinking && liveThinkingSteps && liveThinkingSteps.length > 0 && (
                        <div className="live-processing-indicator">
                            <div className="flex items-center gap-3 mb-2">
                                {/* Elegant pulse ring animation - calm and deliberate */}
                                <div className="processing-pulse-container">
                                    <div className="processing-pulse-ring"></div>
                                    <div className="processing-pulse-ring"></div>
                                    <div className="processing-pulse-ring"></div>
                                    <div className="processing-pulse-core"></div>
                                </div>
                                <span className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Thinking...</span>
                            </div>
                            <div className="thinking-steps-list">
                                {liveThinkingSteps.map((step, idx) => (
                                    <div key={step.id || idx} className={`thinking-step-item ${step.completed ? 'completed' : 'active'}`}>
                                        <div className="step-icon">
                                            {step.completed ? (
                                                <CheckCircle2 size={12} className="text-success" />
                                            ) : (
                                                <div className="step-dot animate-pulse" />
                                            )}
                                        </div>
                                        <span className="step-label">{step.label}</span>
                                        {step.completed && step.duration !== undefined && (
                                            <span className="step-duration">{step.duration.toFixed(1)}s</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Finalized thinking steps (collapsible) */}
                    {!isThinking && stepsToShow && stepsToShow.length > 0 && (
                        <div className="mb-4">
                            <CollapsibleThinkingSteps steps={stepsToShow} />
                        </div>
                    )}

                    {/* Response content (with fade-in animation) */}
                    {content && (
                        <div className={!isThinking && !isUser ? 'fade-in-content' : ''}>
                            <SafeRender value={content} />
                        </div>
                    )}
                </div>

                <div className="message-footer">
                    <span className="message-timestamp">
                        {parseTimestamp(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                </div>

                {/* Render DataCard if structured data is present (Legacy) */}
                {type === 'assistant_data' && data && (
                    <DataCard data={data} title="Retrieved Data" />
                )}

                {/* Render Manifest-driven UI */}
                {type === 'assistant_manifest' && manifest && (
                    <div style={{ marginTop: 'var(--spacing-4)' }}>
                        {manifest.componentType === 'table' && (
                            <DataCard data={manifest.payload} title="Retrieved Results" />
                        )}
                        {manifest.componentType === 'form' && (
                            <DynamicForm
                                title={manifest.payload.title}
                                fields={manifest.payload.fields}
                                submitAction={manifest.payload.submitAction}
                                disabled={readOnly}
                                onSubmit={(values) => {
                                    if (readOnly) return;
                                    (window as any).dispatchChatAction({
                                        type: 'form_submit',
                                        action: manifest.payload.submitAction,
                                        messageId: message.id,
                                        values
                                    });
                                }}
                            />
                        )}
                        {manifest.componentType === 'pills' && (() => {
                            // Extract area IDs from manifest pills to filter HierarchicalPills
                            const manifestPills = Array.isArray(manifest.payload) ? manifest.payload : [];
                            const availableAreaIds = manifestPills
                                .filter((p: any) => p.action === 'select_area')
                                .map((p: any) => p.value);

                            return (
                                <HierarchicalPills
                                    disabled={readOnly}
                                    availableAreaIds={availableAreaIds.length > 0 ? availableAreaIds : undefined}
                                    onAction={(action, value, areaId, actionLabel) => {
                                        if (readOnly) return;
                                        (window as any).dispatchChatAction({
                                            type: 'pill_click',
                                            action: action,
                                            messageId: message.id,
                                            value: value,
                                            label: actionLabel,
                                            areaId: areaId
                                        });
                                    }}
                                />
                            );
                        })()}
                        {manifest.componentType === 'markdown' && (
                            <div className="text-sm opacity-90">
                                <SafeRender value={manifest.payload} />
                            </div>
                        )}
                        {/* Forms and Hero will be added next */}
                    </div>
                )}

                {/* Render generative UI component if present */}
                {component && (
                    <div style={{ marginTop: 'var(--spacing-4)' }}>
                        {component}
                    </div>
                )}

                {/* Show hierarchical navigation pills on all assistant messages (skip if manifest has its own pills component) */}
                {!isUser && !isThinking && !(manifest?.componentType === 'pills') && (
                    <HierarchicalPills
                        disabled={readOnly}
                        initialState={message.pillState}
                        onAction={(action, value, areaId, actionLabel) => {
                            if (readOnly) return;
                            (window as any).dispatchChatAction({
                                type: 'pill_click',
                                action: action,
                                messageId: message.id,
                                value: value,
                                label: actionLabel,
                                areaId: areaId
                            });
                        }}
                    />
                )}

                {/* Show pills during thinking too (but disabled) */}
                {!isUser && isThinking && (
                    <HierarchicalPills
                        disabled={true}
                        initialState={message.pillState}
                        onAction={() => { }}
                    />
                )}
            </div>
        </div>
    );
};

// Typing indicator component
export const TypingIndicator: React.FC = () => (
    <div className="message message-assistant" style={{ padding: 'var(--spacing-3) var(--spacing-4)' }}>
        <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
);

export default ChatMessage;
