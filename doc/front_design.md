# Parental Control Service Frontend Design Document

## 1. Project Overview

### 1.1 Service Overview
- **Service Name**: Safe Browser AI
- **Purpose**: Provide safe digital experiences for children under 12 years old
- **Core Features**: AI Detection → Function Restriction → Parent Notification → Approval Flow

### 1.2 Technology Stack
- **Frontend**: React.js + Tailwind CSS
- **State Management**: React Context API / Redux
- **Communication**: WebSocket (Real-time notifications) + REST API
- **Build Tool**: Vite
- **Deployment**: Vercel / Netlify

## 2. UI Screen Design

### 2.1 Child Lock Popup Screen (CHILD-LOCK-001)

#### 2.1.1 Functional Requirements
- **Display Trigger**: When AI detects inappropriate behavior
- **Operation Restriction**: Overlay entire screen and block all operations
- **Release Condition**: Parent approval only

#### 2.1.2 Technical Implementation
```javascript
// Full-screen overlay implementation
const ChildLockOverlay = ({ isActive, lockData }) => {
  useEffect(() => {
    if (isActive) {
      // Capture and block all events
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', preventAllActions, true);
      document.addEventListener('contextmenu', preventAllActions, true);
      window.addEventListener('beforeunload', preventPageLeave);
    }
    return () => {
      document.body.style.overflow = 'auto';
      document.removeEventListener('keydown', preventAllActions, true);
      document.removeEventListener('contextmenu', preventAllActions, true);
      window.removeEventListener('beforeunload', preventPageLeave);
    };
  }, [isActive]);

  const preventAllActions = (e) => {
    e.preventDefault();
    e.stopPropagation();
    return false;
  };

  if (!isActive) return null;

  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center"
      style={{ 
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        fontFamily: 'var(--font-sans)'
      }}
    >
      <div 
        className="p-8 max-w-md mx-4"
        style={{
          backgroundColor: 'var(--card)',
          color: 'var(--card-foreground)',
          borderRadius: 'var(--radius)',
          boxShadow: 'var(--shadow-2xl)'
        }}
      >
        {/* Popup content */}
      </div>
    </div>
  );
};
```

#### 2.1.3 Design Specifications
- **z-index**: 9999 (top-most display)
- **Background**: Black semi-transparent overlay (`rgba(0, 0, 0, 0.5)`)
- **Popup**: Center-aligned, card background (`var(--card)`), rounded corners (`var(--radius)`)
- **Color**: Accent color (`var(--accent)`) with appropriate foreground (`var(--accent-foreground)`)
- **Shadow**: Large shadow (`var(--shadow-2xl)`) for prominence

#### 2.1.4 Content Elements
```html
<div className="child-lock-popup">
  <div className="icon-container text-center mb-4">
    <span 
      className="material-icons text-6xl"
      style={{ color: 'var(--accent)' }}
    >
      pause_circle_filled
    </span>
  </div>
  <h2 
    className="title text-2xl font-bold text-center mb-4"
    style={{ 
      color: 'var(--card-foreground)',
      fontFamily: 'var(--font-sans)'
    }}
  >
    Time for a talk!
  </h2>
  <p 
    className="message text-center mb-6"
    style={{ 
      color: 'var(--muted-foreground)',
      fontFamily: 'var(--font-sans)'
    }}
  >
    {dynamicMessage}
  </p>
  <div 
    className="contact-info mb-6 p-4 rounded"
    style={{ 
      backgroundColor: 'var(--muted)',
      color: 'var(--muted-foreground)',
      borderRadius: 'calc(var(--radius) * 0.5)'
    }}
  >
    <p className="mb-2">📞 Phone: 090-XXXX-XXXX</p>
    <p>💬 Messenger: <a href="#" style={{ color: 'var(--primary)' }}>Contact Link</a></p>
  </div>
  <button 
    className="got-it-btn w-full py-3 px-6 font-semibold rounded transition-colors"
    style={{
      backgroundColor: 'var(--primary)',
      color: 'var(--primary-foreground)',
      borderRadius: 'var(--radius)',
      fontFamily: 'var(--font-sans)',
      border: 'none',
      cursor: 'pointer'
    }}
    onMouseOver={(e) => e.target.style.opacity = '0.9'}
    onMouseOut={(e) => e.target.style.opacity = '1'}
  >
    Got it
  </button>
</div>
```

### 2.2 Parent Notification & Approval Screen (PARENT-APPROVE-001)

#### 2.2.1 Functional Requirements
- **Access Method**: Navigate from link in notification
- **Display Content**: Restriction reason, detailed information, approval button
- **Real-time Updates**: State synchronization via WebSocket

#### 2.2.2 Screen Structure
```html
<div 
  className="parent-approval-screen min-h-screen p-6"
  style={{
    backgroundColor: 'var(--background)',
    fontFamily: 'var(--font-sans)'
  }}
>
  <header 
    className="header mb-8 p-6 rounded"
    style={{
      backgroundColor: 'var(--card)',
      color: 'var(--card-foreground)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-md)'
    }}
  >
    <h1 className="text-3xl font-bold">Safe Browser AI - Restriction Review</h1>
  </header>
  
  <section 
    className="restriction-summary mb-6 p-6 rounded"
    style={{
      backgroundColor: 'var(--card)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-md)'
    }}
  >
    <h2 
      className="text-xl font-semibold mb-4"
      style={{ color: 'var(--card-foreground)' }}
    >
      Restriction Summary
    </h2>
    <div className="summary-grid grid grid-cols-1 md:grid-cols-3 gap-4">
      <div 
        className="p-3 rounded"
        style={{
          backgroundColor: 'var(--muted)',
          color: 'var(--muted-foreground)'
        }}
      >
        <strong>Who:</strong> {childName}
      </div>
      <div 
        className="p-3 rounded"
        style={{
          backgroundColor: 'var(--muted)',
          color: 'var(--muted-foreground)'
        }}
      >
        <strong>When:</strong> {timestamp}
      </div>
      <div 
        className="p-3 rounded"
        style={{
          backgroundColor: 'var(--muted)',
          color: 'var(--muted-foreground)'
        }}
      >
        <strong>Where:</strong> {deviceName}
      </div>
    </div>
  </section>
  
  <section 
    className="restriction-details mb-6 p-6 rounded"
    style={{
      backgroundColor: 'var(--card)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-md)'
    }}
  >
    <h2 
      className="text-xl font-semibold mb-4"
      style={{ color: 'var(--card-foreground)' }}
    >
      Restriction Details
    </h2>
    <div className="ai-judgment">
      <p 
        className="mb-4 font-medium"
        style={{ color: 'var(--destructive)' }}
      >
        AI Judgment: {aiJudgment}
      </p>
      <div 
        className="specific-content p-4 rounded"
        style={{
          backgroundColor: 'var(--muted)',
          borderRadius: 'calc(var(--radius) * 0.5)'
        }}
      >
        <p className="mb-2"><strong>URL:</strong> {blockedUrl}</p>
        <p className="mb-2"><strong>Keywords:</strong> {keywords}</p>
        <img 
          src={screenshot} 
          alt="Screenshot" 
          className="mt-4 rounded max-w-full"
          style={{ borderRadius: 'calc(var(--radius) * 0.5)' }}
        />
      </div>
    </div>
  </section>
  
  <section 
    className="ai-explanation mb-6 p-6 rounded"
    style={{
      backgroundColor: 'var(--card)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-md)'
    }}
  >
    <h2 
      className="text-xl font-semibold mb-4"
      style={{ color: 'var(--card-foreground)' }}
    >
      AI Explanation
    </h2>
    <p style={{ color: 'var(--muted-foreground)' }}>{aiExplanation}</p>
  </section>
  
  <section 
    className="action-buttons mb-6 p-6 rounded"
    style={{
      backgroundColor: 'var(--card)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-md)'
    }}
  >
    <div className="flex gap-4 flex-col sm:flex-row">
      <button 
        className="approve-btn flex-1 py-3 px-6 font-semibold rounded transition-colors"
        style={{
          backgroundColor: 'var(--primary)',
          color: 'var(--primary-foreground)',
          borderRadius: 'var(--radius)',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        Approve Usage
      </button>
      <button 
        className="deny-btn flex-1 py-3 px-6 font-semibold rounded transition-colors"
        style={{
          backgroundColor: 'var(--destructive)',
          color: 'var(--destructive-foreground)',
          borderRadius: 'var(--radius)',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        Deny This Time
      </button>
    </div>
  </section>
  
  <section 
    className="feedback p-6 rounded"
    style={{
      backgroundColor: 'var(--card)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-md)'
    }}
  >
    <h2 
      className="text-xl font-semibold mb-4"
      style={{ color: 'var(--card-foreground)' }}
    >
      Feedback
    </h2>
    <button 
      className="feedback-btn py-2 px-4 rounded transition-colors"
      style={{
        backgroundColor: 'var(--secondary)',
        color: 'var(--secondary-foreground)',
        borderRadius: 'var(--radius)',
        border: 'none',
        cursor: 'pointer'
      }}
    >
      Provide Feedback on AI Judgment
    </button>
  </section>
</div>
```

### 2.3 Learning Dashboard Screen

#### 2.3.1 Responsive Layout
```css
/* Dashboard Base Styles */
.dashboard-container {
  background-color: var(--background);
  color: var(--foreground);
  font-family: var(--font-sans);
  min-height: 100vh;
  padding: var(--spacing);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-card {
  background-color: var(--card);
  color: var(--card-foreground);
  border-radius: var(--radius);
  padding: 1.5rem;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border);
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--foreground);
  margin-bottom: 0.5rem;
}

.dashboard-subtitle {
  color: var(--muted-foreground);
  font-size: 1rem;
}

/* Tablet */
@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}

/* Mobile */
@media (max-width: 640px) {
  .dashboard-grid {
    gap: 1rem;
  }
  
  .dashboard-card {
    padding: 1rem;
  }
  
  .dashboard-title {
    font-size: 1.5rem;
  }
}
```

#### 2.3.2 Component Structure
1. **Header**: Title + Description
2. **SafetyReport**: Priority display of safety report
3. **InterestCompass**: Interest visualization
4. **LearningTimeline**: Learning history timeline
5. **CommunicationSupporter**: Parent-child communication support

## 3. Backend Integration Design

### 3.1 API Endpoints

#### 3.1.1 Child Lock Related
```javascript
// Get lock status
GET /api/child/lock-status
Response: {
  isLocked: boolean,
  lockData: {
    id: string,
    reason: string,
    timestamp: string,
    aiJudgment: string,
    blockedContent: object
  }
}

// Acknowledge lock
POST /api/child/acknowledge-lock
Request: { lockId: string }
Response: { acknowledged: boolean }
```

#### 3.1.2 Parent Approval Related
```javascript
// Get restriction details
GET /api/parent/restriction/{lockId}
Response: {
  childName: string,
  timestamp: string,
  deviceName: string,
  aiJudgment: string,
  blockedUrl: string,
  keywords: string[],
  screenshot: string,
  aiExplanation: string
}

// Approve/deny usage
POST /api/parent/approve/{lockId}
Request: { 
  action: 'approve' | 'deny',
  reason?: string 
}
Response: { success: boolean }

// Send feedback
POST /api/parent/feedback/{lockId}
Request: { 
  feedback: string,
  rating: number 
}
Response: { success: boolean }
```

#### 3.1.3 Dashboard Related
```javascript
// Get learning data
GET /api/dashboard/learning-data
Response: {
  safetyReport: object,
  interests: object,
  timeline: object[],
  communicationTips: object
}

// Real-time updates
WebSocket: /ws/dashboard-updates
```

### 3.2 WebSocket Communication Design

#### 3.2.1 Real-time Notifications
```javascript
// WebSocket connection management
const useWebSocket = (url, userId) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`${url}?userId=${userId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      setSocket(ws);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleRealtimeUpdate(data);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      // Reconnection logic
    };
    
    return () => ws.close();
  }, [url, userId]);

  return { socket, isConnected };
};

// Event types
const WEBSOCKET_EVENTS = {
  LOCK_TRIGGERED: 'lock_triggered',
  LOCK_APPROVED: 'lock_approved',
  LOCK_DENIED: 'lock_denied',
  DASHBOARD_UPDATE: 'dashboard_update'
};
```

#### 3.2.2 State Synchronization
```javascript
// Child device state management
const useLockState = () => {
  const [lockState, setLockState] = useState({
    isLocked: false,
    lockData: null
  });

  const { socket } = useWebSocket('/ws/child-updates', childId);

  useEffect(() => {
    if (socket) {
      socket.onmessage = (event) => {
        const { type, data } = JSON.parse(event.data);
        
        switch (type) {
          case WEBSOCKET_EVENTS.LOCK_TRIGGERED:
            setLockState({ isLocked: true, lockData: data });
            break;
          case WEBSOCKET_EVENTS.LOCK_APPROVED:
            setLockState({ isLocked: false, lockData: null });
            break;
        }
      };
    }
  }, [socket]);

  return lockState;
};
```

## 4. Security Measures

### 4.1 Frontend Bypass Prevention
```javascript
// Disable developer tools
const disableDevTools = () => {
  // Disable F12 key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'F12' || 
        (e.ctrlKey && e.shiftKey && e.key === 'I') ||
        (e.ctrlKey && e.shiftKey && e.key === 'C')) {
      e.preventDefault();
      return false;
    }
  });

  // Disable right-click
  document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    return false;
  });
};

// Prevent page leave
const preventPageLeave = (e) => {
  e.preventDefault();
  e.returnValue = '';
  return '';
};
```

### 4.2 Authentication & Authorization
```javascript
// Parent authentication verification
const useParentAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  useEffect(() => {
    const token = localStorage.getItem('parentToken');
    if (token) {
      verifyParentToken(token).then(setIsAuthenticated);
    }
  }, []);

  return { isAuthenticated };
};
```

## 5. Implementation Plan

### 5.1 Folder Structure
```
frontend/
├── public/
│   ├── index.html
│   └── assets/
├── src/
│   ├── components/
│   │   ├── child/
│   │   │   └── LockOverlay.jsx
│   │   ├── parent/
│   │   │   ├── ApprovalScreen.jsx
│   │   │   └── NotificationHandler.jsx
│   │   ├── dashboard/
│   │   │   ├── Header.jsx
│   │   │   ├── SafetyReport.jsx
│   │   │   ├── InterestCompass.jsx
│   │   │   ├── LearningTimeline.jsx
│   │   │   └── CommunicationSupporter.jsx
│   │   └── common/
│   │       ├── Button.jsx
│   │       ├── Card.jsx
│   │       └── WebSocketProvider.jsx
│   ├── hooks/
│   │   ├── useWebSocket.js
│   │   ├── useLockState.js
│   │   └── useParentAuth.js
│   ├── services/
│   │   ├── api.js
│   │   └── websocket.js
│   ├── pages/
│   │   ├── ChildView.jsx
│   │   ├── ParentApproval.jsx
│   │   └── Dashboard.jsx
│   ├── styles/
│   │   └── globals.css
│   └── utils/
│       └── security.js
├── package.json
└── vite.config.js
```

### 5.2 Development Phases
1. **Phase 1**: Child lock popup implementation
2. **Phase 2**: Parent approval screen implementation
3. **Phase 3**: WebSocket real-time communication
4. **Phase 4**: Learning dashboard implementation
5. **Phase 5**: Security enhancement and testing

### 5.3 Technical Challenges and Solutions

#### 5.3.1 Reliable Full-screen Overlay Implementation
- **Challenge**: Prevent user bypass
- **Solutions**: 
  - Event capture utilization
  - Developer tools disabling
  - Server-side state management

#### 5.3.2 Real-time Communication Stability
- **Challenge**: Network disconnection handling
- **Solutions**:
  - Auto-reconnection functionality
  - Offline state retention
  - Heartbeat functionality

#### 5.3.3 Responsive Design Optimization
- **Challenge**: Multi-device support
- **Solutions**:
  - Mobile-first approach
  - Tailwind CSS utilization
  - Progressive enhancement

## 6. CSS Variables Integration

### 6.1 Design System Variables
```css
:root {
  --background: #f7f9f3;
  --foreground: #000000;
  --card: #ffffff;
  --card-foreground: #000000;
  --primary: #4f46e5;
  --primary-foreground: #ffffff;
  --secondary: #14b8a6;
  --secondary-foreground: #ffffff;
  --accent: #f59e0b;
  --accent-foreground: #000000;
  --destructive: #ef4444;
  --destructive-foreground: #ffffff;
  --muted: #f0f0f0;
  --muted-foreground: #333333;
  --border: #000000;
  --font-sans: DM Sans, sans-serif;
  --radius: 1rem;
  --shadow-md: 0px 2px 4px -1px hsl(0 0% 10.1961% / 0.05);
  --shadow-2xl: 0px 0px 0px 0px hsl(0 0% 10.1961% / 0.13);
}

.dark {
  --background: #000000;
  --foreground: #ffffff;
  --card: #1a212b;
  --card-foreground: #ffffff;
  --primary: #818cf8;
  --primary-foreground: #000000;
  --secondary: #2dd4bf;
  --secondary-foreground: #000000;
  --accent: #fcd34d;
  --accent-foreground: #000000;
  --destructive: #f87171;
  --destructive-foreground: #000000;
  --muted: #333333;
  --muted-foreground: #cccccc;
  --border: #545454;
}
```

### 6.2 Color Scheme Usage
- **Primary Colors**: `var(--primary)` for main actions, `var(--secondary)` for secondary actions
- **Accent Colors**: `var(--accent)` for warnings and highlights
- **Destructive Colors**: `var(--destructive)` for deny/dangerous actions
- **Muted Colors**: `var(--muted)` for backgrounds, `var(--muted-foreground)` for secondary text
- **Card System**: `var(--card)` for component backgrounds with `var(--card-foreground)` for text

### 6.3 Typography and Spacing
- **Font Family**: `var(--font-sans)` (DM Sans) for all text elements
- **Border Radius**: `var(--radius)` (1rem) for consistent rounded corners
- **Shadows**: `var(--shadow-md)` for cards, `var(--shadow-2xl)` for prominent overlays

### 6.4 Dark Mode Support
The design system includes full dark mode support with appropriate color adjustments:
- Background transitions from light green (`#f7f9f3`) to black (`#000000`)
- Cards transition from white to dark blue (`#1a212b`)
- All interactive elements maintain proper contrast ratios

## 7. Summary

This design document defines implementation policies centered on "reliable operation restriction" and "real-time communication," which are particularly important for the parental control service frontend.

Full-screen overlay operation restriction is technically feasible, and with proper event handling and security measures, it can prevent bypass attempts by children.

For backend integration, WebSocket-based real-time communication enables immediate state synchronization between parent and child devices.

The design system utilizes CSS custom properties for consistent theming across all components, ensuring a cohesive visual experience with full dark mode support.
