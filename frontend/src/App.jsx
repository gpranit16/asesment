import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import CitationsModal from './components/CitationsModal';
import {
  sendChatMessage,
  streamChatMessage,
  fetchAvailableSlots,
  fetchThreadState,
  fetchHealth,
} from './services/api';

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export default function App() {
  const [threadId, setThreadId] = useState(() => {
    return localStorage.getItem('agent_thread_id') || generateUUID();
  });
  const [messages, setMessages] = useState([]);
  const [activeNode, setActiveNode] = useState('router');
  const [nodeSteps, setNodeSteps] = useState(['router']);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [healthStatus, setHealthStatus] = useState('healthy');
  const [bookingState, setBookingState] = useState({
    service_type: 'Performance Review',
    stage: 'idle',
    confirmed: false,
  });

  const [citationsModal, setCitationsModal] = useState({
    isOpen: false,
    sources: [],
    primaryPage: 4,
  });

  // Load initial slots and health
  useEffect(() => {
    localStorage.setItem('agent_thread_id', threadId);

    fetchHealth()
      .then((data) => setHealthStatus(data.status || 'healthy'))
      .catch(() => setHealthStatus('offline'));

    loadSlots();
  }, [threadId]);

  const loadSlots = () => {
    fetchAvailableSlots()
      .then((data) => {
        if (data.success && data.available_slots) {
          setAvailableSlots(data.available_slots);
        }
      })
      .catch((err) => console.error('Failed to load slots:', err));
  };

  const handleNewSession = () => {
    const newId = generateUUID();
    setThreadId(newId);
    setMessages([]);
    setActiveNode('router');
    setNodeSteps(['router']);
    setBookingState({
      service_type: 'Performance Review',
      stage: 'idle',
      confirmed: false,
    });
    loadSlots();
  };

  const handleOpenCitations = (sources, primaryPage = 4) => {
    setCitationsModal({
      isOpen: true,
      sources: sources || [],
      primaryPage: primaryPage || 4,
    });
  };

  const handleCloseCitations = () => {
    setCitationsModal((prev) => ({ ...prev, isOpen: false }));
  };

  const handleSendMessage = useCallback(
    async (text) => {
      if (!text || isLoading || isStreaming) return;

      // 1. Add User Message
      const userMsg = { sender: 'user', text };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setActiveNode('router');
      setNodeSteps(['router']);

      if (useStreaming) {
        setIsStreaming(true);
        let accumulatedReply = '';
        let targetNode = 'faq_rag_node';
        let targetIntent = 'faq';
        let sources = [];
        let primaryPage = 4;

        // Placeholder for Assistant Message being streamed
        const botMsgIndex = messages.length + 1;
        setMessages((prev) => [
          ...prev,
          {
            sender: 'bot',
            text: '',
            node: 'router',
            intent: 'processing',
            sources: [],
            isStreaming: true,
          },
        ]);

        await streamChatMessage({
          message: text,
          threadId,
          onNodeChange: (data) => {
            if (data.node) {
              setActiveNode(data.node);
              targetNode = data.node;
              setNodeSteps((prev) => {
                if (!prev.includes(data.node)) return [...prev, data.node];
                return prev;
              });
            }
          },
          onToken: (token) => {
            accumulatedReply += token;
            setMessages((prev) => {
              const copy = [...prev];
              const last = copy[copy.length - 1];
              if (last && last.sender === 'bot') {
                last.text = accumulatedReply;
                last.node = targetNode;
                last.isStreaming = true;
              }
              return copy;
            });
          },
          onMetadata: (meta) => {
            sources = meta.rag_sources || [];
            if (meta.booking_context) {
              setBookingState(meta.booking_context);
              if (meta.booking_context.confirmed) {
                loadSlots();
              }
            }
            if (meta.intermediate_steps) {
              setNodeSteps(meta.intermediate_steps);
            }
            if (sources.length > 0) {
              primaryPage = sources[0].page || 4;
            }
          },
          onDone: () => {
            setIsStreaming(false);
            setIsLoading(false);
            setMessages((prev) => {
              const copy = [...prev];
              const last = copy[copy.length - 1];
              if (last && last.sender === 'bot') {
                last.text = accumulatedReply;
                last.node = targetNode;
                last.sources = sources;
                last.primaryPage = primaryPage;
                last.isStreaming = false;
              }
              return copy;
            });
          },
          onError: (errMsg) => {
            setIsStreaming(false);
            setIsLoading(false);
            setMessages((prev) => {
              const copy = [...prev];
              const last = copy[copy.length - 1];
              if (last && last.sender === 'bot') {
                last.text = `Error: ${errMsg}`;
                last.isStreaming = false;
              }
              return copy;
            });
          },
        });
      } else {
        // Standard non-streaming JSON route
        try {
          const resp = await sendChatMessage(text, threadId);
          setActiveNode(resp.active_node);
          setNodeSteps(resp.intermediate_steps || ['router', resp.active_node]);
          if (resp.booking_context) {
            setBookingState(resp.booking_context);
            if (resp.booking_context.confirmed) {
              loadSlots();
            }
          }

          const primaryPage =
            resp.rag_sources && resp.rag_sources.length > 0
              ? resp.rag_sources[0].page
              : 4;

          setMessages((prev) => [
            ...prev,
            {
              sender: 'bot',
              text: resp.reply,
              node: resp.active_node,
              intent: resp.current_intent,
              sources: resp.rag_sources || [],
              primaryPage,
              isStreaming: false,
            },
          ]);
        } catch (err) {
          setMessages((prev) => [
            ...prev,
            {
              sender: 'bot',
              text: `Error processing request: ${err.message}`,
              node: 'router',
              isStreaming: false,
            },
          ]);
        } finally {
          setIsLoading(false);
        }
      }
    },
    [isLoading, isStreaming, messages.length, threadId, useStreaming]
  );

  return (
    <div className="min-h-screen w-full flex flex-col bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Top Navbar */}
      <Header
        activeNode={activeNode}
        isStreaming={isStreaming || isLoading}
        threadId={threadId}
        onNewSession={handleNewSession}
        healthStatus={healthStatus}
      />

      {/* Main App Layout */}
      <div className="flex-1 flex flex-col lg:flex-row w-full overflow-hidden">
        {/* Left Sidebar: Live Booking Status & Quick Tools */}
        <Sidebar
          booking={bookingState}
          availableSlots={availableSlots}
          onSelectSlot={(slotDisplay) => handleSendMessage(`Let's go with ${slotDisplay}.`)}
          onSampleClick={(sampleText) => handleSendMessage(sampleText)}
        />

        {/* Center: Real-Time Chat Engine */}
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isStreaming={isStreaming}
          activeNode={activeNode}
          nodeSteps={nodeSteps}
          onOpenCitations={handleOpenCitations}
          onSelectSlot={(slotDisplay) => handleSendMessage(`Let's go with ${slotDisplay}.`)}
          useStreaming={useStreaming}
          onToggleStreaming={setUseStreaming}
        />
      </div>

      {/* Citations Modal */}
      <CitationsModal
        isOpen={citationsModal.isOpen}
        onClose={handleCloseCitations}
        sources={citationsModal.sources}
        primaryPage={citationsModal.primaryPage}
      />
    </div>
  );
}
