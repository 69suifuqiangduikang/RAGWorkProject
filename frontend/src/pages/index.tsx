import type {ReactNode} from 'react';
import {useEffect, useMemo, useRef, useState} from 'react';
import Layout from '@theme/Layout';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import styles from './index.module.css';

type MessageStatus = 'thinking' | 'typing' | 'done' | 'error';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  status: MessageStatus;
  images?: string[];
};

const DEFAULT_API_BASE = 'http://127.0.0.1:8000';
const TYPE_SPEED_MS = 22;

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  const apiBase =
    (siteConfig.customFields?.apiBaseUrl as string | undefined) ?? DEFAULT_API_BASE;
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [useRetrieval, setUseRetrieval] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatStarted, setChatStarted] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [activeImage, setActiveImage] = useState<string | null>(null);
  const typingTimerRef = useRef<number | null>(null);
  const messageListRef = useRef<HTMLDivElement | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const sessionInitRef = useRef<Promise<string | null> | null>(null);

  const navLinks = useMemo(
    () => [
      {label: '友情链接', href: 'https://www.bnu.edu.cn/'},
      {label: '北京师范大学', href: 'https://www.bnu.edu.cn/'},
      {label: '人工智能学院', href: 'https://ai.bnu.edu.cn/'},
      {label: 'AIC服务器平台', href: 'http://aic.bnu.edu.cn/'},
      // {label: '帮助中心', href: '#help'},
    ],
    [],
  );

  useEffect(() => {
    ensureSession();
    return () => {
      if (typingTimerRef.current) {
        window.clearInterval(typingTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const list = messageListRef.current;
    if (list) {
      list.scrollTop = list.scrollHeight;
    }
  }, [messages]);

  const initSession = async () => {
    try {
      const res = await fetch(`${apiBase}/api/sessions/init`, {method: 'POST'});
      if (!res.ok) {
        throw new Error('Session init failed');
      }
      const data = await res.json();
      if (data?.session_id) {
        const id = data.session_id as string;
        sessionIdRef.current = id;
        setSessionId(id);
        return id;
      }
    } catch (error) {
      setSessionId(null);
    }
    return null;
  };

  const clearSession = () => {
    sessionIdRef.current = null;
    setSessionId(null);
  };

  const ensureSession = async () => {
    if (sessionIdRef.current) {
      return sessionIdRef.current;
    }
    if (!sessionInitRef.current) {
      sessionInitRef.current = initSession();
    }
    const id = await sessionInitRef.current;
    sessionInitRef.current = null;
    return id;
  };

  const updateMessage = (id: string, patch: Partial<ChatMessage>) => {
    setMessages((prev) =>
      prev.map((message) => (message.id === id ? {...message, ...patch} : message)),
    );
  };

  const startTyping = (id: string, fullText: string, images: string[]) => {
    let index = 0;
    updateMessage(id, {status: 'typing', content: ''});

    if (typingTimerRef.current) {
      window.clearInterval(typingTimerRef.current);
    }

    typingTimerRef.current = window.setInterval(() => {
      index += 1;
      updateMessage(id, {content: fullText.slice(0, index)});
      if (index >= fullText.length) {
        if (typingTimerRef.current) {
          window.clearInterval(typingTimerRef.current);
        }
        updateMessage(id, {status: 'done', images});
      }
    }, TYPE_SPEED_MS);
  };

  const normalizeImageUrl = (path: string) => {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const safePath = encodeURIComponent(path);
    return `${apiBase}/api/assets/image?path=${safePath}`;
  };

  const openImage = (path: string) => {
    setActiveImage(normalizeImageUrl(path));
  };

  const closeImage = () => {
    setActiveImage(null);
  };

  const handleSend = async () => {
    if (isSending) return;
    const trimmed = input.trim();
    if (!trimmed) return;

    setChatStarted(true);
    setInput('');

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
      status: 'done',
    };

    const assistantMessage: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      status: 'thinking',
      images: [],
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsSending(true);

    const activeSession = sessionId ?? (await ensureSession());
    if (!activeSession) {
      updateMessage(assistantMessage.id, {
        status: 'error',
        content: '会话初始化失败，请稍后重试。',
      });
      setIsSending(false);
      return;
    }

    try {
      const requestChat = async (session: string) => {
        const res = await fetch(`${apiBase}/api/chat?session_id=${session}`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            content: trimmed,
            use_retrieval: useRetrieval,
            top_k: 5,
          }),
        });
        return res;
      };

      let res = await requestChat(activeSession);
      if (res.status === 404) {
        clearSession();
        const newSession = await ensureSession();
        if (!newSession) {
          throw new Error('Session re-init failed');
        }
        res = await requestChat(newSession);
      }

      if (!res.ok) {
        throw new Error('Chat request failed');
      }

      const data = await res.json();
      const answer = String(data?.answer ?? '');
      const images = Array.isArray(data?.retrieved_images)
        ? (data.retrieved_images as string[])
        : [];

      if (!answer.length) {
        updateMessage(assistantMessage.id, {status: 'done', images});
      } else {
        startTyping(assistantMessage.id, answer, images);
      }
    } catch (error) {
      updateMessage(assistantMessage.id, {
        status: 'error',
        content: '服务暂时不可用，请稍后再试。',
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const renderInput = () => (
    <div className={styles.inputCard}>
      <textarea
        className={styles.inputArea}
        placeholder="输入你关于集群使用、模型训练、作业提交的问题..."
        value={input}
        onChange={(event) => setInput(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={3}
      />
      <div className={styles.inputFooter}>
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={useRetrieval}
            onChange={(event) => setUseRetrieval(event.target.checked)}
          />
          <span>检索</span>
        </label>
        <button
          className={styles.sendButton}
          onClick={handleSend}
          disabled={isSending || !input.trim()}
        >
          发送
        </button>
      </div>
    </div>
  );

  return (
    <Layout
      title="北京师范大学 AI 智能助手"
      description="北京师范大学人工智能学院计算服务器集群 AI 智能助手"
      noNavbar
      noFooter>
      <div className={styles.page} data-mode={chatStarted ? 'chat' : 'welcome'}>
        <nav className={styles.nav}>
          <div className={styles.navBrand}>
            <span className={styles.brandMark} />
            <div>
              <div className={styles.brandTitle}>BNU | AI 智能助手</div>
              <div className={styles.brandSubtitle}>计算服务器集群 · RAG 智能对话</div>
            </div>
          </div>
          <div className={styles.navLinks}>
            {navLinks.map((link) => (
              <a key={link.label} className={styles.navLink} href={link.href}>
                {link.label}
              </a>
            ))}
          </div>
        </nav>

        <main className={styles.main}>
          {!chatStarted ? (
            <section className={styles.centerStage}>
              <div className={styles.centerGlow} />
              <div className={styles.welcomeCard}>
                <div className={styles.welcomeTitle}>你好，欢迎进入 AI 智能助手</div>
                <div className={styles.welcomeSubtitle}>
                  面向北京师范大学人工智能学院计算服务器集群的专属 RAG + AI 对话平台
                </div>
                {renderInput()}
              </div>
            </section>
          ) : (
            <section className={styles.chatShell}>
              <div className={styles.chatWindow}>
                <div className={styles.messageList} ref={messageListRef}>
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={
                        message.role === 'user'
                          ? styles.messageRowUser
                          : styles.messageRowAssistant
                      }>
                      <div
                        className={
                          message.role === 'user'
                            ? styles.bubbleUser
                            : styles.bubbleAssistant
                        }
                      >
                        {message.role === 'assistant' && message.status === 'thinking' ? (
                          <div className={styles.thinkingLine}>
                            <span>AI 思考中</span>
                            <span className={styles.thinkingDots}>
                              <span />
                              <span />
                              <span />
                            </span>
                          </div>
                        ) : message.role === 'assistant' ? (
                          <ReactMarkdown
                            className={styles.messageMarkdown}
                            remarkPlugins={[remarkGfm]}
                          >
                            {message.content}
                          </ReactMarkdown>
                        ) : (
                          <p className={styles.messageText}>{message.content}</p>
                        )}
                        {message.role === 'assistant' &&
                        message.status === 'done' &&
                        message.images &&
                        message.images.length > 0 ? (
                          <div className={styles.imageGrid}>
                            {message.images.map((image) => (
                              <button
                                key={image}
                                type="button"
                                className={styles.imageButton}
                                onClick={() => openImage(image)}
                              >
                                <img
                                  className={styles.imageThumb}
                                  src={normalizeImageUrl(image)}
                                  alt="检索结果"
                                  loading="lazy"
                                />
                                <span>查看大图</span>
                              </button>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className={styles.inputDock}>{renderInput()}</div>
            </section>
          )}
        </main>

        <div className={styles.footerFloat}>
          <span>© 2026 北京师范大学人工智能学院 | 计算服务器集群 AI 智能助手</span>
        </div>
        {activeImage ? (
          <div className={styles.imageOverlay} onClick={closeImage}>
            <div className={styles.imageModal} onClick={(event) => event.stopPropagation()}>
              <button type="button" className={styles.modalClose} onClick={closeImage}>
                关闭
              </button>
              <img className={styles.modalImage} src={activeImage} alt="检索图片" />
            </div>
          </div>
        ) : null}
      </div>
    </Layout>
  );
}
