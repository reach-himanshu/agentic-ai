import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { ChatMessage } from '../components/ChatMessage';
import type { Message } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { ConfirmationCard } from '../components/ConfirmationCard';
import type { ConfirmationCardData } from '../components/ConfirmationCard';
import { SessionSidebar } from '../components/SessionSidebar';
import { SettingsModal } from '../components/SettingsModal';
import { useAgents } from '../hooks/useAgents';
import {
    Button,
    Avatar,
    Badge,
    SparklesIcon,
    LogoutIcon,
    SettingsIcon
} from '../components/ui';
import { APP_CONFIG } from '../config';

const generateId = () => {
    // Use UUID4 for bulletproof session uniqueness across devices/users
    return crypto.randomUUID();
};

// Helper to parse timestamps, treating naive (no timezone) as UTC
const parseTimestamp = (timestamp: string | Date): Date => {
    if (timestamp instanceof Date) return timestamp;
    // If string doesn't include timezone info (+, Z, or offset), assume UTC
    const str = String(timestamp);
    if (!str.match(/[Z+\-]\d/)) {
        // No timezone info - append Z to treat as UTC
        return new Date(str + 'Z');
    }
    return new Date(str);
};

// Factory function to create welcome message with dynamic agent pills
const createWelcomeMessage = (
    sessionId: string,
    userName?: string,
    availableAgents?: { id: string; name: string; icon: string }[]
): Message => {
    // Base pill - always available
    const basePills = [
        { label: "📚 Knowledge Hub", action: "select_area", value: "knowledge_hub" },
    ];

    // Default agent pills (IT Support, HR) - everyone has these
    const defaultAgentPills = [
        { label: "🛠️ IT Support", action: "select_area", value: "it_support" },
        { label: "👥 HR", action: "select_area", value: "hr" },
    ];

    // Specialized agent pills - only if user is entitled
    const specializedAgentIds = ['sales', 'onboarding'];
    const specializedPills = (availableAgents || [])
        .filter(a => specializedAgentIds.includes(a.id))
        .map(a => ({
            label: `${a.icon} ${a.name.replace(' Agent', '')}`,
            action: "select_area",
            value: a.id
        }));

    // Combine all pills
    const allPills = [...basePills, ...defaultAgentPills, ...specializedPills];

    // Build greeting
    const userGreeting = userName ? `Hello **${userName}**! ` : "Hello! ";
    const helpText = "How can I help you today?";

    return {
        id: `welcome-${sessionId}`,
        type: 'assistant_manifest',
        content: `${userGreeting}${helpText}`,
        timestamp: new Date(),
        manifest: {
            componentType: 'pills',
            payload: allPills
        }
    };
};

export const Chat: React.FC = () => {
    const { user, signOut, hasRole, accessToken } = useAuth();
    const { availableAgents } = useAgents();
    const [sessionId, setSessionId] = useState<string>(() => {
        const saved = localStorage.getItem('ops_iq_session_id');
        return saved || generateId();
    });
    const sessionIdRef = useRef(sessionId);

    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isThinking, setIsThinking] = useState(false);
    const thinkingStepsRef = useRef<{ id: string, label: string, startTime: number, duration?: number, completed: boolean }[]>([]);
    const [consumedActions, setConsumedActions] = useState<Set<string>>(new Set());
    const [pendingConfirmation, setPendingConfirmation] = useState<ConfirmationCardData | null>(null);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);
    // Track last pill navigation state for continuity
    const lastPillStateRef = useRef<{ mode: 'areas' } | { mode: 'actions'; areaId: string } | { mode: 'breadcrumb'; areaId: string; actionLabel: string }>({ mode: 'areas' });

    // Auto-scroll using container scrollTop to avoid viewport jumps
    useEffect(() => {
        if (scrollContainerRef.current) {
            const { scrollHeight, clientHeight } = scrollContainerRef.current;
            scrollContainerRef.current.scrollTo({
                top: scrollHeight - clientHeight,
                behavior: 'smooth'
            });
        }
    }, [messages, isThinking]);

    // Persist session ID and track latest actionable session
    useEffect(() => {
        localStorage.setItem('ops_iq_session_id', sessionId);
        sessionIdRef.current = sessionId; // Sync ref for async closures

        // Update latest session if this is a new one we just generated
        const latest = localStorage.getItem('ops_iq_latest_session');
        if (!latest || messages.length > 0) {
            // If we have messages, it's a real session
            localStorage.setItem('ops_iq_latest_session', sessionId);
        }
    }, [sessionId, messages]);

    const isReadOnly = messages.length > 0 && sessionId !== localStorage.getItem('ops_iq_latest_session');
    const isHistorical = sessionId !== localStorage.getItem('ops_iq_latest_session') && localStorage.getItem('ops_iq_latest_session') !== null;

    // Fetch history on session change
    useEffect(() => {
        let isActive = true;

        // CRITICAL: Clear messages immediately when session changes
        // This ensures we don't show stale data from previous session
        setMessages([]);
        thinkingStepsRef.current = [];
        setIsThinking(false);
        setPendingConfirmation(null);

        const fetchAndInit = async () => {
            try {
                const response = await fetch(`/api/v1/chat/${sessionId}/history`);
                if (!isActive) return;
                if (response.ok) {
                    const history = await response.json();

                    if (history.length > 0) {
                        // Map history to message format with proper UTC handling
                        const mappedHistory = history.map((m: any) => ({
                            ...m,
                            type: m.role === 'user' ? 'user' : (m.type || 'assistant'),
                            timestamp: parseTimestamp(m.timestamp)
                        }));

                        // Prepend synthetic welcome message with timestamp just before first message
                        const firstMsgTime = mappedHistory[0]?.timestamp || new Date();
                        const welcomeTime = new Date(firstMsgTime.getTime() - 1000); // 1 second before first msg
                        const syntheticWelcome = {
                            ...createWelcomeMessage(sessionId, user?.name, availableAgents),
                            timestamp: welcomeTime
                        };

                        setMessages([syntheticWelcome, ...mappedHistory]);
                    } else {
                        // Empty session, show welcome with dynamic agent pills
                        setMessages([createWelcomeMessage(sessionId, user?.name, availableAgents)]);
                    }
                } else {
                    // Server error - show welcome message anyway (works without DB)
                    console.warn('[Chat] History fetch returned error, starting fresh:', response.status);
                    setMessages([createWelcomeMessage(sessionId, user?.name, availableAgents)]);
                }
            } catch (err: any) {
                if (!isActive) return;
                // Connection failed - show welcome message anyway (works without backend history)
                console.warn('[Chat] History fetch failed, starting fresh:', err.message);
                setMessages([createWelcomeMessage(sessionId, user?.name, availableAgents)]);
            }
        };
        fetchAndInit();
        return () => { isActive = false; };
    }, [sessionId, user?.name, availableAgents]);

    const handleSendMessage = async (text: string, action?: string, values?: Record<string, any>) => {
        if (!text.trim() && !action) return;

        // Add user message to UI immediately
        const userMsg: Message = {
            id: generateId(),
            type: 'user',
            content: text,
            timestamp: new Date(),
        };

        // Create placeholder assistant message that will show live processing
        const thinkingMsgId = generateId();
        const initialSteps = [{
            id: 'init',
            label: '🔄 Preparing request',
            startTime: Date.now(),
            completed: false
        }];

        const thinkingMsg: Message = {
            id: thinkingMsgId,
            type: 'assistant',
            content: '',  // Content will be filled when response arrives
            timestamp: new Date(),
            isThinking: true,
            liveThinkingSteps: initialSteps,
            pillState: lastPillStateRef.current,  // Carry forward navigation state
        };

        setMessages(prev => [...prev, userMsg, thinkingMsg]);

        setIsThinking(true);
        thinkingStepsRef.current = initialSteps;
        abortControllerRef.current = new AbortController();

        try {
            const sentToId = sessionId;
            const response = await fetch('/api/v1/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sentToId,
                    user_id: user?.id || 'unknown',
                    user_email: user?.email,
                    content: text,
                    action: action,
                    values: values,
                    model_id: 'azure-openai',
                    auth_token: accessToken,
                    name: user?.name,
                    roles: user?.roles || []
                }),
                signal: abortControllerRef.current.signal
            });

            if (!response.body) throw new Error('No response body');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            // Helper function to process a single SSE event block
            const processEventBlock = (part: string) => {
                if (!part.trim()) return;
                console.log('[Chat][SSE] RAW event block:', part.substring(0, 100));
                const lines = part.split('\n');
                let event = 'message';
                let dataText = '';

                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        event = line.replace('event: ', '').trim();
                    } else if (line.startsWith('data: ')) {
                        dataText = line.replace('data: ', '').trim();
                    }
                }

                console.log('[Chat][SSE] Parsed event type:', event, '| Data:', dataText.substring(0, 50));

                if (dataText) {
                    try {
                        const data = JSON.parse(dataText);

                        // SESSION AFFINITY CHECK
                        if (sessionIdRef.current !== sentToId) {
                            console.warn('[Chat] Aborting SSE commit: session changed from', sentToId, 'to', sessionIdRef.current);
                            return; // Skip this event
                        }

                        if (event === 'thought' || event === 'status') {
                            console.log('[Chat][SSE] THOUGHT/STATUS received:', data.content);
                            const lastSteps = [...thinkingStepsRef.current];
                            console.log('[Chat][SSE] Current steps count:', lastSteps.length);
                            if (lastSteps.length > 0) {
                                const last = lastSteps[lastSteps.length - 1];
                                if (!last.completed) {
                                    last.completed = true;
                                    last.duration = (Date.now() - last.startTime) / 1000;
                                }
                            }
                            const nextSteps = [...lastSteps, {
                                id: Math.random().toString(36).substr(2, 9),
                                label: data.content,
                                startTime: Date.now(),
                                completed: false
                            }];
                            thinkingStepsRef.current = nextSteps;
                            syncLiveSteps(nextSteps);
                            console.log('[Chat][SSE] Updated steps count:', nextSteps.length, '| Labels:', nextSteps.map(s => s.label.substring(0, 20)));
                        } else if (event === 'reasoning') {
                            // Structured reasoning event from enhanced emit()
                            const stageIcons: Record<string, string> = {
                                intent_detection: '🎯',
                                security_check: '🔒',
                                tool_selection: '🔌',
                                tool_execution: '⚙️',
                                data_processing: '📊',
                                ui_generation: '🎨',
                                orchestration: '🤖',
                            };
                            const icon = stageIcons[data.stage] || '📋';
                            const label = `${icon} ${data.message}${data.tool ? ` (${data.tool})` : ''}`;

                            console.log('[Chat][SSE] REASONING received:', data.stage, data.message);
                            const lastSteps = [...thinkingStepsRef.current];
                            if (lastSteps.length > 0) {
                                const last = lastSteps[lastSteps.length - 1];
                                if (!last.completed) {
                                    last.completed = true;
                                    last.duration = (Date.now() - last.startTime) / 1000;
                                }
                            }
                            const nextSteps = [...lastSteps, {
                                id: Math.random().toString(36).substr(2, 9),
                                label,
                                startTime: Date.now(),
                                completed: data.status === 'complete'
                            }];
                            thinkingStepsRef.current = nextSteps;
                            syncLiveSteps(nextSteps);
                        } else if (event === 'message') {
                            console.log('[Chat][SSE] MESSAGE received, marking thinking complete');
                            markThinkingComplete();
                            handleAgentResponse(data, thinkingStepsRef.current);
                        } else if (event === 'error') {
                            markThinkingComplete();
                            handleError(data.content);
                        }
                    } catch (e) {
                        console.error('[Chat] SSE Parse error:', e, dataText);
                    }
                }
            };

            while (true) {
                const { value, done } = await reader.read();

                if (value) {
                    buffer += decoder.decode(value, { stream: true });
                }

                // Normalize Windows line endings before splitting
                const normalizedBuffer = buffer.replace(/\r\n/g, '\n');

                // Process all complete events in the buffer (SSE events are separated by double newline)
                const parts = normalizedBuffer.split('\n\n');
                buffer = parts.pop() || ''; // Keep the incomplete part for next iteration

                for (const part of parts) {
                    processEventBlock(part);
                }

                // If stream is done, process any remaining buffer content
                if (done) {
                    if (buffer.trim()) {
                        processEventBlock(buffer);
                    }
                    break;
                }
            }
        } catch (err: any) {
            if (err.name === 'AbortError') {
                setMessages(prev => [...prev, {
                    id: generateId(),
                    type: 'system',
                    content: 'Operation cancelled.',
                    timestamp: new Date()
                }]);
            } else {
                handleError(err.message);
            }
        } finally {
            setIsThinking(false);
            abortControllerRef.current = null;
        }
    };

    const markThinkingComplete = () => {
        const lastSteps = [...thinkingStepsRef.current];
        if (lastSteps.length === 0) return;
        const last = lastSteps[lastSteps.length - 1];
        last.completed = true;
        last.duration = (Date.now() - last.startTime) / 1000;
        thinkingStepsRef.current = lastSteps;
    };

    // Sync live thinking steps to the placeholder message
    const syncLiveSteps = (steps: { id: string, label: string, startTime: number, duration?: number, completed: boolean }[]) => {
        setMessages(prev => {
            const lastIdx = prev.length - 1;
            const lastMsg = prev[lastIdx];
            if (lastMsg && lastMsg.isThinking) {
                const updated = [...prev];
                updated[lastIdx] = { ...lastMsg, liveThinkingSteps: [...steps] };
                return updated;
            }
            return prev;
        });
    };

    const handleAgentResponse = (msg: any, steps: any[]) => {
        if (msg.type === 'confirmation_request') {
            setPendingConfirmation(msg.confirmation_data);
        }
        setMessages(prev => {
            // Find the thinking placeholder and update it with the response
            const lastIdx = prev.length - 1;
            const lastMsg = prev[lastIdx];

            if (lastMsg && lastMsg.isThinking) {
                // Update the placeholder message with actual content
                const updatedMessages = [...prev];
                updatedMessages[lastIdx] = {
                    ...lastMsg,
                    type: msg.role === 'assistant' ? 'assistant' : (msg.type as any || 'assistant'),
                    content: msg.content,
                    manifest: msg.manifest,
                    isThinking: false,  // No longer thinking
                    thinkingSteps: [...steps],  // Finalized steps
                    liveThinkingSteps: undefined,  // Clear live steps
                };
                return updatedMessages;
            }

            // Fallback: create new message if no placeholder found
            return [...prev, {
                id: generateId(),
                type: msg.role === 'assistant' ? 'assistant' : (msg.type as any || 'assistant'),
                content: msg.content,
                manifest: msg.manifest,
                timestamp: new Date(),
                thinkingSteps: [...steps]
            }];
        });

        // Clear active thinking steps
        thinkingStepsRef.current = [];
    };
    const handleError = (error: string) => {
        setMessages(prev => [...prev, {
            id: generateId(),
            type: 'system',
            content: `Error: ${error}`,
            timestamp: new Date(),
        }]);
    };

    const handleCancel = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
    };

    const handleNewChat = () => {
        const newId = generateId();
        setSessionId(newId);
        setMessages([]);
        localStorage.setItem('ops_iq_latest_session', newId);
    };

    // Listen for auth success from popups
    useEffect(() => {
        const handleMessage = (event: MessageEvent) => {
            // Security: Verify origin to prevent cross-origin attacks
            const allowedOrigins = [window.location.origin, 'http://localhost:8000', 'http://localhost:5173'];
            if (!allowedOrigins.includes(event.origin)) {
                console.warn('[Chat] Ignoring message from untrusted origin:', event.origin);
                return;
            }
            if (event.data?.type === 'snow_auth_success') {
                console.log('[Chat] ServiceNow authentication success signal received.');
                // Trigger area re-discovery to show enriched pills
                handleSendMessage('ServiceNow connection verified', 'select_area', { value: 'servicenow' });
            }
        };
        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [sessionId]);

    // Note: dispatchChatAction is registered in the useEffect at line ~529 below

    const handleConfirm = async (values: Record<string, string>) => {
        setPendingConfirmation(null);
        // In REST mode, we send the confirmation as a new user message or special payload
        // For now, we'll treat it as a message to the chat endpoint
        handleSendMessage(`Confirmed with values: ${JSON.stringify(values)}`);
    };

    const handleCancelConfirmation = () => {
        setPendingConfirmation(null);
        handleSendMessage("Cancel action");
    };

    // Global action dispatcher for pills/manifests
    useEffect(() => {
        (window as any).dispatchChatAction = (action: any) => {
            if (isThinking) return;
            if (action.messageId && consumedActions.has(action.messageId)) return;

            if (action.messageId) {
                setConsumedActions(prev => new Set(prev).add(action.messageId));
            }

            if (action.type === 'pill_click') {
                // Update last pill state for continuity
                if (action.areaId) {
                    lastPillStateRef.current = { mode: 'actions', areaId: action.areaId };
                }

                if (action.action === 'open_url') {
                    const width = 600;
                    const height = 700;
                    const left = window.screenX + (window.outerWidth - width) / 2;
                    const top = window.screenY + (window.outerHeight - height) / 2;
                    window.open(action.value, 'ServiceNowAuth', `width=${width},height=${height},left=${left},top=${top}`);
                    return;
                }
                handleSendMessage(action.label || action.value, action.action, { value: action.value, areaId: action.areaId });
            } else if (action.type === 'form_submit') {
                if (action.action === 'open_url') {
                    const width = 600;
                    const height = 700;
                    const left = window.screenX + (window.outerWidth - width) / 2;
                    const top = window.screenY + (window.outerHeight - height) / 2;
                    window.open(action.value, 'ServiceNowAuth', `width=${width},height=${height},left=${left},top=${top}`);
                    return;
                }
                handleSendMessage(`Submitted ${action.action}`, action.action, action.values);
            }
        };
        return () => { delete (window as any).dispatchChatAction; };
    }, [sessionId, isThinking, consumedActions]);

    return (
        <div className="chat-layout">
            <SessionSidebar
                userId={user?.id || 'unknown'}
                currentSessionId={sessionId}
                isCollapsed={isSidebarCollapsed}
                onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                onSelectSession={setSessionId}
                onNewChat={handleNewChat}
            />

            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
            />

            <div className="chat-container">
                <header className="chat-header">
                    <div className="flex items-center gap-3">
                        <div className="login-logo-icon"><SparklesIcon size={20} /></div>
                        <div>
                            <h1 className="text-xl font-bold leading-none">{APP_CONFIG.appName}</h1>
                            <span className="text-muted text-xs uppercase tracking-[0.2em] font-medium">{APP_CONFIG.appDescription}</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-4">
                            <div className="flex gap-2">
                                {hasRole('APP_ROLE_ADMIN') && <Badge variant="info">Admin</Badge>}
                                {hasRole('APP_ROLE_PARTNER') && <Badge variant="warning">Partner</Badge>}
                            </div>
                            <Avatar name={user?.name || ''} size="sm" />
                            <div className="flex gap-1">
                                <Button
                                    variant="ghost"
                                    className="btn-icon"
                                    onClick={() => setIsSettingsOpen(true)}
                                >
                                    <SettingsIcon size={20} />
                                </Button>
                                <Button variant="ghost" className="btn-icon" onClick={signOut}><LogoutIcon size={20} /></Button>
                            </div>
                        </div>
                    </div>
                </header>

                <main className="chat-messages" ref={scrollContainerRef}>
                    {messages.map(message => (
                        <ChatMessage
                            key={message.id}
                            message={message}
                            user={user}
                            readOnly={isReadOnly || consumedActions.has(message.id) || isThinking}
                        />
                    ))}

                    {/* Floating thinking indicator removed - now rendered inside placeholder message bubble */}

                    {pendingConfirmation && (
                        <div className={`p-4 max-w-2xl ${isHistorical ? 'opacity-50 pointer-events-none' : ''}`}>
                            <ConfirmationCard
                                data={pendingConfirmation}
                                onConfirm={handleConfirm}
                                onCancel={handleCancelConfirmation}
                            />
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </main>

                <footer className="chat-input-area">
                    {isHistorical ? (
                        <div className="p-4 text-center text-muted opacity-50 italic">
                            This is a historical session and is currently read-only.
                        </div>
                    ) : (
                        <ChatInput
                            onSend={handleSendMessage}
                            onCancel={handleCancel}
                            isLoading={isThinking}
                            placeholder="Type your automation request..."
                        />
                    )}
                </footer>
            </div>
        </div>
    );
};

export default Chat;
