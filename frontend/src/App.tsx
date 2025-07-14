import React, { useEffect, useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { ParentDashboardProvider, useParentDashboard } from './contexts/ParentDashboardContext';
import { SystemStatusMonitor } from './components/parent/SystemStatusMonitor';
import LearningDashboard from './components/dashboard/LearningDashboard';
import ApprovalModal from './components/parent/ApprovalModal';
import { Layout, Container, PageHeader } from './components/common/Layout';
import { Card, CardHeader, CardContent } from './components/common/Card';
import Button from './components/common/Button';
import ThemeToggle from './components/common/ThemeToggle';
import Icon from './components/common/Icon';
import { Monitor, BookOpen, Settings } from 'lucide-react';

const AppContent: React.FC = () => {
  const { state, connect, disconnect, sendApprovalResponse } = useParentDashboard();
  const [currentView, setCurrentView] = useState<'dashboard' | 'learning' | 'settings'>('learning');
  const [selectedRequest, setSelectedRequest] = useState<any>(null);

  useEffect(() => {
    // Auto-connect to WebSocket when component mounts
    connect();
    
    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const handleConnect = () => {
    connect();
  };

  const handleDisconnect = () => {
    disconnect();
  };

  const handleApprovalResponse = (requestId: string, approved: boolean) => {
    console.log(`${approved ? 'Approving' : 'Denying'} request:`, requestId);
    sendApprovalResponse(requestId, approved);
  };

  const handleRequestClick = (request: any) => {
    // Add mock data for demonstration
    const enhancedRequest = {
      ...request,
      screenshot: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2Y3ZjlmMyIvPgogIDx0ZXh0IHg9IjIwMCIgeT0iMTUwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM2NjY2NjYiIHRleHQtYW5jaG9yPSJtaWRkbGUiPlNjcmVlbnNob3QgUHJldmlldyBVbmF2YWlsYWJsZTwvdGV4dD4KPC9zdmc+',
      context: 'Child was attempting to access educational content about dinosaurs, but the AI detected some potentially inappropriate language in the search query.',
      riskLevel: 'medium' as const
    };
    setSelectedRequest(enhancedRequest);
  };

  const navigationItems = [
    { id: 'dashboard', label: 'System Status', icon: Monitor },
    { id: 'learning', label: 'Learning Dashboard', icon: BookOpen },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <Layout>
      <Container maxWidth="2xl" className="py-8">
        <div className="flex justify-between items-center mb-8 bg-white p-4 rounded-lg shadow-sm border">
          <PageHeader 
            title="Safe Browser AI - Parent Dashboard" 
            description="Manage your child's safe internet experience"
          />
          <ThemeToggle />
        </div>

        {/* Navigation */}
        <div className="flex space-x-1 mb-8 bg-gray-100 p-1 rounded-lg">
          {navigationItems.map((item) => (
            <Button
              key={item.id}
              variant={currentView === item.id ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setCurrentView(item.id as any)}
              className="flex items-center gap-2"
            >
              <Icon icon={item.icon} className="w-4 h-4" />
              {item.label}
            </Button>
          ))}
        </div>

        {/* Content based on current view */}
        {currentView === 'dashboard' && (
          <>
            {/* System Status Monitor */}
            <SystemStatusMonitor />

            <div className="space-y-6">
          {/* Connection Control */}
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Connection Management</h2>
              <p className="text-muted-foreground">
                Manage connection to backend server
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Button 
                    onClick={handleConnect} 
                    variant="primary"
                    disabled={state.isConnected}
                  >
                    Connect
                  </Button>
                  <Button 
                    onClick={handleDisconnect} 
                    variant="outline"
                    disabled={!state.isConnected}
                  >
                    Disconnect
                  </Button>
                </div>
                
                <div className="bg-muted/30 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Connection Status:</h3>
                  <ul className="text-sm space-y-1">
                    <li>
                      WebSocket: 
                      <span className={`ml-2 font-semibold ${state.isConnected ? 'text-success' : 'text-destructive'}`}>
                        {state.connectionState}
                      </span>
                    </li>
                    <li>
                      System Status: 
                      <span className="ml-2 font-semibold">
                        {state.systemStatus.status}
                      </span>
                    </li>
                    <li>
                      Pending Approvals: 
                      <span className="ml-2 font-semibold">
                        {state.approvalRequests.length} items
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Approval Requests */}
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Approval Requests</h2>
              <p className="text-muted-foreground">
                Manage approval requests from your child
              </p>
            </CardHeader>
            <CardContent>
              {state.approvalRequests.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No pending approval requests at the moment
                </div>
              ) : (
                <div className="space-y-4">
                  {state.approvalRequests.map((request) => (
                    <div key={request.id} className="border rounded-lg p-4 hover:bg-muted/30 transition-colors cursor-pointer">
                      <div className="flex justify-between items-start mb-2">
                        <div onClick={() => handleRequestClick(request)} className="flex-1">
                          <h3 className="font-semibold">{request.reason}</h3>
                          <p className="text-sm text-muted-foreground">
                            {request.applicationName || 'Unknown App'} - {new Date(request.timestamp).toLocaleString('en-US')}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="primary"
                            onClick={() => handleApprovalResponse(request.id, true)}
                          >
                            Approve
                          </Button>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleApprovalResponse(request.id, false)}
                          >
                            Deny
                          </Button>
                        </div>
                      </div>
                      {request.blockedUrl && (
                        <div className="text-xs text-muted-foreground">
                          URL: {request.blockedUrl}
                        </div>
                      )}
                      {request.keywords && request.keywords.length > 0 && (
                        <div className="text-xs text-muted-foreground">
                          Keywords: {request.keywords.join(', ')}
                        </div>
                      )}
                      <div className="text-xs text-muted-foreground">
                        AI Confidence: {Math.round(request.confidence * 100)}%
                      </div>
                      <div className="text-xs text-muted-foreground mt-2">
                        Click for detailed view
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
            </div>
          </>
        )}

        {currentView === 'learning' && <LearningDashboard />}

        {currentView === 'settings' && (
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Settings</h2>
              <p className="text-muted-foreground">
                Configure monitoring rules and preferences
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                Settings panel coming soon...
              </div>
            </CardContent>
          </Card>
        )}

        {/* Enhanced Approval Modal */}
        {selectedRequest && (
          <ApprovalModal
            request={selectedRequest}
            isOpen={!!selectedRequest}
            onClose={() => setSelectedRequest(null)}
            onApprove={(requestId) => handleApprovalResponse(requestId, true)}
            onDeny={(requestId) => handleApprovalResponse(requestId, false)}
          />
        )}
      </Container>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <ParentDashboardProvider>
        <AppContent />
      </ParentDashboardProvider>
    </ThemeProvider>
  );
};

export default App;
