import React from 'react';
import { Card, CardHeader, CardContent } from '../common/Card';
import Button from '../common/Button';
import Icon from '../common/Icon';
import { 
  X, 
  Clock, 
  Monitor, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info,
  Globe,
  Zap
} from 'lucide-react';

interface ApprovalRequest {
  id: string;
  reason: string;
  applicationName?: string;
  timestamp: string;
  blockedUrl?: string;
  keywords?: string[];
  confidence: number;
  screenshot?: string;
  context?: string;
  riskLevel: 'low' | 'medium' | 'high';
}

interface ApprovalModalProps {
  request: ApprovalRequest;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (requestId: string) => void;
  onDeny: (requestId: string) => void;
}

const ApprovalModal: React.FC<ApprovalModalProps> = ({
  request,
  isOpen,
  onClose,
  onApprove,
  onDeny
}) => {
  if (!isOpen) return null;

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-success bg-success/10';
      case 'medium': return 'text-accent bg-accent/10';
      case 'high': return 'text-destructive bg-destructive/10';
      default: return 'text-muted-foreground bg-muted/10';
    }
  };

  const getRiskLevelIcon = (level: string) => {
    switch (level) {
      case 'low': return CheckCircle;
      case 'medium': return AlertTriangle;
      case 'high': return XCircle;
      default: return Info;
    }
  };

  const handleApprove = () => {
    onApprove(request.id);
    onClose();
  };

  const handleDeny = () => {
    onDeny(request.id);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Icon icon={Shield} className="w-6 h-6 text-primary" />
              <h2 className="text-xl font-bold">Approval Request</h2>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <Icon icon={X} className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Request Summary */}
          <div className="bg-muted/30 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <Icon icon={AlertTriangle} className="w-5 h-5 text-accent mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold mb-1">Content Blocked</h3>
                <p className="text-sm text-muted-foreground">{request.reason}</p>
              </div>
            </div>
          </div>

          {/* Screenshot Preview */}
          {request.screenshot && (
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Icon icon={Monitor} className="w-4 h-4" />
                Screenshot Preview
              </h3>
              <div className="border rounded-lg overflow-hidden">
                <img 
                  src={request.screenshot} 
                  alt="Blocked content screenshot" 
                  className="w-full h-auto max-h-64 object-contain bg-muted/10"
                />
              </div>
            </div>
          )}

          {/* Context Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h3 className="font-semibold">Request Details</h3>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Time:</span>
                  <div className="flex items-center gap-1">
                    <Icon icon={Clock} className="w-3 h-3" />
                    <span>{new Date(request.timestamp).toLocaleString()}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Application:</span>
                  <span className="font-medium">{request.applicationName || 'Unknown'}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Risk Level:</span>
                  <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(request.riskLevel)}`}>
                    <Icon icon={getRiskLevelIcon(request.riskLevel)} className="w-3 h-3" />
                    <span className="capitalize">{request.riskLevel}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="font-semibold">AI Analysis</h3>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Confidence:</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-muted rounded-full h-2">
                      <div 
                        className="h-2 bg-primary rounded-full transition-all duration-300"
                        style={{ width: `${Math.round(request.confidence * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium">{Math.round(request.confidence * 100)}%</span>
                  </div>
                </div>

                {request.blockedUrl && (
                  <div className="text-sm">
                    <span className="text-muted-foreground">URL:</span>
                    <div className="flex items-center gap-1 mt-1">
                      <Icon icon={Globe} className="w-3 h-3 text-muted-foreground" />
                      <span className="text-xs bg-muted/50 px-2 py-1 rounded font-mono break-all">
                        {request.blockedUrl}
                      </span>
                    </div>
                  </div>
                )}

                {request.keywords && request.keywords.length > 0 && (
                  <div className="text-sm">
                    <span className="text-muted-foreground">Keywords:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {request.keywords.map((keyword, index) => (
                        <span 
                          key={index} 
                          className="text-xs bg-accent/10 text-accent px-2 py-1 rounded"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Additional Context */}
          {request.context && (
            <div>
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <Icon icon={Info} className="w-4 h-4" />
                Additional Context
              </h3>
              <div className="bg-muted/30 rounded-lg p-3">
                <p className="text-sm text-muted-foreground">{request.context}</p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t">
            <Button 
              variant="primary" 
              onClick={handleApprove}
              className="flex-1 flex items-center justify-center gap-2"
            >
              <Icon icon={CheckCircle} className="w-4 h-4" />
              Approve Access
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDeny}
              className="flex-1 flex items-center justify-center gap-2"
            >
              <Icon icon={XCircle} className="w-4 h-4" />
              Deny Access
            </Button>
          </div>

          {/* Quick Actions */}
          <div className="bg-muted/20 rounded-lg p-3">
            <h4 className="font-medium text-sm mb-2">Quick Actions</h4>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" className="text-xs">
                <Icon icon={Zap} className="w-3 h-3 mr-1" />
                Always Allow This Site
              </Button>
              <Button variant="outline" size="sm" className="text-xs">
                <Icon icon={Clock} className="w-3 h-3 mr-1" />
                Allow for 1 Hour
              </Button>
              <Button variant="outline" size="sm" className="text-xs">
                <Icon icon={Shield} className="w-3 h-3 mr-1" />
                Block Permanently
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApprovalModal; 