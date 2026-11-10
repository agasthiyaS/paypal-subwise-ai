import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { assistantAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import ReactMarkdown from 'react-markdown';
import {
  Bot,
  User,
  Send,
  Sparkles,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  FileText,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Info,
  ArrowRight,
  BarChart2,
  Layers,
  Calculator,
  Brain,
  Database,
  Zap,
  MessageSquare,
  Clock,
  ChevronRight,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Utility Helpers
// ---------------------------------------------------------------------------
const fmt = (n) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

// ---------------------------------------------------------------------------
// Badge Status → colours mapping
// ---------------------------------------------------------------------------
const BADGE_COLORS = {
  success: { bg: 'var(--emerald-bg)', color: 'var(--emerald-dark)', border: 'var(--emerald-border)' },
  warning: { bg: 'var(--amber-bg)', color: 'var(--amber-dark)', border: 'var(--amber-border)' },
  danger: { bg: '#ffe4e6', color: '#be123c', border: '#fecaca' },
  neutral: { bg: 'var(--bg-subtle)', color: 'var(--navy-slate)', border: 'var(--border-medium)' },
  info: { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
};

// ---------------------------------------------------------------------------
// Intent → icon mapping
// ---------------------------------------------------------------------------
const INTENT_ICONS = {
  AFFORDABILITY_CHECK: Calculator,
  RENEWAL_CALENDAR: Calendar,
  FORECAST_INQUIRY: TrendingUp,
  REPORT_SUMMARY: FileText,
  HEALTH_AND_RISKS: ShieldCheck,
  RECOMMENDATIONS: Sparkles,
  REVENUE_INQUIRY: DollarSign,
  SPEND_OVERVIEW: Layers,
  GENERAL_FINTECH: Brain,
};

// ---------------------------------------------------------------------------
// Suggested Category → icon
// ---------------------------------------------------------------------------
const CATEGORY_ICONS = {
  subscriptions: Layers,
  forecast: TrendingUp,
  affordability: Calculator,
  health: ShieldCheck,
  reports: FileText,
};

// ---------------------------------------------------------------------------
// Evidence Card Component
// ---------------------------------------------------------------------------
const EvidenceCardDisplay = ({ card }) => {
  const statusColors = BADGE_COLORS[card.badge_status] || BADGE_COLORS.neutral;

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: `1.5px solid ${statusColors.border}`,
      borderRadius: 'var(--radius-md)',
      padding: '0.95rem 1.1rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.4rem',
      minWidth: '220px',
      flex: '1 1 220px',
    }}>
      <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-muted)' }}>
        {card.title}
      </div>
      {card.amount !== null && card.amount !== undefined && (
        <div style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontWeight: 800,
          fontSize: '1.45rem',
          color: 'var(--navy-primary)',
          lineHeight: 1.1,
        }}>
          {card.currency === 'USD' ? fmt(card.amount) : `${card.amount} ${card.currency}`}
        </div>
      )}
      {card.badge_label && (
        <span style={{
          display: 'inline-block',
          padding: '0.2rem 0.6rem',
          borderRadius: '99px',
          fontSize: '0.75rem',
          fontWeight: 700,
          background: statusColors.bg,
          color: statusColors.color,
          border: `1px solid ${statusColors.border}`,
          alignSelf: 'flex-start',
        }}>
          {card.badge_label}
        </span>
      )}
      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>
        {card.data_type.replace('_', ' ').toUpperCase()}
      </div>
      {card.navigation_link && (
        <Link
          to={card.navigation_link}
          style={{
            fontSize: '0.78rem',
            color: 'var(--paypal-blue)',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem',
            textDecoration: 'none',
            marginTop: '0.2rem',
          }}
        >
          View Details <ChevronRight size={12} />
        </Link>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Message Bubble Component
// ---------------------------------------------------------------------------
const MessageBubble = ({ msg }) => {
  const isUser = msg.role === 'user';
  const IntentIcon = msg.intent ? (INTENT_ICONS[msg.intent] || Brain) : Bot;

  return (
    <div style={{
      display: 'flex',
      flexDirection: isUser ? 'row-reverse' : 'row',
      gap: '0.75rem',
      alignItems: 'flex-start',
      padding: '0.25rem 0',
    }}>
      {/* Avatar */}
      <div style={{
        width: '36px',
        height: '36px',
        borderRadius: isUser ? 'var(--radius-sm)' : '50%',
        background: isUser
          ? 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)'
          : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
      }}>
        {isUser ? <User size={18} color="#fff" /> : <Bot size={18} color="#fff" />}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: 'min(74%, 740px)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {/* Header: role + intent label + model */}
        {!isUser && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#6366f1' }}>SubWise AI</span>
            {msg.intent && (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.2rem',
                padding: '0.15rem 0.5rem',
                borderRadius: '99px',
                fontSize: '0.7rem',
                fontWeight: 700,
                background: '#eff6ff',
                color: '#1d4ed8',
                border: '1px solid #bfdbfe',
              }}>
                <IntentIcon size={10} />
                {msg.intent.replace(/_/g, ' ')}
              </span>
            )}
            {msg.is_ai_generated && (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.2rem',
                padding: '0.15rem 0.5rem',
                borderRadius: '99px',
                fontSize: '0.7rem',
                fontWeight: 700,
                background: 'var(--emerald-bg)',
                color: 'var(--emerald-dark)',
                border: '1px solid var(--emerald-border)',
              }}>
                <Sparkles size={10} />
                AI-Enhanced
              </span>
            )}
            {!msg.is_ai_generated && msg.generation_model && (
              <span style={{
                fontSize: '0.68rem',
                color: 'var(--text-muted)',
                fontStyle: 'italic',
              }}>
                {msg.generation_model}
              </span>
            )}
          </div>
        )}

        {/* Message text with markdown */}
        <div style={{
          background: isUser
            ? 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)'
            : 'var(--bg-surface)',
          border: isUser ? 'none' : '1px solid var(--border-light)',
          borderRadius: isUser ? '12px 4px 12px 12px' : '4px 12px 12px 12px',
          padding: '0.9rem 1.1rem',
          color: isUser ? '#fff' : 'var(--text-primary)',
          fontSize: '0.9rem',
          lineHeight: 1.6,
          boxShadow: isUser ? '0 2px 8px rgba(0,48,135,0.2)' : '0 1px 4px rgba(0,0,0,0.06)',
        }}>
          {isUser ? (
            <span>{msg.content}</span>
          ) : (
            <div className="assistant-markdown">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Evidence Cards */}
        {!isUser && msg.evidence_cards && msg.evidence_cards.length > 0 && (
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.6rem',
            marginTop: '0.25rem',
          }}>
            {msg.evidence_cards.map((card, idx) => (
              <EvidenceCardDisplay key={idx} card={card} />
            ))}
          </div>
        )}

        {/* Suggested Follow-ups */}
        {!isUser && msg.suggested_followups && msg.suggested_followups.length > 0 && (
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.4rem',
            marginTop: '0.1rem',
          }}>
            {msg.suggested_followups.map((fp, idx) => (
              <button
                key={idx}
                onClick={() => msg.onFollowup && msg.onFollowup(fp)}
                style={{
                  padding: '0.3rem 0.7rem',
                  borderRadius: '99px',
                  border: '1px solid var(--border-light)',
                  background: 'var(--bg-subtle)',
                  color: 'var(--paypal-blue)',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.background = '#eff6ff'}
                onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-subtle)'}
              >
                <ArrowRight size={11} />
                {fp}
              </button>
            ))}
          </div>
        )}

        {/* Disclaimer + Data Status */}
        {!isUser && msg.data_sufficiency_status === 'insufficient_data' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 0.75rem',
            background: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-light)',
            fontSize: '0.74rem',
            color: 'var(--text-muted)',
          }}>
            <Database size={12} color="#94a3b8" />
            <span>Insufficient ledger data — connect a PayPal account with operating transactions for full analysis.</span>
          </div>
        )}

        {/* Timestamp */}
        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', alignSelf: isUser ? 'flex-end' : 'flex-start' }}>
          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Typing indicator
// ---------------------------------------------------------------------------
const TypingIndicator = () => (
  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', padding: '0.25rem 0' }}>
    <div style={{
      width: '36px', height: '36px', borderRadius: '50%',
      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <Bot size={18} color="#fff" />
    </div>
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-light)',
      borderRadius: '4px 12px 12px 12px',
      padding: '0.9rem 1.1rem',
      display: 'flex',
      gap: '5px',
      alignItems: 'center',
    }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: '7px',
          height: '7px',
          borderRadius: '50%',
          background: 'var(--paypal-blue)',
          animation: `typingBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Starter Suggestion Chip
// ---------------------------------------------------------------------------
const SuggestionChip = ({ suggestion, onClick }) => {
  const CatIcon = CATEGORY_ICONS[suggestion.category] || Brain;
  return (
    <button
      onClick={() => onClick(suggestion.prompt)}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.35rem',
        padding: '0.85rem 1rem',
        background: 'var(--bg-surface)',
        border: '1.5px solid var(--border-light)',
        borderRadius: 'var(--radius-md)',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'all 0.15s ease',
        flex: '1 1 180px',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'var(--paypal-blue)';
        e.currentTarget.style.background = '#eff6ff';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--border-light)';
        e.currentTarget.style.background = 'var(--bg-surface)';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <CatIcon size={14} color="var(--paypal-blue)" />
        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--paypal-blue)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {suggestion.label}
        </span>
      </div>
      <div style={{ fontSize: '0.82rem', color: 'var(--text-primary)', lineHeight: 1.4, fontWeight: 500 }}>
        {suggestion.prompt}
      </div>
    </button>
  );
};

// ---------------------------------------------------------------------------
// Insufficient Data Banner
// ---------------------------------------------------------------------------
const InsufficientDataBanner = () => (
  <div style={{
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.85rem',
    padding: '1rem 1.25rem',
    background: 'var(--bg-subtle)',
    borderRadius: 'var(--radius-md)',
    border: '1.5px dashed var(--border-medium)',
    marginBottom: '1rem',
  }}>
    <Database size={20} color="var(--text-muted)" strokeWidth={1.5} />
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.2rem' }}>
        No Verified Operating Data Connected
      </div>
      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
        The connected PayPal Sandbox account has no confirmed operating receipts or recurring subscriptions.
        SubWise AI will answer questions honestly — it will never fabricate revenue, vendor, or cash figures.
        {' '}<Link to="/dashboard" style={{ color: 'var(--paypal-blue)', fontWeight: 700, textDecoration: 'none' }}>
          Sync PayPal transactions →
        </Link>
      </div>
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
const AssistantPage = () => {
  const { business } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [dataStatus, setDataStatus] = useState(null);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);
  const [conversationId] = useState(() => `conv_${Date.now()}`);
  const [inputError, setInputError] = useState('');

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load starter suggestions
  useEffect(() => {
    const load = async () => {
      try {
        const res = await assistantAPI.getSuggestions();
        setSuggestions(res.suggestions || []);
        setDataStatus(res.data_sufficiency_status);
      } catch (err) {
        console.error('Failed to load suggestions:', err);
      } finally {
        setSuggestionsLoading(false);
      }
    };
    load();
  }, []);

  // Auto-scroll to bottom whenever messages update
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleFollowup = useCallback((prompt) => {
    setInputValue(prompt);
    inputRef.current?.focus();
  }, []);

  const sendMessage = useCallback(async (textOverride) => {
    const text = (textOverride || inputValue).trim();
    if (!text) return;
    if (text.length > 500) {
      setInputError('Message too long (max 500 characters)');
      return;
    }
    setInputError('');

    const userMsg = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const res = await assistantAPI.query({
        message: text,
        conversation_id: conversationId,
      });

      const aiMsg = {
        id: `ai_${Date.now()}`,
        role: 'assistant',
        content: res.response_text,
        intent: res.intent,
        is_ai_generated: res.is_ai_generated,
        generation_model: res.generation_model,
        evidence_cards: res.evidence_cards || [],
        suggested_followups: res.suggested_followups || [],
        data_sufficiency_status: res.data_sufficiency_status,
        reporting_period: res.reporting_period,
        disclaimer: res.disclaimer,
        timestamp: new Date().toISOString(),
        onFollowup: handleFollowup,
      };

      setMessages(prev => [...prev, aiMsg]);
      setDataStatus(res.data_sufficiency_status);
    } catch (err) {
      const errMsg = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: '**Service temporarily unavailable.** Please try again in a moment, or navigate to the [Dashboard](/dashboard) for a full overview.',
        intent: 'GENERAL_FINTECH',
        is_ai_generated: false,
        generation_model: 'Error Handler',
        evidence_cards: [],
        suggested_followups: [],
        data_sufficiency_status: 'unknown',
        timestamp: new Date().toISOString(),
        onFollowup: handleFollowup,
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [inputValue, conversationId, handleFollowup]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setInputValue('');
  };

  const hasMessages = messages.length > 0;
  const companyName = business?.company_name || 'Your Business';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 120px)',
      gap: '1.25rem',
    }}>
      {/* ----------------------------------------------------------------- */}
      {/* Page Header                                                        */}
      {/* ----------------------------------------------------------------- */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
            <div style={{
              width: '36px', height: '36px', borderRadius: '50%',
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(99,102,241,0.3)',
            }}>
              <Bot size={20} color="#fff" />
            </div>
            <h1 style={{ fontSize: '1.55rem', fontWeight: 800, color: 'var(--navy-primary)', margin: 0 }}>
              AI Financial Assistant
            </h1>
            <span style={{
              padding: '0.2rem 0.65rem',
              borderRadius: '99px',
              fontSize: '0.73rem',
              fontWeight: 700,
              background: '#f5f3ff',
              color: '#7c3aed',
              border: '1px solid #e9d5ff',
            }}>
              Stage 7 · Beta
            </span>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', margin: 0 }}>
            Ask financial questions about <strong>{companyName}</strong>. All answers are grounded in your verified PayPal ledger records.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          {hasMessages && (
            <button
              onClick={clearConversation}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.5rem 0.9rem',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-muted)',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={14} /> New Chat
            </button>
          )}
          {/* Quick nav links */}
          <Link to="/forecast" style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.5rem 0.9rem',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--navy-slate)',
            fontSize: '0.82rem',
            fontWeight: 600,
            textDecoration: 'none',
          }}>
            <TrendingUp size={14} /> Forecast
          </Link>
          <Link to="/reports" style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.5rem 0.9rem',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--navy-slate)',
            fontSize: '0.82rem',
            fontWeight: 600,
            textDecoration: 'none',
          }}>
            <FileText size={14} /> Reports
          </Link>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Architecture Principles Notice                                      */}
      {/* ----------------------------------------------------------------- */}
      <div style={{
        display: 'flex',
        gap: '0.6rem',
        flexWrap: 'wrap',
      }}>
        {[
          { icon: ShieldCheck, label: 'Zero Hallucination', desc: 'Only verified ledger figures', color: '#059669' },
          { icon: Database, label: 'Deterministic Finance', desc: 'Calculations never delegated to AI', color: '#1d4ed8' },
          { icon: Sparkles, label: 'AI-Enhanced Narratives', desc: 'Gemini 1.5 Flash when available', color: '#7c3aed' },
        ].map(({ icon: Icon, label, desc, color }) => (
          <div key={label} style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.5rem 0.85rem',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-sm)',
            flex: '0 0 auto',
          }}>
            <Icon size={14} color={color} />
            <div>
              <div style={{ fontSize: '0.76rem', fontWeight: 700, color: 'var(--navy-slate)' }}>{label}</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Chat Container                                                      */}
      {/* ----------------------------------------------------------------- */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-surface)',
        border: '1.5px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
        minHeight: 0,
      }}>
        {/* Messages area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.5rem 1.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.1rem',
        }}>
          {/* Show insufficient data banner in chat area when no messages */}
          {!hasMessages && dataStatus === 'insufficient_data' && (
            <InsufficientDataBanner />
          )}

          {/* Starter suggestions (shown when no messages yet) */}
          {!hasMessages && !suggestionsLoading && suggestions.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.85rem',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.07em',
              }}>
                <MessageSquare size={14} />
                Start a conversation
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.65rem' }}>
                {suggestions.map((s, idx) => (
                  <SuggestionChip key={idx} suggestion={s} onClick={sendMessage} />
                ))}
              </div>
              <div style={{ textAlign: 'center', marginTop: '0.5rem' }}>
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  padding: '0.5rem 1rem',
                  background: 'var(--bg-subtle)',
                  borderRadius: '99px',
                  fontSize: '0.78rem',
                  color: 'var(--text-muted)',
                }}>
                  <Brain size={12} />
                  Or type any financial question below — subscriptions, revenue, renewals, cash runway, affordability...
                </div>
              </div>
            </div>
          )}

          {/* Message history */}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}

          {/* Typing indicator */}
          {isLoading && <TypingIndicator />}

          {/* Auto-scroll anchor */}
          <div ref={chatEndRef} />
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Input Bar                                                         */}
        {/* ---------------------------------------------------------------- */}
        <div style={{
          borderTop: '1.5px solid var(--border-light)',
          padding: '1rem 1.25rem',
          background: 'var(--bg-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.4rem',
        }}>
          <div style={{
            display: 'flex',
            gap: '0.6rem',
            alignItems: 'flex-end',
          }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => {
                  setInputValue(e.target.value);
                  if (inputError) setInputError('');
                }}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your subscriptions, cash runway, upcoming renewals, or type 'Can I afford [tool] for $[amount]/month?'"
                rows={2}
                maxLength={500}
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  border: inputError ? '1.5px solid #ef4444' : '1.5px solid var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                  lineHeight: 1.5,
                  resize: 'none',
                  fontFamily: 'inherit',
                  outline: 'none',
                  transition: 'border-color 0.15s ease',
                  boxSizing: 'border-box',
                }}
                onFocus={e => e.target.style.borderColor = 'var(--paypal-blue)'}
                onBlur={e => e.target.style.borderColor = inputError ? '#ef4444' : 'var(--border-medium)'}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={() => sendMessage()}
              disabled={isLoading || !inputValue.trim()}
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-sm)',
                background: (isLoading || !inputValue.trim())
                  ? 'var(--border-medium)'
                  : 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)',
                border: 'none',
                cursor: (isLoading || !inputValue.trim()) ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'all 0.15s ease',
                boxShadow: (isLoading || !inputValue.trim()) ? 'none' : '0 2px 8px rgba(0,48,135,0.25)',
              }}
            >
              {isLoading
                ? <RefreshCw size={18} color="#fff" style={{ animation: 'spin 1s linear infinite' }} />
                : <Send size={18} color="#fff" />
              }
            </button>
          </div>

          {/* Error + char count row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingLeft: '0.1rem' }}>
            {inputError
              ? <span style={{ fontSize: '0.74rem', color: '#ef4444', fontWeight: 600 }}>{inputError}</span>
              : <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Press <kbd style={{ padding: '1px 5px', border: '1px solid var(--border-medium)', borderRadius: '3px', background: 'var(--bg-surface)', fontSize: '0.68rem' }}>Enter</kbd> to send
                  · <kbd style={{ padding: '1px 5px', border: '1px solid var(--border-medium)', borderRadius: '3px', background: 'var(--bg-surface)', fontSize: '0.68rem' }}>Shift+Enter</kbd> for newline
                </span>
            }
            <span style={{ fontSize: '0.72rem', color: inputValue.length > 450 ? '#f59e0b' : 'var(--text-muted)' }}>
              {inputValue.length}/500
            </span>
          </div>

          {/* Governance footer */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.4rem',
            padding: '0.4rem 0 0',
            fontSize: '0.68rem',
            color: 'var(--text-muted)',
          }}>
            <ShieldCheck size={10} color="#94a3b8" />
            SubWise AI never fabricates transactions, vendors, or cash figures. All amounts are sourced from your PayPal ledger or deterministic forecast models.
          </div>
        </div>
      </div>

      {/* Keyframe styles */}
      <style>{`
        @keyframes typingBounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
          30% { transform: translateY(-5px); opacity: 1; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .assistant-markdown h1, .assistant-markdown h2, .assistant-markdown h3,
        .assistant-markdown h4, .assistant-markdown h5 {
          color: var(--navy-primary);
          margin: 0.65rem 0 0.35rem;
          line-height: 1.3;
        }
        .assistant-markdown h3 { font-size: 1rem; }
        .assistant-markdown h4 { font-size: 0.92rem; }
        .assistant-markdown p { margin: 0.3rem 0; }
        .assistant-markdown ul, .assistant-markdown ol {
          margin: 0.3rem 0 0.3rem 1.1rem;
          padding: 0;
        }
        .assistant-markdown li { margin: 0.2rem 0; }
        .assistant-markdown strong { color: var(--navy-primary); font-weight: 700; }
        .assistant-markdown code {
          background: var(--bg-subtle);
          border: 1px solid var(--border-light);
          border-radius: 4px;
          padding: 0.1rem 0.4rem;
          font-size: 0.82em;
          font-family: 'JetBrains Mono', monospace;
          color: var(--navy-slate);
        }
        .assistant-markdown blockquote {
          border-left: 3px solid var(--paypal-blue);
          margin: 0.5rem 0;
          padding: 0.4rem 0.8rem;
          background: var(--bg-subtle);
          border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
          color: var(--text-secondary);
          font-style: normal;
        }
        .assistant-markdown table {
          width: 100%;
          border-collapse: collapse;
          margin: 0.5rem 0;
          font-size: 0.85em;
        }
        .assistant-markdown th {
          background: var(--bg-subtle);
          border: 1px solid var(--border-light);
          padding: 0.4rem 0.65rem;
          text-align: left;
          font-weight: 700;
          color: var(--navy-slate);
        }
        .assistant-markdown td {
          border: 1px solid var(--border-light);
          padding: 0.35rem 0.65rem;
          vertical-align: top;
        }
        .assistant-markdown tr:nth-child(even) td {
          background: var(--bg-subtle);
        }
        .assistant-markdown a {
          color: var(--paypal-blue);
          font-weight: 600;
          text-decoration: none;
        }
        .assistant-markdown a:hover { text-decoration: underline; }
        .assistant-markdown hr {
          border: none;
          border-top: 1px solid var(--border-light);
          margin: 0.65rem 0;
        }
      `}</style>
    </div>
  );
};

export default AssistantPage;

