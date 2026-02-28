/**
 * useAgents Hook - Manage agent state based on user roles
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchAgentCatalog, getAgentPills } from '../services/agentService';
import type { AgentInfo, AgentCatalog } from '../services/agentService';

interface UseAgentsResult {
    availableAgents: AgentInfo[];
    lockedAgents: AgentInfo[];
    selectedAgent: AgentInfo | null;
    isLoading: boolean;
    error: string | null;
    selectAgent: (agentId: string) => void;
    getAgentPills: (agentId: string) => { label: string; action: string; value: string }[];
    hasAppAccess: boolean;
}

export function useAgents(): UseAgentsResult {
    const { user } = useAuth();
    const [catalog, setCatalog] = useState<AgentCatalog>({ available: [], locked: [] });
    const [selectedAgent, setSelectedAgent] = useState<AgentInfo | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Fetch agents when user roles change
    useEffect(() => {
        async function loadAgents() {
            if (!user) {
                setIsLoading(false);
                return;
            }

            setIsLoading(true);
            setError(null);

            try {
                const result = await fetchAgentCatalog(user.roles);
                setCatalog(result);

                if (result.error) {
                    setError(result.error);
                }

                // Auto-select first available agent
                if (result.available.length > 0 && !selectedAgent) {
                    setSelectedAgent(result.available[0]);
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load agents');
            } finally {
                setIsLoading(false);
            }
        }

        loadAgents();
    }, [user?.roles]);

    const selectAgent = useCallback((agentId: string) => {
        const agent = catalog.available.find(a => a.id === agentId);
        if (agent) {
            setSelectedAgent(agent);
        }
    }, [catalog.available]);

    const hasAppAccess = user?.roles.includes('OpsIQ.User') ?? false;

    return {
        availableAgents: catalog.available,
        lockedAgents: catalog.locked,
        selectedAgent,
        isLoading,
        error,
        selectAgent,
        getAgentPills,
        hasAppAccess,
    };
}
