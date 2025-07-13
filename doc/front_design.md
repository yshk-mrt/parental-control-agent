# Parental Control Service Frontend Design Document

## 1. Project Overview

### 1.1 Service Overview
- **Service Name**: Safe Browser AI
- **Purpose**: Provide safe digital experiences for children under 12 years old
- **Core Features**: AI Detection → System Lock (Backend) → Parent Notification (Frontend) → Approval Flow

### 1.2 Architecture Overview
- **Frontend Role**: Parent Dashboard & Management Interface
- **Backend Role**: System-level monitoring, AI detection, and screen locking
- **Separation of Concerns**: Frontend handles UI/UX, Backend handles security enforcement

### 1.3 Technology Stack
- **Frontend**: React.js + Tailwind CSS
- **State Management**: React Context API
- **Communication**: WebSocket (Real-time notifications) + REST API
- **Build Tool**: Vite
- **Deployment**: Vercel / Netlify

## 2. UI Screen Design

### 2.1 Parent Dashboard (PARENT-DASH-001)

#### 2.1.1 Functional Requirements
- **Real-time Monitoring**: Display child's current activity status
- **Approval Management**: Handle approval requests from locked system
- **Activity History**: Show past activities and decisions
- **Settings Management**: Configure monitoring rules and restrictions

#### 2.1.2 Technical Implementation
```javascript
// Parent Dashboard with real-time updates
const ParentDashboard = () => {
  const [systemStatus, setSystemStatus] = useState('monitoring');
  const [approvalRequests, setApprovalRequests] = useState([]);
  const [childActivity, setChildActivity] = useState(null);

  useEffect(() => {
    // WebSocket connection to backend
    const ws = new WebSocket('ws://localhost:8080/parent-dashboard');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'SYSTEM_LOCKED':
          setSystemStatus('locked');
          break;
        case 'APPROVAL_REQUEST':
          setApprovalRequests(prev => [...prev, data.request]);
          break;
        case 'ACTIVITY_UPDATE':
          setChildActivity(data.activity);
          break;
      }
    };

    return () => ws.close();
  }, []);
};
```

### 2.2 Approval Request Modal (APPROVAL-001)

#### 2.2.1 Functional Requirements
- **Request Display**: Show blocked content details and reason
- **Screenshot Preview**: Display what child was trying to access
- **Quick Actions**: Approve/Deny buttons with one-click operation
- **Context Information**: Show time, application, and AI confidence level

#### 2.2.2 Technical Implementation
```javascript
// Approval request handling
const ApprovalRequestModal = ({ request, onApprove, onDeny }) => {
  const handleApproval = (approved) => {
    const response = {
      requestId: request.id,
      approved: approved,
      timestamp: new Date().toISOString(),
      parentId: getCurrentParentId()
    };
    
    // Send to backend via WebSocket
    websocket.send(JSON.stringify({
      type: 'APPROVAL_RESPONSE',
      data: response
    }));
    
    approved ? onApprove(request.id) : onDeny(request.id);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">承認リクエスト</h2>
        <div className="mb-4">
          <img src={request.screenshot} alt="Blocked content" className="w-full rounded" />
        </div>
        <p className="mb-4">{request.reason}</p>
        <div className="flex gap-2">
          <button onClick={() => handleApproval(true)} className="bg-green-500 text-white px-4 py-2 rounded">
            承認
          </button>
          <button onClick={() => handleApproval(false)} className="bg-red-500 text-white px-4 py-2 rounded">
            拒否
          </button>
        </div>
      </div>
    </div>
  );
};
```

### 2.3 Learning Dashboard (LEARNING-001)

#### 2.3.1 Functional Requirements
- **Activity Visualization**: Charts showing learning progress and interests
- **Time Management**: Screen time tracking and healthy usage patterns
- **Interest Analysis**: AI-powered analysis of child's learning preferences
- **Progress Reports**: Weekly/monthly summaries for parents

### 2.4 System Status Indicator (STATUS-001)

#### 2.4.1 Functional Requirements
- **Real-time Status**: Show current system state (monitoring/locked/offline)
- **Connection Health**: Display WebSocket connection status
- **Alert System**: Visual and audio notifications for urgent situations

## 3. Backend Integration

### 3.1 System Lock Communication
- **Backend Responsibility**: Full system screen lock using tkinter/pygame
- **Frontend Responsibility**: Receive notifications and manage approval flow
- **Communication Protocol**: WebSocket for real-time updates

### 3.2 API Endpoints
```
GET /api/system/status          - Get current system status
POST /api/approval/respond      - Send approval response
GET /api/activity/history       - Get child activity history
POST /api/settings/update       - Update monitoring settings
```

### 3.3 WebSocket Events
```
// From Backend to Frontend
SYSTEM_LOCKED: { reason, screenshot, timestamp }
APPROVAL_REQUEST: { id, reason, screenshot, confidence }
ACTIVITY_UPDATE: { application, duration, category }
CONNECTION_STATUS: { status, lastHeartbeat }

// From Frontend to Backend
APPROVAL_RESPONSE: { requestId, approved, parentId }
SETTINGS_UPDATE: { rules, restrictions }
HEARTBEAT: { timestamp }
```

## 4. Design System

### 4.1 Color Palette
- **Primary**: #4f46e5 (Indigo) - Main actions and branding
- **Secondary**: #14b8a6 (Teal) - Secondary actions and highlights
- **Accent**: #f59e0b (Amber) - Warnings and attention-grabbing elements
- **Destructive**: #ef4444 (Red) - Dangerous actions and alerts
- **Success**: #10b981 (Green) - Positive actions and confirmations

### 4.2 Typography
- **Font Family**: DM Sans (Google Fonts)
- **Heading Scale**: 
  - H1: 2.25rem (36px) - Page titles
  - H2: 1.875rem (30px) - Section headers
  - H3: 1.5rem (24px) - Subsection headers
  - H4: 1.25rem (20px) - Card titles

### 4.3 Component Specifications

#### 4.3.1 Status Cards
```css
.status-card {
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.status-card.locked {
  border-color: var(--destructive);
  background: rgba(239, 68, 68, 0.05);
}

.status-card.monitoring {
  border-color: var(--primary);
  background: rgba(79, 70, 229, 0.05);
}
```

#### 4.3.2 Approval Buttons
```css
.approval-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s;
}

.approval-button.approve {
  background: var(--success);
  color: white;
}

.approval-button.deny {
  background: var(--destructive);
  color: white;
}
```

## 5. Security Considerations

### 5.1 Frontend Security
- **Authentication**: Parent login with secure tokens
- **Authorization**: Role-based access control
- **Input Validation**: Sanitize all user inputs
- **XSS Prevention**: Content Security Policy headers

### 5.2 Communication Security
- **WebSocket Security**: WSS (WebSocket Secure) protocol
- **API Security**: HTTPS only, JWT tokens
- **Data Encryption**: End-to-end encryption for sensitive data

## 6. Performance Requirements

### 6.1 Real-time Performance
- **WebSocket Latency**: < 100ms for approval requests
- **UI Responsiveness**: < 50ms for user interactions
- **Data Synchronization**: Real-time updates without page refresh

### 6.2 Scalability
- **Concurrent Users**: Support multiple parent devices
- **Data Storage**: Efficient caching for activity history
- **Network Optimization**: Minimize bandwidth usage

## 7. Accessibility

### 7.1 WCAG Compliance
- **Level AA**: Meet WCAG 2.1 AA standards
- **Screen Readers**: Full compatibility with assistive technologies
- **Keyboard Navigation**: Complete keyboard accessibility
- **Color Contrast**: Minimum 4.5:1 ratio for text

### 7.2 Responsive Design
- **Mobile First**: Optimized for mobile devices
- **Tablet Support**: Responsive layout for tablets
- **Desktop Enhancement**: Enhanced features for desktop users

## 8. Testing Strategy

### 8.1 Unit Testing
- **Component Tests**: React Testing Library
- **Hook Tests**: Custom hook testing
- **Utility Tests**: Pure function testing

### 8.2 Integration Testing
- **WebSocket Tests**: Mock WebSocket server
- **API Tests**: Mock API responses
- **End-to-End**: Cypress for critical user flows

### 8.3 Performance Testing
- **Load Testing**: Simulate multiple concurrent users
- **Stress Testing**: Test system limits
- **Memory Profiling**: Monitor memory usage patterns
