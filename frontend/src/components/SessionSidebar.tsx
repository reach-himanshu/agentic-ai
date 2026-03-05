import React, { useEffect, useState } from 'react';
import { History, Plus, MessageSquare, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';
import { Button } from './ui/Button';

interface Session {
    id: string;
    title: string;
    model_id: string;
    updated_at: string;
}

interface SessionSidebarProps {
    userId: string;
    currentSessionId: string;
    isCollapsed: boolean;
    onToggle: () => void;
    onSelectSession: (sessionId: string) => void;
    onNewChat: () => void;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
    userId,
    currentSessionId,
    isCollapsed,
    onToggle,
    onSelectSession,
    onNewChat
}) => {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchSessions = async () => {
        try {
            setLoading(true);
            const response = await fetch(`/api/v1/sessions?user_id=${userId}`);
            if (response.ok) {
                const data = await response.json();
                setSessions(data);
            }
        } catch (error) {
            console.error('[SessionSidebar] Failed to fetch sessions:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation(); // Prevent selecting the session

        if (!window.confirm('Are you sure you want to delete this chat?')) return;

        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}?user_id=${userId}`, {
                method: 'DELETE',
            });
            if (response.ok) {
                // Remove from local state
                setSessions(prev => prev.filter(s => s.id !== sessionId));
                // If the deleted session was the current one, start a new chat
                if (sessionId === currentSessionId) {
                    onNewChat();
                }
            } else {
                console.error('[SessionSidebar] Failed to delete session');
            }
        } catch (error) {
            console.error('[SessionSidebar] Delete error:', error);
        }
    };

    useEffect(() => {
        if (userId) {
            fetchSessions();
        }
    }, [userId]);

    return (
        <div className={`chat-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-header">
                {!isCollapsed && (
                    <Button
                        variant="primary"
                        fullWidth
                        onClick={onNewChat}
                        className="flex items-center gap-2"
                    >
                        <Plus size={18} />
                        <span>New Chat</span>
                    </Button>
                )}
                {isCollapsed && (
                    <Button variant="primary" className="btn-icon" onClick={onNewChat}>
                        <Plus size={18} />
                    </Button>
                )}

                <button
                    className="sidebar-toggle"
                    onClick={onToggle}
                    title={isCollapsed ? "Show chat history" : "Hide chat history"}
                >
                    <History size={16} />
                    {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                </button>
            </div>

            <div className="sidebar-content">
                <div className="sidebar-section-title">
                    <History size={14} className={isCollapsed ? '' : 'mr-2'} />
                    {!isCollapsed && <span>Recent Chats</span>}
                </div>

                {loading && !isCollapsed && <div className="p-4 text-xs opacity-50">Loading history...</div>}

                <div className="session-list">
                    {sessions.map(session => (
                        <div
                            key={session.id}
                            className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                            onClick={() => onSelectSession(session.id)}
                            title={isCollapsed ? session.id : undefined}
                        >
                            <MessageSquare size={16} className="flex-shrink-0" />
                            {!isCollapsed && (
                                <div className="session-info">
                                    <div className="session-name">
                                        {session.title || session.id.substring(0, 18)}
                                    </div>
                                    <div className="session-date">
                                        {new Date(session.updated_at).toLocaleString([], {
                                            month: 'short',
                                            day: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </div>
                                </div>
                            )}
                            {!isCollapsed && (
                                <button
                                    className="session-delete-btn"
                                    onClick={(e) => handleDeleteSession(e, session.id)}
                                    title="Delete chat"
                                >
                                    <Trash2 size={14} />
                                </button>
                            )}
                        </div>
                    ))}
                    {!loading && sessions.length === 0 && !isCollapsed && (
                        <div className="p-4 text-xs opacity-50 text-center">No recent chats</div>
                    )}
                </div>
            </div>
        </div>
    );
};
