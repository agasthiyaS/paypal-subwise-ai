import React, { useState, useEffect } from 'react';
import { transactionsAPI } from '../../services/api';
import { Receipt, Search, ArrowDownRight, ArrowUpRight, ShieldCheck, Database, Layers } from 'lucide-react';

const TransactionLedger = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const data = await transactionsAPI.getTransactions({ limit: 150 });
      setTransactions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const filtered = transactions.filter((tx) =>
    tx.raw_description.toLowerCase().includes(search.toLowerCase()) ||
    tx.normalized_vendor.toLowerCase().includes(search.toLowerCase()) ||
    tx.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="card" style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <h3 style={{ fontSize: '1.45rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.65rem', color: 'var(--navy-slate)' }}>
            <Receipt size={26} color="var(--paypal-blue)" /> PayPal Payment Stream Ledger
          </h3>
          <p style={{ fontSize: '1rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            Standardized transactions normalized from PayPal descriptors
          </p>
        </div>

        <div style={{ position: 'relative', width: '320px' }}>
          <Search size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            className="form-input"
            placeholder="Search descriptor or vendor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: '2.6rem', width: '100%', minHeight: '50px' }}
          />
        </div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>PayPal Raw Descriptor</th>
              <th>Normalized Merchant</th>
              <th>Category</th>
              <th>Gross</th>
              <th>PayPal Fee</th>
              <th>Net Amount</th>
              <th>Source Rail</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  Loading PayPal transactions...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No transactions recorded yet. Click "Sync Transactions" in the header to ingest data.
                </td>
              </tr>
            ) : (
              filtered.map((tx) => {
                const isExpense = tx.gross_amount < 0;
                const d = new Date(tx.transaction_date);
                const dateStr = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

                return (
                  <tr key={tx.id}>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{dateStr}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: '#cbd5e1' }}>
                      {tx.raw_description}
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {tx.normalized_vendor}
                    </td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {tx.category}
                    </td>
                    <td style={{ fontWeight: 700, color: isExpense ? '#f87171' : '#34d399' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                        {isExpense ? <ArrowDownRight size={14} /> : <ArrowUpRight size={14} />}
                        ${Math.abs(tx.gross_amount).toFixed(2)}
                      </div>
                    </td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      ${(tx.fee_amount || 0).toFixed(2)}
                    </td>
                    <td style={{ fontWeight: 600 }}>
                      ${Math.abs(tx.net_amount).toFixed(2)}
                    </td>
                    <td>
                      <span className={`badge ${tx.data_source === 'live' ? 'badge-live' : tx.data_source === 'sandbox' ? 'badge-sandbox' : 'badge-demo'}`}>
                        {tx.data_source}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TransactionLedger;

