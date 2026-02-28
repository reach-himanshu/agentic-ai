/**
 * WebSocket client for communicating with the Agent Orchestrator.
 */

type MessageHandler = (message: AgentMessage) => void;

export interface AgentMessage {
    type: 'auth_success' | 'assistant_message' | 'system_message' | 'confirmation_request' | 'error';
    content: string;
    confirmation_data?: ConfirmationData;
    data?: Record<string, unknown>;
    manifest?: any;
    model_info?: string;
}

export interface ConfirmationData {
    title: string;
    description: string;
    fields: Array<{
        key: string;
        label: string;
        value: string;
        newValue?: string;
        editable?: boolean;
        type?: 'text' | 'select';
        options?: string[];
    }>;
    confirmLabel: string;
    cancelLabel: string;
}

class AgentSocket {
    private ws: WebSocket | null = null;
    private url: string;
    private selectedModelId: string | undefined = undefined;
    private messageHandler: MessageHandler | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private connectionPromise: Promise<void> | null = null;
    private authFlow: 'OBO' | 'CLIENT_CREDENTIALS' | 'DEV' = 'CLIENT_CREDENTIALS';
    private userName: string | null = null;
    private userRoles: string[] = [];

    constructor(url: string = 'ws://127.0.0.1:8000/ws') {
        this.url = url;
    }

    /**
     * Connect to the WebSocket server.
     */
    connect(): Promise<void> {
        if (this.connectionPromise) return this.connectionPromise;
        if (this.isConnected()) return Promise.resolve();

        this.connectionPromise = new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    console.log('[AgentSocket] Connected');
                    this.reconnectAttempts = 0;
                    this.connectionPromise = null;
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message: AgentMessage = JSON.parse(event.data);
                        // Security: Sanitize log output to prevent log injection
                        const safeType = String(message.type ?? 'unknown').replace(/[\n\r\t]/g, '');
                        console.log('[AgentSocket] Received:', safeType);

                        if (this.messageHandler) {
                            this.messageHandler(message);
                        }
                    } catch (e) {
                        console.error('[AgentSocket] Parse error');
                    }
                };

                this.ws.onclose = () => {
                    console.log('[AgentSocket] Disconnected');
                    this.connectionPromise = null;
                    this.attemptReconnect();
                };

                this.ws.onerror = (error) => {
                    console.error('[AgentSocket] Error:', error);
                    this.connectionPromise = null;
                    reject(error);
                };
            } catch (error) {
                reject(error);
            }
        });
        return this.connectionPromise;
    }

    /**
     * Attempt to reconnect with exponential backoff.
     */
    private attemptReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('[AgentSocket] Max reconnect attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`[AgentSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connect().catch(() => { });
        }, delay);
    }

    /**
     * Set auth info for Reconnect
     */
    setAuthInfo(_token: string, modelId?: string, authFlow?: 'OBO' | 'CLIENT_CREDENTIALS' | 'DEV', name?: string, roles?: string[]): void {
        this.selectedModelId = modelId;
        if (authFlow) this.authFlow = authFlow;
        if (name) this.userName = name;
        if (roles) this.userRoles = roles;
    }

    /**
     * Send authentication token and model choice.
     */
    authenticate(token: string, modelId?: string, authFlow?: 'OBO' | 'CLIENT_CREDENTIALS' | 'DEV', name?: string, roles?: string[]): void {
        this.selectedModelId = modelId || this.selectedModelId;
        if (authFlow) this.authFlow = authFlow;
        if (name) this.userName = name;
        if (roles) this.userRoles = roles;

        this.send({
            type: 'auth',
            token,
            model_id: this.selectedModelId,
            auth_flow: this.authFlow,
            name: this.userName,
            roles: this.userRoles
        });
    }

    /**
     * Send a user message.
     */
    sendMessage(content: string): void {
        this.send({ type: 'user_message', content });
    }

    /**
     * Send confirmation response.
     */
    sendConfirmation(confirmed: boolean, values?: Record<string, string>): void {
        this.send({ type: 'confirmation_response', confirmed, values });
    }

    /**
     * Send form response.
     */
    sendFormResponse(action: string, values: Record<string, any>): void {
        this.send({ type: 'form_response', action, values });
    }

    /**
     * Send raw message.
     */
    private send(data: Record<string, unknown>): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('[AgentSocket] Not connected');
        }
    }

    /**
     * Set message handler.
     */
    onMessage(handler: MessageHandler): void {
        this.messageHandler = handler;
    }

    /**
     * Check if connected.
     */
    isConnected(): boolean {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Disconnect from server.
     */
    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Singleton instance
export const agentSocket = new AgentSocket();
export default agentSocket;
