/**
 * WebSocket Composable for Real-time Updates
 * 
 * Provides reactive WebSocket connections for evaluation progress
 * and notifications in the GuardStack UI.
 */
import { ref, onMounted, onUnmounted, type Ref } from 'vue';

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface EvaluationProgress {
  evaluation_id: string;
  status: string;
  progress: number;
  current_step: string;
  total_steps: number;
  completed_steps: number;
  pillar_results?: Record<string, any>;
  errors?: string[];
}

export interface EvaluationComplete {
  evaluation_id: string;
  status: string;
  overall_score: number;
  pillar_scores: Record<string, number>;
  duration: number;
  results_url: string;
}

export interface UserNotification {
  type: string;
  notification_type: string;
  title: string;
  message: string;
  data: Record<string, any>;
}

interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
}

const DEFAULT_OPTIONS: UseWebSocketOptions = {
  autoConnect: true,
  reconnect: true,
  reconnectAttempts: 5,
  reconnectDelay: 3000,
  heartbeatInterval: 30000,
};

/**
 * Base WebSocket composable
 */
export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
) {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  const ws: Ref<WebSocket | null> = ref(null);
  const isConnected = ref(false);
  const lastMessage: Ref<WebSocketMessage | null> = ref(null);
  const error: Ref<string | null> = ref(null);
  const reconnectCount = ref(0);
  
  let heartbeatTimer: number | null = null;
  let reconnectTimer: number | null = null;
  
  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      return;
    }
    
    try {
      ws.value = new WebSocket(url);
      
      ws.value.onopen = () => {
        isConnected.value = true;
        error.value = null;
        reconnectCount.value = 0;
        startHeartbeat();
      };
      
      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          lastMessage.value = data;
        } catch (e) {
          // Handle non-JSON messages (like pong)
          if (event.data !== 'pong') {
            console.warn('Non-JSON WebSocket message:', event.data);
          }
        }
      };
      
      ws.value.onerror = (event) => {
        error.value = 'WebSocket error occurred';
        console.error('WebSocket error:', event);
      };
      
      ws.value.onclose = () => {
        isConnected.value = false;
        stopHeartbeat();
        
        if (opts.reconnect && reconnectCount.value < (opts.reconnectAttempts || 5)) {
          scheduleReconnect();
        }
      };
    } catch (e) {
      error.value = `Failed to connect: ${e}`;
    }
  };
  
  const disconnect = () => {
    stopHeartbeat();
    stopReconnect();
    
    if (ws.value) {
      ws.value.close();
      ws.value = null;
    }
    
    isConnected.value = false;
  };
  
  const send = (message: any) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      ws.value.send(data);
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  };
  
  const startHeartbeat = () => {
    stopHeartbeat();
    heartbeatTimer = window.setInterval(() => {
      send('ping');
    }, opts.heartbeatInterval);
  };
  
  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  };
  
  const scheduleReconnect = () => {
    stopReconnect();
    reconnectCount.value++;
    
    reconnectTimer = window.setTimeout(() => {
      console.log(`Reconnecting... (attempt ${reconnectCount.value})`);
      connect();
    }, opts.reconnectDelay);
  };
  
  const stopReconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };
  
  onMounted(() => {
    if (opts.autoConnect) {
      connect();
    }
  });
  
  onUnmounted(() => {
    disconnect();
  });
  
  return {
    ws,
    isConnected,
    lastMessage,
    error,
    reconnectCount,
    connect,
    disconnect,
    send,
  };
}

/**
 * WebSocket composable for evaluation progress updates
 */
export function useEvaluationProgress(evaluationId: string) {
  const baseUrl = import.meta.env.VITE_API_WS_URL || 'ws://localhost:8000';
  const url = `${baseUrl}/ws/evaluations/${evaluationId}`;
  
  const {
    ws,
    isConnected,
    lastMessage,
    error,
    connect,
    disconnect,
    send,
  } = useWebSocket(url);
  
  const progress: Ref<EvaluationProgress | null> = ref(null);
  const complete: Ref<EvaluationComplete | null> = ref(null);
  const status = ref('connecting');
  
  // Watch for progress messages
  const processMessage = (message: WebSocketMessage | null) => {
    if (!message) return;
    
    switch (message.type) {
      case 'connected':
        status.value = 'connected';
        break;
      case 'progress':
        progress.value = message as unknown as EvaluationProgress;
        status.value = 'running';
        break;
      case 'complete':
        complete.value = message as unknown as EvaluationComplete;
        status.value = 'complete';
        break;
      case 'heartbeat':
        // Heartbeat received, connection is alive
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  };
  
  // Watch lastMessage changes
  let unwatch: (() => void) | null = null;
  
  onMounted(() => {
    const { watch } = require('vue');
    unwatch = watch(lastMessage, processMessage, { immediate: true });
  });
  
  onUnmounted(() => {
    if (unwatch) unwatch();
  });
  
  return {
    ws,
    isConnected,
    error,
    progress,
    complete,
    status,
    connect,
    disconnect,
  };
}

/**
 * WebSocket composable for user notifications
 */
export function useUserNotifications(userId: string) {
  const baseUrl = import.meta.env.VITE_API_WS_URL || 'ws://localhost:8000';
  const url = `${baseUrl}/ws/user/${userId}`;
  
  const {
    ws,
    isConnected,
    lastMessage,
    error,
    connect,
    disconnect,
  } = useWebSocket(url);
  
  const notifications: Ref<UserNotification[]> = ref([]);
  const unreadCount = ref(0);
  
  // Process incoming notifications
  const processMessage = (message: WebSocketMessage | null) => {
    if (!message) return;
    
    if (message.type === 'notification') {
      const notification = message as unknown as UserNotification;
      notifications.value.unshift(notification);
      unreadCount.value++;
      
      // Limit stored notifications
      if (notifications.value.length > 100) {
        notifications.value = notifications.value.slice(0, 100);
      }
    }
  };
  
  let unwatch: (() => void) | null = null;
  
  onMounted(() => {
    const { watch } = require('vue');
    unwatch = watch(lastMessage, processMessage, { immediate: true });
  });
  
  onUnmounted(() => {
    if (unwatch) unwatch();
  });
  
  const markAllRead = () => {
    unreadCount.value = 0;
  };
  
  const clearNotifications = () => {
    notifications.value = [];
    unreadCount.value = 0;
  };
  
  return {
    ws,
    isConnected,
    error,
    notifications,
    unreadCount,
    connect,
    disconnect,
    markAllRead,
    clearNotifications,
  };
}

/**
 * WebSocket composable for broadcast messages
 */
export function useBroadcast() {
  const baseUrl = import.meta.env.VITE_API_WS_URL || 'ws://localhost:8000';
  const url = `${baseUrl}/ws/broadcast`;
  
  const {
    ws,
    isConnected,
    lastMessage,
    error,
    connect,
    disconnect,
  } = useWebSocket(url);
  
  const broadcasts: Ref<WebSocketMessage[]> = ref([]);
  
  const processMessage = (message: WebSocketMessage | null) => {
    if (!message || message.type === 'connected' || message.type === 'heartbeat') {
      return;
    }
    
    broadcasts.value.unshift(message);
    
    // Limit stored broadcasts
    if (broadcasts.value.length > 50) {
      broadcasts.value = broadcasts.value.slice(0, 50);
    }
  };
  
  let unwatch: (() => void) | null = null;
  
  onMounted(() => {
    const { watch } = require('vue');
    unwatch = watch(lastMessage, processMessage, { immediate: true });
  });
  
  onUnmounted(() => {
    if (unwatch) unwatch();
  });
  
  return {
    ws,
    isConnected,
    error,
    broadcasts,
    connect,
    disconnect,
  };
}

export default useWebSocket;
