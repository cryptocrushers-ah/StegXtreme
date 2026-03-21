import { useState, useEffect } from 'react';
import type { 
  TunnelMessage, 
} from '../api/tunnel';
import {
  startReceiving, 
  stopReceiving, 
  getMessages, 
  getReceiveStatus, 
  clearMessages 
} from '../api/tunnel';

export const useTunnelReceiver = () => {
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<TunnelMessage[]>([]);
  const [port, setPort] = useState(9000);
  const [lanIp, setLanIp] = useState("");
  const [shareableUrl, setShareableUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newMessageCount, setNewMessageCount] = useState(0);

  // Check initial status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await getReceiveStatus();
        setIsListening(status.listening);
        setPort(status.port || 9000);
        setLanIp(status.lan_ip || "");
        setShareableUrl(status.shareable_url || "");
        
        if (status.listening) {
          const { messages } = await getMessages();
          setMessages(messages);
        }
      } catch (err) {
        console.error("Failed to check receiver status", err);
      }
    };
    checkStatus();
  }, []);

  const startListening = async (targetPort: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await startReceiving(targetPort);
      setIsListening(true);
      setPort(response.port);
      setLanIp(response.lan_ip);
      setShareableUrl(response.shareable_url);
    } catch (err: any) {
      setError(err.message || 'Failed to start listening');
    } finally {
      setLoading(false);
    }
  };

  const stopListening = async () => {
    setLoading(true);
    try {
      await stopReceiving();
      setIsListening(false);
      setLanIp("");
      setShareableUrl("");
    } catch (err: any) {
      setError(err.message || 'Failed to stop listening');
    } finally {
      setLoading(false);
    }
  };

  const clearAll = async () => {
    try {
      await clearMessages();
      setMessages([]);
      setNewMessageCount(0);
    } catch (err: any) {
      setError(err.message || 'Failed to clear messages');
    }
  };

  // Polling for new messages
  useEffect(() => {
    if (!isListening) return;

    const interval = setInterval(async () => {
      try {
        const { messages: newMessages } = await getMessages();
        
        if (newMessages.length > messages.length) {
          setNewMessageCount(prev => prev + (newMessages.length - messages.length));
        }
        
        setMessages(newMessages);
      } catch (err) {
        console.error("Failed to poll messages", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isListening, messages.length]);

  return {
    isListening,
    messages,
    port,
    setPort,
    lanIp,
    shareableUrl,
    loading,
    error,
    newMessageCount,
    setNewMessageCount,
    startListening,
    stopListening,
    clearAll
  };
};
