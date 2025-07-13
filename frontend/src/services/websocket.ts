export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface SystemStatus {
  status: 'monitoring' | 'locked' | 'offline';
  lastUpdate: string;
  connectionHealth: 'good' | 'poor' | 'disconnected';
}

export interface ApprovalRequest {
  id: string;
  childId: string;
  reason: string;
  screenshot?: string;
  blockedUrl?: string;
  keywords?: string[];
  confidence: number;
  timestamp: string;
  applicationName?: string;
}

export interface ActivityUpdate {
  childId: string;
  applicationName: string;
  duration: number;
  category: string;
  timestamp: string;
  isActive: boolean;
}

type EventHandler = (...args: any[]) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: number | null = null;
  private isConnecting = false;
  private shouldReconnect = true;
  private eventHandlers: Map<string, EventHandler[]> = new Map();

  constructor(url: string = 'ws://localhost:8080/parent-dashboard') {
    this.url = url;
  }

  // Event system implementation
  on(event: string, handler: EventHandler): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  off(event: string, handler: EventHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  once(event: string, handler: EventHandler): void {
    const onceHandler = (...args: any[]) => {
      handler(...args);
      this.off(event, onceHandler);
    };
    this.on(event, onceHandler);
  }

  private emit(event: string, ...args: any[]): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(...args);
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        this.once('connected', resolve);
        this.once('error', reject);
        return;
      }

      this.isConnecting = true;
      console.log('🔌 Connecting to WebSocket:', this.url);

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('❌ Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          this.emit('disconnected', event);

          if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        console.error('❌ Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  disconnect(): void {
    console.log('🔌 Disconnecting WebSocket');
    this.shouldReconnect = false;
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: Omit<WebSocketMessage, 'timestamp'>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const fullMessage: WebSocketMessage = {
        ...message,
        timestamp: new Date().toISOString()
      };
      
      this.ws.send(JSON.stringify(fullMessage));
      console.log('📤 Sent message:', fullMessage.type);
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message:', message.type);
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    console.log('📨 Received message:', message.type);

    switch (message.type) {
      case 'SYSTEM_LOCKED':
        this.emit('systemLocked', message.data);
        break;
      
      case 'SYSTEM_UNLOCKED':
        this.emit('systemUnlocked', message.data);
        break;
      
      case 'APPROVAL_REQUEST':
        this.emit('approvalRequest', message.data as ApprovalRequest);
        break;
      
      case 'ACTIVITY_UPDATE':
        this.emit('activityUpdate', message.data as ActivityUpdate);
        break;
      
      case 'CONNECTION_STATUS':
        this.emit('connectionStatus', message.data as SystemStatus);
        break;
      
      case 'HEARTBEAT_RESPONSE':
        // Heartbeat acknowledged
        break;
      
      default:
        console.warn('⚠️ Unknown message type:', message.type);
        this.emit('unknownMessage', message);
    }
  }

  private scheduleReconnect(): void {
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    
    console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect().catch(error => {
          console.error('❌ Reconnection failed:', error);
        });
      }
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      this.send({
        type: 'HEARTBEAT',
        data: { timestamp: new Date().toISOString() }
      });
    }, 30000); // Send heartbeat every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Convenience methods for common operations
  sendApprovalResponse(requestId: string, approved: boolean, parentId: string): void {
    this.send({
      type: 'APPROVAL_RESPONSE',
      data: {
        requestId,
        approved,
        parentId,
        timestamp: new Date().toISOString()
      }
    });
  }

  requestSystemStatus(): void {
    this.send({
      type: 'REQUEST_SYSTEM_STATUS',
      data: {}
    });
  }

  updateSettings(settings: any): void {
    this.send({
      type: 'SETTINGS_UPDATE',
      data: settings
    });
  }

  // Getters for connection state
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get connectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }
}

// Singleton instance
export const websocketService = new WebSocketService(); 