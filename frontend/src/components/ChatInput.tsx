import React, { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { Button, SendIcon, StopIcon } from './ui';

interface ChatInputProps {
    onSend: (message: string) => void;
    onCancel?: () => void;
    isLoading?: boolean;
    placeholder?: string;
    disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
    onSend,
    onCancel,
    isLoading = false,
    placeholder = "Type a message...",
    disabled = false,
}) => {
    const [message, setMessage] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSend = () => {
        const trimmed = message.trim();
        if (trimmed && !isLoading && !disabled) {
            onSend(trimmed);
            setMessage('');
            // Reset textarea height
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
        }
    }, [message]);

    return (
        <div
            className="flex items-end gap-3"
            style={{
                background: 'var(--color-bg-tertiary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--border-radius-lg)',
                padding: 'var(--spacing-3)',
                transition: 'border-color var(--transition-fast)',
            }}
        >
            <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                disabled={disabled || isLoading}
                rows={1}
                style={{
                    flex: 1,
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    resize: 'none',
                    fontFamily: 'var(--font-family-sans)',
                    fontSize: 'var(--font-size-base)',
                    color: 'var(--color-text-primary)',
                    lineHeight: 'var(--line-height-normal)',
                    minHeight: '24px',
                    maxHeight: '150px',
                }}
            />
            <Button
                variant={isLoading ? "danger" : "primary"}
                className="btn-icon"
                onClick={isLoading ? onCancel : handleSend}
                disabled={(!message.trim() && !isLoading) || disabled}
                style={{ flexShrink: 0 }}
            >
                {isLoading ? <StopIcon size={18} /> : <SendIcon size={18} />}
            </Button>
        </div>
    );
};

export default ChatInput;
