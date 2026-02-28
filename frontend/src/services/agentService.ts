/**
 * Agent Service - Fetch available agents based on user roles
 */

import { API_BASE_URL } from '../config';

export interface AgentInfo {
    id: string;
    name: string;
    icon: string;
    description: string;
    systems: string[];
    reason?: string;  // For locked agents
}

export interface AgentCatalog {
    available: AgentInfo[];
    locked: AgentInfo[];
    error?: string;
}

/**
 * Fetch available agents from backend based on user roles
 */
export async function fetchAgentCatalog(roles: string[]): Promise<AgentCatalog> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/agents`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ roles }),
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch agents: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('[AgentService] Error fetching agents:', error);
        return {
            available: [],
            locked: [],
            error: error instanceof Error ? error.message : 'Unknown error',
        };
    }
}

/**
 * Get pills for a specific agent
 */
export function getAgentPills(agentId: string): { label: string; action: string; value: string }[] {
    const pillsByAgent: Record<string, { label: string; action: string; value: string }[]> = {
        sales: [
            { label: "Find Client", action: "ask", value: "Search for a client by name" },
            { label: "New Opportunity", action: "ask", value: "Create a new sales opportunity" },
            { label: "Client Ingestion", action: "ask", value: "Import new client data" },
        ],
        onboarding: [
            { label: "New Client Setup", action: "ask", value: "I need to onboard a new client" },
            { label: "Find Client", action: "ask", value: "Search for an existing client" },
            { label: "Time Setup", action: "ask", value: "Set up time tracking for a client" },
        ],
        it_support: [
            { label: "Report Issue", action: "ask", value: "I need to report an IT issue" },
            { label: "My Tickets", action: "ask", value: "Show my open IT tickets" },
            { label: "My Approvals", action: "ask", value: "Show my pending approvals" },
        ],
        hr: [
            { label: "My Time Entries", action: "ask", value: "Show my recent time entries" },
            { label: "Log Time", action: "ask", value: "I need to log my time" },
            { label: "HR Policy", action: "ask", value: "Find HR policy information" },
        ],
    };

    return pillsByAgent[agentId] || [];
}
