'use client';

import { useState, useEffect } from 'react';
import styles from './page.module.css';

const API_BASE = 'http://localhost:8000/patients';

export default function Home() {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    sex: 'Decline to Answer',
    phone_number: '',
    address_line_1: '',
    city: '',
    state: '',
    zip_code: '',
  });

  const fetchPatients = async () => {
    try {
      const res = await fetch(API_BASE);
      const json = await res.json();
      if (json.error) {
        setError(`Backend error: ${json.error.message}`);
      } else {
        setPatients(json.data || []);
        setError('');
      }
    } catch (err: any) {
      if (err instanceof TypeError && err.message.toLowerCase().includes('fetch')) {
        setError('Cannot reach backend on http://localhost:8000 — is uvicorn running?');
      } else {
        setError(`Unexpected error: ${err.message}`);
      }
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const res = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const json = await res.json();
      
      if (json.error) {
        const fieldPrefix = json.error.field ? `[${json.error.field}] ` : '';
        setError(`${fieldPrefix}${json.error.message}`);
      } else {
        setSuccess(`✅ Patient ${json.data.first_name} ${json.data.last_name} registered successfully!`);
        setFormData({
          first_name: '',
          last_name: '',
          date_of_birth: '',
          sex: 'Decline to Answer',
          phone_number: '',
          address_line_1: '',
          city: '',
          state: '',
          zip_code: '',
        });
        fetchPatients();
      }
    } catch (err: any) {
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to soft-delete this patient?')) return;
    try {
      const res = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.error) {
        setError(json.error.message);
      } else {
        fetchPatients();
      }
    } catch (err) {
      setError('Failed to delete patient');
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Voice AI Dashboard</h1>
        <p className={styles.subtitle}>
          Phase 2 Verification Portal — Test the REST API backend endpoints for patient registration.
        </p>
      </header>

      <main className={styles.mainContent}>
        
        {/* Left Column: Form */}
        <section className={styles.glassCard}>
          <h2 className={styles.cardTitle}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>
            Add New Patient
          </h2>
          
          {error && <div className={styles.errorMessage}>{error}</div>}
          {success && <div className={styles.successMessage}>{success}</div>}
          
          <form onSubmit={handleSubmit}>
            <div className={styles.formGroup}>
              <label className={styles.label}>First Name</label>
              <input required name="first_name" value={formData.first_name} onChange={handleInputChange} className={styles.input} placeholder="John" />
            </div>
            
            <div className={styles.formGroup}>
              <label className={styles.label}>Last Name</label>
              <input required name="last_name" value={formData.last_name} onChange={handleInputChange} className={styles.input} placeholder="Doe" />
            </div>
            
            <div className={styles.formGroup}>
              <label className={styles.label}>Date of Birth</label>
              <input required type="date" name="date_of_birth" value={formData.date_of_birth} onChange={handleInputChange} className={styles.input} />
            </div>
            
            <div className={styles.formGroup}>
              <label className={styles.label}>Sex</label>
              <select name="sex" value={formData.sex} onChange={handleInputChange} className={styles.input}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
                <option value="Decline to Answer">Decline to Answer</option>
              </select>
            </div>
            
            <div className={styles.formGroup}>
              <label className={styles.label}>Phone Number (10 digits)</label>
              <input required name="phone_number" value={formData.phone_number} onChange={handleInputChange} className={styles.input} placeholder="5551234567" />
            </div>
            
            <div className={styles.formGroup}>
              <label className={styles.label}>Address Line 1</label>
              <input required name="address_line_1" value={formData.address_line_1} onChange={handleInputChange} className={styles.input} placeholder="123 Main St" />
            </div>
            
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'}}>
              <div className={styles.formGroup}>
                <label className={styles.label}>City</label>
                <input required name="city" value={formData.city} onChange={handleInputChange} className={styles.input} placeholder="New York" />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>State</label>
                <input required name="state" value={formData.state} onChange={handleInputChange} className={styles.input} placeholder="NY" maxLength={2} />
              </div>
            </div>
            
            <div className={styles.formGroup}>
              <label className={styles.label}>Zip Code</label>
              <input required name="zip_code" value={formData.zip_code} onChange={handleInputChange} className={styles.input} placeholder="10001" />
            </div>

            <button type="submit" disabled={loading} className={styles.submitBtn}>
              {loading ? <span className={styles.spinner}></span> : 'Register Patient'}
            </button>
          </form>
        </section>

        {/* Right Column: List */}
        <section className={styles.glassCard} style={{ display: 'flex', flexDirection: 'column' }}>
          <h2 className={styles.cardTitle}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Registered Patients
          </h2>
          
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem' }}>
            {patients.length === 0 ? (
              <div className={styles.emptyState}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{margin: '0 auto 1rem', opacity: 0.5}}><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
                <p>No active patients found in database.</p>
              </div>
            ) : (
              <div className={styles.patientGrid}>
                {patients.map(p => (
                  <div key={p.patient_id} className={styles.patientCard}>
                    <button onClick={() => handleDelete(p.patient_id)} className={styles.deleteBtn}>Delete</button>
                    <div className={styles.patientName}>{p.first_name} {p.last_name}</div>
                    <div className={styles.patientDetail}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                      {p.phone_number}
                    </div>
                    <div className={styles.patientDetail}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                      {p.date_of_birth} ({p.sex})
                    </div>
                    <div className={styles.patientDetail}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                      {p.city}, {p.state} {p.zip_code}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

      </main>
    </div>
  );
}
