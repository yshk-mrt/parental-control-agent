import React, { useEffect } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { ParentDashboardProvider, useParentDashboard } from './contexts/ParentDashboardContext';
import { SystemStatusMonitor } from './components/parent/SystemStatusMonitor';
import { Layout, Container, PageHeader } from './components/common/Layout';
import { Card, CardHeader, CardContent } from './components/common/Card';
import Button from './components/common/Button';
import ThemeToggle from './components/common/ThemeToggle';

const AppContent: React.FC = () => {
  const { state, connect, disconnect } = useParentDashboard();

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

  return (
    <Layout>
      <Container maxWidth="2xl" className="py-8">
        <div className="flex justify-between items-center mb-8">
          <PageHeader 
            title="Safe Browser AI - Parent Dashboard" 
            description="Manage your child's safe internet experience"
          />
          <ThemeToggle />
        </div>

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
                    <div key={request.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold">{request.reason}</h3>
                          <p className="text-sm text-muted-foreground">
                            {request.applicationName || 'Unknown App'} - {new Date(request.timestamp).toLocaleString('en-US')}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="primary"
                            onClick={() => {
                              // TODO: Implement approval logic
                              console.log('Approved:', request.id);
                            }}
                          >
                            Approve
                          </Button>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => {
                              // TODO: Implement denial logic
                              console.log('Denied:', request.id);
                            }}
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
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Learning Dashboard */}
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Learning Dashboard</h2>
              <p className="text-muted-foreground">
                Track your child's learning progress and interests
              </p>
            </CardHeader>
            <CardContent>
              <Button variant="outline">Show Dashboard</Button>
            </CardContent>
          </Card>

          {/* Design System Demo */}
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Design System</h2>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="destructive">Destructive</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
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
