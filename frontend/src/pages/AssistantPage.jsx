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
  DollarSign,
  Calendar,
  FileText,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Layers,
  Calculator,
  Brain,
  Database,
  MessageSquare,
  ChevronRight,
  Plus,
  Trash2,
  Edit2,
  Copy,
  Check,
  RotateCcw,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  ExternalLink,
  Shield,
  HelpCircle,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Format currency
// ---------------------------------------------------------------------------
const fmt = (n) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

// ---------------------------------------------------------------------------
// Badge status mapping
// ---------------------------------------------------------------------------
const BADGE_COLORS = {
  success: { bg: 'var(--emerald-bg)', color: 'var(--emerald-dark)', border: 'var(--emerald-border)' },
  warning: { bg: 'var(--amber-bg)', color: 'var(--amber-dark)', border: 'var(--amber-border)' },
  danger: { bg: '#ffe4e6', color: '#be123c', border: '#fecaca' },
  neutral: { bg: 'var(--bg-subtle)', color: 'var(--navy-slate)', border: 'var(--border-medium)' },
  info: { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
};

// ---------------------------------------------------------------------------
// Intent to Icon
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
  SPENDING_BREAKDOWN: Layers,
  BUDGET_STATUS: Calculator,
  READ_ONLY_GUARD: Shield,
  HOUSEHOLD_SPENDING: Layers,
  CONTEXTUAL_FOLLOWUP: Brain,
  GENERAL_FINTECH: Brain,
  CASUAL_CONVERSATION: MessageSquare,
  GENERAL_KNOWLEDGE: HelpCircle,
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
      padding: '0.85rem 1rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.35rem',
      minWidth: '200px',
      flex: '1 1 200px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
    }}>
      <div style={{ fontSize: '0.74rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>
        {card.title}
      </div>
      {card.amount !== null && card.amount !== undefined && (
        <div style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontWeight: 800,
          fontSize: '1.35rem',
          color: 'var(--navy-primary)',
          lineHeight: 1.15,
        }}>
          {card.currency === 'USD' ? fmt(card.amount) : `${card.amount} ${card.currency}`}
        </div>
      )}
      {card.badge_label && (
        <span style={{
          display: 'inline-block',
          padding: '0.18rem 0.55rem',
          borderRadius: '99px',
          fontSize: '0.72rem',
          fontWeight: 700,
          background: statusColors.bg,
          color: statusColors.color,
          border: `1px solid ${statusColors.border}`,
          alignSelf: 'flex-start',
        }}>
          {card.badge_label}
        </span>
      )}
      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>
        {card.data_type?.replace(/_/g, ' ').toUpperCase()}
      </div>
      {card.navigation_link && (
        <Link
          to={card.navigation_link}
          style={{
            fontSize: '0.75rem',
            color: 'var(--paypal-blue)',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.2rem',
            textDecoration: 'none',
            marginTop: '0.15rem',
          }}
        >
          View Details <ChevronRight size={12} />
        </Link>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Action Links Bar
// ---------------------------------------------------------------------------
const ActionButtonsDisplay = ({ actions }) => {
  if (!actions || actions.length === 0) return null;

  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: '0.5rem',
      marginTop: '0.35rem',
    }}>
      {actions.map((act, i) => (
        <Link
          key={i}
          to={act.path}
          title={act.description || act.label}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.4rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            background: '#f0fdf4',
            border: '1px solid #bbf7d0',
            color: '#166534',
            fontSize: '0.78rem',
            fontWeight: 700,
            textDecoration: 'none',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = '#dcfce7';
            e.currentTarget.style.borderColor = '#86efac';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = '#f0fdf4';
            e.currentTarget.style.borderColor = '#bbf7d0';
          }}
        >
          <span>{act.label}</span>
          <ExternalLink size={12} />
        </Link>
      ))}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Typing Indicator
// ---------------------------------------------------------------------------
const TypingIndicator = () => (
  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', padding: '0.5rem 0' }}>
    <div style={{
      width: '34px',
      height: '34px',
      borderRadius: '50%',
      background: 'linear-gradient(135deg, #003087 0%, #0070ba 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      boxShadow: '0 2px 6px rgba(0,48,135,0.2)',
    }}>
      <Bot size={17} color="#fff" />
    </div>
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-light)',
      borderRadius: '4px 12px 12px 12px',
      padding: '0.85rem 1.1rem',
      display: 'flex',
      gap: '6px',
      alignItems: 'center',
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
    }}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            background: 'var(--paypal-blue)',
            animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: '4px', fontWeight: 600 }}>
        Consulting financial ledger...
      </span>
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Main AssistantPage Component
// ---------------------------------------------------------------------------
const AssistantPage = () => {
  const { business } = useAuth();
  const navigate = useNavigate();

  const accountType = (business?.account_type || 'business').toLowerCase();
  const companyName = business?.company_name || 'Your Account';

  // State
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [copiedMsgId, setCopiedMsgId] = useState(null);
  const [editingConvId, setEditingConvId] = useState(null);
  const [editTitleValue, setEditTitleValue] = useState('');
  const [providerStatus, setProviderStatus] = useState(null);
  const [starterSuggestions, setStarterSuggestions] = useState([]);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll helper
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Load conversations on mount
  const loadConversations = useCallback(async () => {
    try {
      const list = await assistantAPI.getConversations();
      setConversations(list || []);
      return list;
    } catch (err) {
      console.error('Failed to load conversations:', err);
      return [];
    }
  }, []);

  // Load starter suggestions and provider status
  useEffect(() => {
    const init = async () => {
      try {
        const [sugRes, provRes] = await Promise.allSettled([
          assistantAPI.getSuggestions(),
          assistantAPI.getProviderStatus(),
        ]);
        if (sugRes.status === 'fulfilled') {
          setStarterSuggestions(sugRes.value?.suggestions || []);
        }
        if (provRes.status === 'fulfilled') {
          setProviderStatus(provRes.value);
        }
      } catch (e) {
        console.error('Failed to initialize assistant status:', e);
      }
    };
    init();
    loadConversations();
  }, [loadConversations]);

  // Select a conversation
  const selectConversation = useCallback(async (convId) => {
    if (!convId) {
      setActiveConversationId(null);
      setMessages([]);
      return;
    }
    setActiveConversationId(convId);
    setIsLoading(true);
    try {
      const detail = await assistantAPI.getConversation(convId);
      const parsedMsgs = (detail.messages || []).map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        meta_data: m.meta_data || {},
        created_at: m.created_at,
      }));
      setMessages(parsedMsgs);
    } catch (err) {
      console.error('Failed to load conversation detail:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Create New Chat
  const startNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setInputValue('');
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  // Delete Conversation
  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation thread?')) return;
    try {
      await assistantAPI.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversationId === convId) {
        startNewChat();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  // Rename Conversation
  const handleRenameConversation = async (convId) => {
    if (!editTitleValue.trim()) {
      setEditingConvId(null);
      return;
    }
    try {
      await assistantAPI.renameConversation(convId, editTitleValue.trim());
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, title: editTitleValue.trim() } : c))
      );
    } catch (err) {
      console.error('Failed to rename conversation:', err);
    } finally {
      setEditingConvId(null);
    }
  };

  // Copy message text
  const copyToClipboard = (text, msgId) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(msgId);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  // Send message
  const handleSendMessage = async (textOverride = null) => {
    const textToSend = (textOverride || inputValue).trim();
    if (!textToSend || isLoading) return;

    // Reset input
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Append temporary user bubble
    const tempUserMsg = {
      id: `temp_u_${Date.now()}`,
      role: 'user',
      content: textToSend,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const res = await assistantAPI.chat({
        message: textToSend,
        conversation_id: activeConversationId,
      });

      // Update active conversation ID if newly created
      if (!activeConversationId && res.conversation_id) {
        setActiveConversationId(res.conversation_id);
        await loadConversations();
      }

      // Append assistant response
      const assistantMsg = {
        id: `ai_${Date.now()}`,
        role: 'assistant',
        content: res.message,
        meta_data: {
          provider: res.provider,
          is_ai_generated: res.is_ai_generated,
          generation_model: res.generation_model,
          intent: res.intent,
          data_sufficiency_status: res.data_sufficiency_status,
          evidence_cards: res.evidence_cards || [],
          suggested_followups: res.suggested_followups || [],
          actions: res.actions || [],
          reporting_period: res.reporting_period,
          disclaimer: res.disclaimer,
        },
        created_at: res.created_at || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Failed to send message:', err);
      const errorMsg = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content:
          '**System Notice:** Unable to reach assistant services. Please check your network connection and retry.',
        is_error: true,
        meta_data: { actions: [] },
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  // Retry failed query
  const handleRetry = (lastUserContent) => {
    handleSendMessage(lastUserContent);
  };

  // Keyboard handler: Enter sends, Shift+Enter new line
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Filtered conversation list
  const filteredConversations = conversations.filter((c) =>
    (c.title || '').toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div style={{
      display: 'flex',
      height: 'calc(100vh - 110px)',
      background: 'var(--bg-main)',
      overflow: 'hidden',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border-light)',
      boxShadow: '0 4px 20px rgba(0,0,0,0.04)',
      position: 'relative',
    }}>
      {/* ----------------------------------------------------------------- */}
      {/* 1. SIDEBAR: Conversation History Thread Manager                   */}
      {/* ----------------------------------------------------------------- */}
      <div style={{
        width: isSidebarOpen ? '290px' : '0px',
        minWidth: isSidebarOpen ? '290px' : '0px',
        background: 'var(--bg-surface)',
        borderRight: isSidebarOpen ? '1px solid var(--border-light)' : 'none',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        overflow: 'hidden',
        zIndex: 10,
      }}>
        {/* Top: New Chat Button & Search */}
        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <button
            onClick={startNewChat}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              padding: '0.65rem 1rem',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)',
              color: '#fff',
              fontSize: '0.85rem',
              fontWeight: 700,
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(0,48,135,0.18)',
              transition: 'transform 0.15s ease',
            }}
            onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-1px)'}
            onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <Plus size={16} />
            <span>New Chat</span>
          </button>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.4rem 0.65rem',
            background: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-light)',
          }}>
            <Search size={14} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              style={{
                width: '100%',
                border: 'none',
                background: 'transparent',
                fontSize: '0.78rem',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
            />
          </div>
        </div>

        {/* Conversation List */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0.6rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem',
        }}>
          {filteredConversations.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '2rem 1rem',
              color: 'var(--text-muted)',
              fontSize: '0.8rem',
            }}>
              <MessageSquare size={24} style={{ margin: '0 auto 0.5rem auto', opacity: 0.4 }} />
              No conversations yet. Start a new one!
            </div>
          ) : (
            filteredConversations.map((conv) => {
              const isActive = activeConversationId === conv.id;
              const isEditing = editingConvId === conv.id;

              return (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  style={{
                    padding: '0.65rem 0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    background: isActive ? '#eff6ff' : 'transparent',
                    border: isActive ? '1px solid #bfdbfe' : '1px solid transparent',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '0.5rem',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'var(--bg-subtle)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    {isEditing ? (
                      <input
                        type="text"
                        autoFocus
                        value={editTitleValue}
                        onChange={(e) => setEditTitleValue(e.target.value)}
                        onBlur={() => handleRenameConversation(conv.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleRenameConversation(conv.id);
                          if (e.key === 'Escape') setEditingConvId(null);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        style={{
                          width: '100%',
                          fontSize: '0.8rem',
                          padding: '0.15rem 0.35rem',
                          borderRadius: '4px',
                          border: '1px solid var(--paypal-blue)',
                          outline: 'none',
                        }}
                      />
                    ) : (
                      <>
                        <div style={{
                          fontSize: '0.82rem',
                          fontWeight: isActive ? 700 : 500,
                          color: isActive ? 'var(--paypal-blue)' : 'var(--text-primary)',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}>
                          {conv.title}
                        </div>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          marginTop: '0.15rem',
                        }}>
                          <span style={{
                            fontSize: '0.68rem',
                            fontWeight: 700,
                            padding: '0.05rem 0.35rem',
                            borderRadius: '4px',
                            background: conv.account_type === 'business' ? '#eff6ff' : (conv.account_type === 'household' ? '#fef3c7' : '#ecfdf5'),
                            color: conv.account_type === 'business' ? '#1d4ed8' : (conv.account_type === 'household' ? '#b45309' : '#047857'),
                          }}>
                            {conv.account_type}
                          </span>
                          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                            {new Date(conv.updated_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                          </span>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Actions: Rename / Delete */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', opacity: isActive ? 1 : 0.6 }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingConvId(conv.id);
                        setEditTitleValue(conv.title);
                      }}
                      title="Rename"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        padding: '0.2rem',
                        cursor: 'pointer',
                        color: 'var(--text-muted)',
                      }}
                    >
                      <Edit2 size={12} />
                    </button>
                    <button
                      onClick={(e) => handleDeleteConversation(e, conv.id)}
                      title="Delete"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        padding: '0.2rem',
                        cursor: 'pointer',
                        color: 'var(--text-muted)',
                      }}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Sidebar Footer: Mode Info */}
        <div style={{
          padding: '0.85rem 1rem',
          borderTop: '1px solid var(--border-light)',
          background: 'var(--bg-subtle)',
          fontSize: '0.72rem',
          color: 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}>
          <Shield size={13} color="#059669" />
          <span>Strict Read-Only Ledger Security</span>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* 2. CHAT MAIN VIEWPORT                                             */}
      {/* ----------------------------------------------------------------- */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minWidth: 0,
      }}>
        {/* Top Header Bar */}
        <div style={{
          padding: '0.75rem 1.25rem',
          borderBottom: '1px solid var(--border-light)',
          background: 'var(--bg-surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              onClick={() => setIsSidebarOpen((prev) => !prev)}
              title={isSidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
              style={{
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.35rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                color: 'var(--text-muted)',
              }}
            >
              {isSidebarOpen ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}
            </button>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontWeight: 800, fontSize: '0.98rem', color: 'var(--navy-primary)' }}>
                  SubWise Financial AI
                </span>
                <span style={{
                  padding: '0.15rem 0.5rem',
                  borderRadius: '99px',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  background: '#f0fdf4',
                  color: '#166534',
                  border: '1px solid #bbf7d0',
                }}>
                  {accountType.toUpperCase()}
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {companyName} · Grounded in verified PayPal ledger records
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {providerStatus?.llm_provider_configured ? (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                fontSize: '0.72rem',
                fontWeight: 700,
                color: '#7c3aed',
                background: '#f5f3ff',
                padding: '0.2rem 0.6rem',
                borderRadius: '99px',
                border: '1px solid #e9d5ff',
              }}>
                <Sparkles size={11} />
                Gemini 1.5 Hybrid
              </span>
            ) : (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                fontSize: '0.72rem',
                fontWeight: 700,
                color: '#0369a1',
                background: '#f0f9ff',
                padding: '0.2rem 0.6rem',
                borderRadius: '99px',
                border: '1px solid #bae6fd',
              }}>
                <Database size={11} />
                Deterministic Intelligence
              </span>
            )}
          </div>
        </div>

        {/* Messages Scroll Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}>
          {/* Welcome Screen when no messages */}
          {messages.length === 0 && (
            <div style={{
              margin: 'auto',
              maxWidth: '680px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1.25rem',
              padding: '1.5rem 0',
            }}>
              <div style={{
                width: '54px',
                height: '54px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 16px rgba(0,48,135,0.2)',
              }}>
                <Bot size={28} color="#fff" />
              </div>

              <div>
                <h2 style={{
                  fontSize: '1.65rem',
                  fontWeight: 800,
                  color: 'var(--navy-primary)',
                  marginBottom: '0.4rem',
                  letterSpacing: '-0.02em',
                }}>
                  Your finances, understood.
                </h2>
                <p style={{
                  fontSize: '0.92rem',
                  color: 'var(--text-muted)',
                  lineHeight: 1.5,
                  maxWidth: '520px',
                  margin: '0 auto',
                }}>
                  Ask anything about your spending, savings, subscriptions, and financial health.
                  Responses are verified deterministically against your live records.
                </p>
              </div>

              {/* Starter Suggestion Chips */}
              {starterSuggestions.length > 0 && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: '0.65rem',
                  width: '100%',
                  marginTop: '0.5rem',
                }}>
                  {starterSuggestions.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(s.prompt)}
                      style={{
                        padding: '0.85rem 1rem',
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-surface)',
                        border: '1.5px solid var(--border-light)',
                        textAlign: 'left',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--paypal-blue)';
                        e.currentTarget.style.background = '#f8fafc';
                        e.currentTarget.style.transform = 'translateY(-1px)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--border-light)';
                        e.currentTarget.style.background = 'var(--bg-surface)';
                        e.currentTarget.style.transform = 'translateY(0)';
                      }}
                    >
                      <div style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: 'var(--paypal-blue)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        marginBottom: '0.25rem',
                      }}>
                        {s.label}
                      </div>
                      <div style={{
                        fontSize: '0.82rem',
                        fontWeight: 500,
                        color: 'var(--text-primary)',
                        lineHeight: 1.35,
                      }}>
                        {s.prompt}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Render message dialogue turns */}
          {messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            const meta = msg.meta_data || {};
            const IntentIcon = meta.intent ? (INTENT_ICONS[meta.intent] || Brain) : Bot;

            return (
              <div
                key={msg.id || index}
                style={{
                  display: 'flex',
                  flexDirection: isUser ? 'row-reverse' : 'row',
                  gap: '0.75rem',
                  alignItems: 'flex-start',
                  maxWidth: '100%',
                }}
              >
                {/* Avatar */}
                <div style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: isUser ? 'var(--radius-sm)' : '50%',
                  background: isUser
                    ? 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)'
                    : 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
                }}>
                  {isUser ? <User size={16} color="#fff" /> : <Bot size={16} color="#fff" />}
                </div>

                {/* Message Body */}
                <div style={{
                  maxWidth: 'min(82%, 780px)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.45rem',
                }}>
                  {/* Assistant header badges */}
                  {!isUser && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--navy-primary)' }}>
                        SubWise AI
                      </span>
                      {meta.intent && (
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.2rem',
                          padding: '0.12rem 0.45rem',
                          borderRadius: '99px',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          background: '#eff6ff',
                          color: '#1d4ed8',
                          border: '1px solid #bfdbfe',
                        }}>
                          <IntentIcon size={10} />
                          {meta.intent.replace(/_/g, ' ')}
                        </span>
                      )}
                      {meta.is_ai_generated && (
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.2rem',
                          padding: '0.12rem 0.45rem',
                          borderRadius: '99px',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          background: 'var(--emerald-bg)',
                          color: 'var(--emerald-dark)',
                          border: '1px solid var(--emerald-border)',
                        }}>
                          <Sparkles size={10} />
                          AI
                        </span>
                      )}
                    </div>
                  )}

                  {/* Message bubble */}
                  <div style={{
                    background: isUser
                      ? 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)'
                      : 'var(--bg-surface)',
                    border: isUser ? 'none' : '1px solid var(--border-light)',
                    borderRadius: isUser ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
                    padding: '0.9rem 1.15rem',
                    color: isUser ? '#fff' : 'var(--text-primary)',
                    fontSize: '0.88rem',
                    lineHeight: 1.6,
                    boxShadow: isUser ? '0 2px 8px rgba(0,48,135,0.18)' : '0 1px 4px rgba(0,0,0,0.04)',
                    position: 'relative',
                  }}>
                    {isUser ? (
                      <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                    ) : (
                      <div className="assistant-markdown">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {/* Evidence Cards */}
                  {!isUser && meta.evidence_cards && meta.evidence_cards.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.55rem', marginTop: '0.2rem' }}>
                      {meta.evidence_cards.map((c, i) => (
                        <EvidenceCardDisplay key={i} card={c} />
                      ))}
                    </div>
                  )}

                  {/* Deep Actions */}
                  {!isUser && meta.actions && meta.actions.length > 0 && (
                    <ActionButtonsDisplay actions={meta.actions} />
                  )}

                  {/* Suggested Followups */}
                  {!isUser && meta.suggested_followups && meta.suggested_followups.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.2rem' }}>
                      {meta.suggested_followups.map((fp, i) => (
                        <button
                          key={i}
                          onClick={() => handleSendMessage(fp)}
                          style={{
                            padding: '0.28rem 0.65rem',
                            borderRadius: '99px',
                            border: '1px solid var(--border-light)',
                            background: 'var(--bg-surface)',
                            color: 'var(--paypal-blue)',
                            fontSize: '0.74rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            transition: 'all 0.15s ease',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = '#eff6ff';
                            e.currentTarget.style.borderColor = 'var(--paypal-blue)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'var(--bg-surface)';
                            e.currentTarget.style.borderColor = 'var(--border-light)';
                          }}
                        >
                          <ArrowRight size={10} />
                          {fp}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Footer actions: Copy & Retry & Timestamp */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                    alignSelf: isUser ? 'flex-end' : 'flex-start',
                    fontSize: '0.68rem',
                    color: 'var(--text-muted)',
                    marginTop: '0.1rem',
                  }}>
                    {!isUser && (
                      <button
                        onClick={() => copyToClipboard(msg.content, msg.id || index)}
                        title="Copy to clipboard"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          color: 'var(--text-muted)',
                          padding: '0.1rem',
                        }}
                      >
                        {copiedMsgId === (msg.id || index) ? (
                          <>
                            <Check size={11} color="#059669" />
                            <span style={{ color: '#059669', fontWeight: 700 }}>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy size={11} />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    )}

                    {msg.is_error && (
                      <button
                        onClick={() => {
                          const prevUser = messages[index - 1];
                          if (prevUser && prevUser.role === 'user') {
                            handleRetry(prevUser.content);
                          }
                        }}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.2rem',
                          color: '#dc2626',
                          fontWeight: 700,
                        }}
                      >
                        <RotateCcw size={11} /> Retry
                      </button>
                    )}

                    <span>
                      {new Date(msg.created_at || Date.now()).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {isLoading && <TypingIndicator />}

          <div ref={messagesEndRef} />
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* 3. BOTTOM FIXED INPUT BAR                                         */}
        {/* ----------------------------------------------------------------- */}
        <div style={{
          padding: '0.85rem 1.25rem',
          borderTop: '1px solid var(--border-light)',
          background: 'var(--bg-surface)',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: '0.65rem',
            background: 'var(--bg-main)',
            border: '1.5px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            padding: '0.55rem 0.85rem',
            boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.02)',
          }}>
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputValue}
              onChange={(e) => {
                if (e.target.value.length <= 1000) {
                  setInputValue(e.target.value);
                  // auto-resize up to 4 rows
                  e.target.style.height = 'auto';
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
                }
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your spending, budget, or subscriptions... (Enter to send)"
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                resize: 'none',
                fontSize: '0.88rem',
                lineHeight: 1.45,
                color: 'var(--text-primary)',
                outline: 'none',
                maxHeight: '120px',
                fontFamily: 'inherit',
              }}
            />

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
              <span style={{
                fontSize: '0.68rem',
                color: inputValue.length > 900 ? '#dc2626' : 'var(--text-muted)',
                fontWeight: 600,
              }}>
                {inputValue.length}/1000
              </span>

              <button
                disabled={!inputValue.trim() || isLoading}
                onClick={() => handleSendMessage()}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  background: inputValue.trim() && !isLoading
                    ? 'linear-gradient(135deg, var(--navy-primary) 0%, var(--paypal-blue) 100%)'
                    : 'var(--border-medium)',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: inputValue.trim() && !isLoading ? 'pointer' : 'not-allowed',
                  transition: 'all 0.15s ease',
                }}
              >
                <Send size={15} color="#fff" />
              </button>
            </div>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginTop: '0.4rem',
            fontSize: '0.7rem',
            color: 'var(--text-muted)',
          }}>
            <span>Press Enter to send · Shift+Enter for new line</span>
            <span>Grounded strictly in verified PayPal ledger records</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssistantPage;
