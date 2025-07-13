import React from 'react';
import { Card, CardHeader, CardContent } from '../common/Card';
import Icon from '../common/Icon';
import { 
  Shield, 
  ShieldAlert, 
  ShieldOff, 
  Wifi, 
  WifiOff, 
  Monitor, 
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useParentDashboard } from '../../contexts/ParentDashboardContext';

export const SystemStatusMonitor: React.FC = () => {
  const { state } = useParentDashboard();
  const { systemStatus, connectionState, isConnected, currentActivity } = state;

  const getStatusIcon = () => {
    switch (systemStatus.status) {
      case 'monitoring':
        return <Icon icon={Shield} className="w-6 h-6 text-primary" />;
      case 'locked':
        return <Icon icon={ShieldAlert} className="w-6 h-6 text-destructive" />;
      case 'offline':
        return <Icon icon={ShieldOff} className="w-6 h-6 text-muted-foreground" />;
      default:
        return <Icon icon={AlertCircle} className="w-6 h-6 text-accent" />;
    }
  };

  const getStatusText = () => {
    switch (systemStatus.status) {
      case 'monitoring':
        return 'System Monitoring';
      case 'locked':
        return 'System Locked';
      case 'offline':
        return 'Offline';
      default:
        return 'Unknown';
    }
  };

  const getStatusColor = () => {
    switch (systemStatus.status) {
      case 'monitoring':
        return 'text-primary';
      case 'locked':
        return 'text-destructive';
      case 'offline':
        return 'text-muted-foreground';
      default:
        return 'text-accent';
    }
  };

  const getConnectionIcon = () => {
    if (isConnected) {
      return <Icon icon={Wifi} className="w-5 h-5 text-success" />;
    } else {
      return <Icon icon={WifiOff} className="w-5 h-5 text-destructive" />;
    }
  };

  const getConnectionHealthIcon = () => {
    switch (systemStatus.connectionHealth) {
      case 'good':
        return <Icon icon={CheckCircle} className="w-4 h-4 text-success" />;
      case 'poor':
        return <Icon icon={AlertCircle} className="w-4 h-4 text-accent" />;
      case 'disconnected':
        return <Icon icon={XCircle} className="w-4 h-4 text-destructive" />;
      default:
        return <Icon icon={AlertCircle} className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const formatLastUpdate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) {
      return 'Just now';
    } else if (minutes < 60) {
      return `${minutes} min ago`;
    } else {
      return date.toLocaleTimeString('en-US');
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center space-x-2">
          <Icon icon={Monitor} className="w-5 h-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">System Status</h2>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* System Status */}
          <div className="bg-muted/30 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-2">
              {getStatusIcon()}
              <div>
                <h3 className="font-medium">System Status</h3>
                <p className={`text-sm font-semibold ${getStatusColor()}`}>
                  {getStatusText()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-1 text-xs text-muted-foreground">
              <Icon icon={Clock} className="w-3 h-3" />
              <span>Last update: {formatLastUpdate(systemStatus.lastUpdate)}</span>
            </div>
          </div>

          {/* Connection Status */}
          <div className="bg-muted/30 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-2">
              {getConnectionIcon()}
              <div>
                <h3 className="font-medium">Connection Status</h3>
                <p className={`text-sm font-semibold ${isConnected ? 'text-success' : 'text-destructive'}`}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              {getConnectionHealthIcon()}
              <span>Status: {connectionState}</span>
            </div>
          </div>

          {/* Current Activity */}
          <div className="bg-muted/30 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-2">
              <Icon icon={Monitor} className="w-5 h-5 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Current Activity</h3>
                <p className="text-sm font-semibold text-foreground">
                  {currentActivity?.applicationName || 'Unknown'}
                </p>
              </div>
            </div>
            {currentActivity && (
              <div className="text-xs text-muted-foreground">
                <div>Category: {currentActivity.category}</div>
                <div>Duration: {Math.floor(currentActivity.duration / 60)} min</div>
                <div className="flex items-center space-x-1 mt-1">
                  <div className={`w-2 h-2 rounded-full ${currentActivity.isActive ? 'bg-success animate-pulse' : 'bg-muted-foreground'}`}></div>
                  <span>{currentActivity.isActive ? 'Active' : 'Inactive'}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* System Status Details */}
        {systemStatus.status === 'locked' && (
          <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Icon icon={ShieldAlert} className="w-5 h-5 text-destructive" />
              <h3 className="font-semibold text-destructive">System Locked</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              The system has detected inappropriate content and locked the screen.
              Please check approval requests.
            </p>
          </div>
        )}

        {!isConnected && (
          <div className="mt-4 p-4 bg-accent/10 border border-accent/20 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Icon icon={WifiOff} className="w-5 h-5 text-accent" />
              <h3 className="font-semibold text-accent">Connection Error</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              Connection to backend server has been lost.
              Automatically attempting to reconnect.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}; 