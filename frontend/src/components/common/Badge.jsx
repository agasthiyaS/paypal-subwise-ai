import React from 'react';
import { ShieldCheck, AlertTriangle, Flame, Layers, Clock } from 'lucide-react';

export const TierBadge = ({ tier }) => {
  if (tier?.includes('1') || tier === '1') {
    return (
      <span className="status-pill status-pill-navy">
        <ShieldCheck size={12} /> Tier 1: Core Ops
      </span>
    );
  }
  if (tier?.includes('2') || tier === '2') {
    return (
      <span className="status-pill" style={{ background: '#f3e8ff', color: '#7e22ce', border: '1px solid #e9d5ff' }}>
        <Layers size={12} /> Tier 2: Important
      </span>
    );
  }
  return (
    <span className="status-pill status-pill-amber">
      <Clock size={12} /> Tier 3: Discretionary
    </span>
  );
};

export const StatusBadge = ({ status, creepPct }) => {
  if (status === 'At Risk' || (creepPct && creepPct >= 15)) {
    return (
      <span className="status-pill status-pill-amber">
        <AlertTriangle size={12} /> Price Creep {creepPct ? `+${creepPct}%` : 'Alert'}
      </span>
    );
  }
  if (status === 'Redundant') {
    return (
      <span className="status-pill status-pill-rose">
        <Flame size={12} /> Redundant Tool
      </span>
    );
  }
  if (status === 'Zombie') {
    return (
      <span className="status-pill status-pill-rose">
        <Flame size={12} /> Low Utilization
      </span>
    );
  }
  return (
    <span className="status-pill status-pill-emerald">
      <ShieldCheck size={12} /> Active
    </span>
  );
};

