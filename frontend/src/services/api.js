const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchAvailableSlots() {
  const res = await fetch(`${API_BASE}/slots`);
  return res.json();
}

export async function fetchThreadState(threadId) {
  if (!threadId) return null;
  const res = await fetch(`${API_BASE}/state/${threadId}`);
  return res.json();
}

export async function sendChatMessage(message, threadId) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  });
  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.statusText}`);
  }
  return res.json();
}

export async function streamChatMessage({
  message,
  threadId,
  onNodeChange,
  onToken,
  onMetadata,
  onDone,
  onError,
}) {
  try {
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, thread_id: threadId }),
    });

    if (!res.ok) {
      throw new Error(`Stream connection failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const block of lines) {
        if (!block.trim()) continue;

        let eventType = 'message';
        let dataStr = '';

        const blockLines = block.split('\n');
        for (const line of blockLines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            dataStr = line.slice(6).trim();
          }
        }

        if (eventType === 'node_change') {
          try {
            const parsed = JSON.parse(dataStr);
            onNodeChange && onNodeChange(parsed);
          } catch (e) {
            console.error('Error parsing node_change event:', e);
          }
        } else if (eventType === 'token') {
          try {
            const parsed = JSON.parse(dataStr);
            onToken && onToken(parsed.token);
          } catch (e) {
            console.error('Error parsing token event:', e);
          }
        } else if (eventType === 'metadata') {
          try {
            const parsed = JSON.parse(dataStr);
            onMetadata && onMetadata(parsed);
          } catch (e) {
            console.error('Error parsing metadata event:', e);
          }
        } else if (eventType === 'done') {
          onDone && onDone();
        } else if (eventType === 'error') {
          try {
            const parsed = JSON.parse(dataStr);
            onError && onError(parsed.error);
          } catch (e) {
            onError && onError(dataStr);
          }
        }
      }
    }
    onDone && onDone();
  } catch (err) {
    console.error('Streaming error:', err);
    onError && onError(err.message);
  }
}
