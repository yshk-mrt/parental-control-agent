import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { websocketService, type ApprovalRequest, type ActivityUpdate, type SystemStatus } from '../services/websocket';

interface ParentDashboardState {
  systemStatus: SystemStatus;
  approvalRequests: ApprovalRequest[];
  currentActivity: ActivityUpdate | null;
  connectionState: string;
  isConnected: boolean;
}

interface ParentDashboardContextType {
  state: ParentDashboardState;
  sendApprovalResponse: (requestId: string, approved: boolean) => void;
  requestSystemStatus: () => void;
  updateSettings: (settings: any) => void;
  clearApprovalRequest: (requestId: string) => void;
  connect: () => Promise<void>;
  disconnect: () => void;
}

const ParentDashboardContext = createContext<ParentDashboardContextType | undefined>(undefined);

interface ParentDashboardProviderProps {
  children: ReactNode;
}

export const ParentDashboardProvider: React.FC<ParentDashboardProviderProps> = ({ children }) => {
  const [state, setState] = useState<ParentDashboardState>({
    systemStatus: {
      status: 'offline',
      lastUpdate: new Date().toISOString(),
      connectionHealth: 'disconnected'
    },
    approvalRequests: [],
    currentActivity: null,
    connectionState: 'disconnected',
    isConnected: false
  });

  // WebSocket event handlers
  useEffect(() => {
    const handleConnected = () => {
      console.log('📡 Dashboard connected to WebSocket');
      setState(prev => ({
        ...prev,
        connectionState: 'connected',
        isConnected: true,
        systemStatus: {
          ...prev.systemStatus,
          connectionHealth: 'good'
        }
      }));
      
      // Request current system status when connected
      websocketService.requestSystemStatus();
    };

    const handleDisconnected = () => {
      console.log('📡 Dashboard disconnected from WebSocket');
      setState(prev => ({
        ...prev,
        connectionState: 'disconnected',
        isConnected: false,
        systemStatus: {
          ...prev.systemStatus,
          status: 'offline',
          connectionHealth: 'disconnected'
        }
      }));
    };

    const handleSystemLocked = (data: any) => {
      console.log('🔒 System locked:', data);
      setState(prev => ({
        ...prev,
        systemStatus: {
          status: 'locked',
          lastUpdate: new Date().toISOString(),
          connectionHealth: prev.systemStatus.connectionHealth
        }
      }));
    };

    const handleSystemUnlocked = (data: any) => {
      console.log('🔓 System unlocked:', data);
      setState(prev => ({
        ...prev,
        systemStatus: {
          status: 'monitoring',
          lastUpdate: new Date().toISOString(),
          connectionHealth: prev.systemStatus.connectionHealth
        }
      }));
    };

    const handleApprovalRequest = (request: ApprovalRequest) => {
      console.log('📋 New approval request:', request);
      setState(prev => ({
        ...prev,
        approvalRequests: [...prev.approvalRequests, request]
      }));
    };

    const handleActivityUpdate = (activity: ActivityUpdate) => {
      console.log('📊 Activity update:', activity);
      setState(prev => ({
        ...prev,
        currentActivity: activity
      }));
    };

    const handleConnectionStatus = (status: SystemStatus) => {
      console.log('📡 Connection status update:', status);
      setState(prev => ({
        ...prev,
        systemStatus: status
      }));
    };

    const handleError = (error: any) => {
      console.error('❌ WebSocket error:', error);
      setState(prev => ({
        ...prev,
        connectionState: 'error',
        isConnected: false,
        systemStatus: {
          ...prev.systemStatus,
          connectionHealth: 'disconnected'
        }
      }));
    };

    // Register event handlers
    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);
    websocketService.on('systemLocked', handleSystemLocked);
    websocketService.on('systemUnlocked', handleSystemUnlocked);
    websocketService.on('approvalRequest', handleApprovalRequest);
    websocketService.on('activityUpdate', handleActivityUpdate);
    websocketService.on('connectionStatus', handleConnectionStatus);
    websocketService.on('error', handleError);

    // Cleanup event handlers
    return () => {
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      websocketService.off('systemLocked', handleSystemLocked);
      websocketService.off('systemUnlocked', handleSystemUnlocked);
      websocketService.off('approvalRequest', handleApprovalRequest);
      websocketService.off('activityUpdate', handleActivityUpdate);
      websocketService.off('connectionStatus', handleConnectionStatus);
      websocketService.off('error', handleError);
    };
  }, []);

  // Update connection state from WebSocket service
  useEffect(() => {
    const updateConnectionState = () => {
      setState(prev => ({
        ...prev,
        connectionState: websocketService.connectionState,
        isConnected: websocketService.isConnected
      }));
    };

    const interval = setInterval(updateConnectionState, 1000);
    return () => clearInterval(interval);
  }, []);

  // Context methods
  const sendApprovalResponse = useCallback((requestId: string, approved: boolean) => {
    const parentId = 'parent-001'; // TODO: Get from auth context
    websocketService.sendApprovalResponse(requestId, approved, parentId);
    
    // Remove the request from the queue
    setState(prev => ({
      ...prev,
      approvalRequests: prev.approvalRequests.filter(req => req.id !== requestId)
    }));
  }, []);

  const requestSystemStatus = useCallback(() => {
    websocketService.requestSystemStatus();
  }, []);

  const updateSettings = useCallback((settings: any) => {
    websocketService.updateSettings(settings);
  }, []);

  const clearApprovalRequest = useCallback((requestId: string) => {
    setState(prev => ({
      ...prev,
      approvalRequests: prev.approvalRequests.filter(req => req.id !== requestId)
    }));
  }, []);

  const connect = useCallback(async () => {
    try {
      await websocketService.connect();
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
    }
  }, []);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  const contextValue: ParentDashboardContextType = {
    state,
    sendApprovalResponse,
    requestSystemStatus,
    updateSettings,
    clearApprovalRequest,
    connect,
    disconnect
  };

  return (
    <ParentDashboardContext.Provider value={contextValue}>
      {children}
    </ParentDashboardContext.Provider>
  );
};

export const useParentDashboard = (): ParentDashboardContextType => {
  const context = useContext(ParentDashboardContext);
  if (context === undefined) {
    throw new Error('useParentDashboard must be used within a ParentDashboardProvider');
  }
  return context;
}; 