import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../supabaseClient'
import './trainee.css'

export default function TraineeDashboard() {
  const navigate = useNavigate()
  const [section, setSection] = useState('tasks')
  const [dropdownVisit, setDropdownVisit] = useState(null)
  const [toasts, setToasts] = useState([])

  const [isDarkMode, setIsDarkMode] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark-theme')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark-theme')
      localStorage.setItem('theme', 'light')
    }
  }, [isDarkMode])

  const addToast = (message, type = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => {
      setToasts((t) => t.filter((x) => x.id !== id))
    }, 3000)
  }

  const [visits, setVisits] = useState([])
  const [vitals, setVitals] = useState({})
  const [recordedVisits, setRecordedVisits] = useState([])
  const [centers, setCenters] = useState({
    'Village Center (L1)': [
      { id: 'm1', name: 'Paracetamol 500mg', category: 'Analgesic', stock: 240, unit: 'tablets', adequate: true },
      { id: 'm2', name: 'Amoxicillin 250mg', category: 'Antibiotic', stock: 45, unit: 'capsules', adequate: true },
      { id: 'm3', name: 'Ibuprofen 400mg', category: 'NSAID', stock: 5, unit: 'tablets', adequate: false },
      { id: 'm4', name: 'ORS Packets', category: 'Supplement', stock: 50, unit: 'sachets', adequate: true },
      { id: 'm5', name: 'Cetirizine 10mg', category: 'Antihistamine', stock: 0, unit: 'tablets', adequate: false },
    ],
    'Cluster Center (L2)': [
      { id: 'm6', name: 'Ceftriaxone Inj 1g', category: 'Antibiotic', stock: 12, unit: 'vials', adequate: true },
      { id: 'm7', name: 'Insulin Glargine', category: 'Antidiabetic', stock: 2, unit: 'pens', adequate: false },
      { id: 'm8', name: 'Metformin 500mg', category: 'Antidiabetic', stock: 300, unit: 'tablets', adequate: true },
      { id: 'm9', name: 'Amlodipine 5mg', category: 'Antihypertensive', stock: 0, unit: 'tablets', adequate: false },
      { id: 'm10', name: 'Salbutamol Inhaler', category: 'Respiratory', stock: 8, unit: 'inhalers', adequate: true },
    ]
  })

  // On mount or user auth change, fetch trainee tickets
  useEffect(() => {
    const fetchTraineeVisits = async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/trainee/trainee_001/tasks`);
        
        if (!res.ok) throw new Error('Failed to fetch from external API');
        
        const data = await res.json();

        const formattedVisits = data.map((t, index) => ({
          id: t.ticketId,
          idx: index + 1, // Changed from t.ticketId to array index
          name: 'Patient ' + t.patientId.slice(0, 4), // Name isn't in API response
          age: 40,
          sex: 'Unknown',
          address: 'N/A',
          condition: t.symptomsSummary || 'Pending investigation',
          lastBP: '—',
          time: t.createdAt ? new Date(t.createdAt).toLocaleTimeString() : 'Unknown',
          status: t.vitalsData ? 'Done' : 'Pending',
          vitals: t.vitalsData || { sys: '', dia: '', hr: '', spo2: '', temp: '' },
          rawTicket: t
        }));

        setVisits(formattedVisits);
        
        const initialVitals = {};
        formattedVisits.forEach(v => {
          initialVitals[v.id] = v.rawTicket.vitalsData || { sys: '', dia: '', hr: '', spo2: '', temp: '' };
        });
        setVitals(initialVitals);

        setRecordedVisits(formattedVisits.filter(v => v.status === 'Done'));
      } catch (err) {
        console.error('Error fetching trainee visits:', err);
      }
    };

    // Subscribing to tickets table for realtime updates
    const ticketsSubscription = supabase
      .channel('public:tickets')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'tickets' }, payload => {
        fetchTraineeVisits();
      })
      .subscribe();

    fetchTraineeVisits();

    return () => {
      supabase.removeChannel(ticketsSubscription);
    };
  }, [])

  const totalVisits = visits.length
  const completedVisits = recordedVisits.length
  const remainingVisits = Math.max(0, totalVisits - completedVisits)

  const onSubmitVitals = async (id, name) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/trainee/${id}/vitals`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(vitals[id])
      });

      if (!res.ok) throw new Error('Failed to submit vitals');

      addToast(`Vitals submitted for ${name} to Supabase!`, 'success')
      setDropdownVisit(null)
      const visit = visits.find((v) => v.id === id)
      
      // Move to recorded
      setRecordedVisits((prev) => [...prev, { ...visit, vitals: vitals[id] }])
      
      // Update the main visit list status
      setVisits(prev => prev.map(v => v.id === id ? { ...v, status: 'Done' } : v))
    } catch (err) {
      console.error(err);
      addToast(`Failed to submit vitals: ${err.message}`, 'error')
    }
  }

  const activeVisits = visits.filter(v => !recordedVisits.find(r => r.id === v.id))

  const inventoryCenters = Object.keys(centers)
  const [centerTab, setCenterTab] = useState(inventoryCenters[0] || 'Village Center (L1)')
  const [search, setSearch] = useState('')
  const filteredMeds = (centers[centerTab] || []).filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.category.toLowerCase().includes(search.toLowerCase())
  )
  const stats = {
    total: centers[centerTab].length,
    adequate: centers[centerTab].filter((m) => m.adequate).length,
    low: centers[centerTab].filter((m) => !m.adequate && m.stock > 0).length,
    out: centers[centerTab].filter((m) => m.stock === 0).length,
  }

  const [registerModalOpen, setRegisterModalOpen] = useState(false)
  const [patientForm, setPatientForm] = useState({ name: '', age: '', gender: 'Female', mobile: '' })
  
  const today = new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

  const handleRegisterPatient = (e) => {
    e.preventDefault()
    addToast(`${patientForm.name} registered successfully`, 'success')
    setRegisterModalOpen(false)
    setPatientForm({ name: '', age: '', gender: 'Female', mobile: '' })
  }

  return (
    <div className="tp-shell">
      {registerModalOpen && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-head">
              <div className="modal-title">Register Patient</div>
              <button className="close-btn" onClick={() => setRegisterModalOpen(false)}>×</button>
            </div>
            <form onSubmit={handleRegisterPatient}>
              <div className="form-group">
                <label>Patient Name</label>
                <input required value={patientForm.name} onChange={e => setPatientForm({...patientForm, name: e.target.value})} placeholder="Full Name" />
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label>Age</label>
                  <input required type="number" value={patientForm.age} onChange={e => setPatientForm({...patientForm, age: e.target.value})} placeholder="Years" />
                </div>
                <div className="form-group">
                  <label>Gender</label>
                  <select value={patientForm.gender} onChange={e => setPatientForm({...patientForm, gender: e.target.value})}>
                    <option>Female</option>
                    <option>Male</option>
                    <option>Other</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Mobile Number</label>
                <input required type="tel" value={patientForm.mobile} onChange={e => setPatientForm({...patientForm, mobile: e.target.value})} placeholder="+91" />
              </div>
              <button type="submit" className="submit-btn">Confirm Registration</button>
            </form>
          </div>
        </div>
      )}
      <header className="tp-topbar">
        <div className="tp-title">Trainee Dashboard</div>
      </header>
      <div className="tp-body">
        <aside className="tp-sidebar">
          <button className={`nav-item ${section === 'tasks' ? 'active' : ''}`} onClick={() => setSection('tasks')}>Tasks</button>
          <button className={`nav-item ${section === 'recorded' ? 'active' : ''}`} onClick={() => setSection('recorded')}>Recorded</button>
          <button className={`nav-item ${section === 'inventory' ? 'active' : ''}`} onClick={() => setSection('inventory')}>Inventory</button>
          <button className={`nav-item ${section === 'camps' ? 'active' : ''}`} onClick={() => setSection('camps')}>Camps</button>
          <button className={`nav-item ${section === 'settings' ? 'active' : ''}`} onClick={() => setSection('settings')}>Settings</button>
          <button className="nav-item logout-btn" onClick={() => navigate('/')}>Logout</button>
        </aside>
        <main className="tp-main">
          {section === 'tasks' && (
            <div className="tp-page">
              <div className="tp-page-title">Today’s Home Visits</div>
              <div className="tp-subtitle">{today} – Ramgarh Block</div>
              <div className="stats-row">
                <div className="stat-card"><div className="stat-title">Total Visits</div><div className="stat-value">{totalVisits}</div></div>
                <div className="stat-card"><div className="stat-title">Completed</div><div className="stat-value">{completedVisits}</div></div>
                <div className="stat-card"><div className="stat-title">Remaining</div><div className="stat-value">{remainingVisits}</div></div>
              </div>
              <div className="visit-list">
                {activeVisits.map((v) => {
                  const open = dropdownVisit === v.id
                  return (
                    <div key={v.id} className="visit-card">
                      <div className="visit-row">
                        <div className="visit-index">{v.idx}</div>
                        <div className="visit-info">
                          <div className="visit-title">
                            <span className="visit-name">{v.name}</span>
                            <span className="visit-meta"> {v.age}y, {v.sex} • </span>
                            <span className={`chip ${v.status === 'Done' ? 'green' : v.status === 'In Progress' ? 'blue' : 'amber'}`}>{v.status}</span>
                          </div>
                          <div className="meta-row">� {v.address}</div>
                          <div className="meta-row linkish">{v.condition}</div>
                          <div className="meta-row">Last BP: {v.lastBP}</div>
                        </div>
                        <div className="visit-time">{v.time}</div>
                      </div>

                      <div className="visit-actions">
                        <button className="record-btn" onClick={() => setDropdownVisit(open ? null : v.id)}>
                          Record Vitals →
                        </button>
                      </div>

                      {open && (
                        <div className="vitals-horizontal">
                          <div className="vital-item">
                            <label>Sys (mmHg)</label>
                            <input type="number" placeholder="120" value={vitals[v.id].sys} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], sys: e.target.value } }))} />
                          </div>
                          <div className="vital-item">
                            <label>Dia (mmHg)</label>
                            <input type="number" placeholder="80" value={vitals[v.id].dia} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], dia: e.target.value } }))} />
                          </div>
                          <div className="vital-item">
                            <label>HR (bpm)</label>
                            <input type="number" placeholder="72" value={vitals[v.id].hr} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], hr: e.target.value } }))} />
                          </div>
                          <div className="vital-item">
                            <label>SpO2 (%)</label>
                            <input type="number" placeholder="98" value={vitals[v.id].spo2} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], spo2: e.target.value } }))} />
                          </div>
                          <div className="vital-item">
                            <label>Temp (°F)</label>
                            <input type="number" placeholder="98.6" value={vitals[v.id].temp} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], temp: e.target.value } }))} />
                          </div>
                          <button className="vital-submit" onClick={() => onSubmitVitals(v.id, v.name)}>Submit</button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {section === 'recorded' && (
            <div className="tp-page">
              <div className="tp-page-title">Recorded Vitals</div>
              <div className="tp-subtitle">{today} – Ramgarh Block</div>
              {recordedVisits.length === 0 ? (
                <div className="placeholder">No vitals recorded yet</div>
              ) : (
                <div className="visit-list">
                  {recordedVisits.map((v) => {
                    const open = dropdownVisit === v.id
                    return (
                      <div key={v.id} className="visit-card">
                        <div className="visit-row">
                          <div className="visit-index">{v.idx}</div>
                          <div className="visit-info">
                            <div className="visit-title">
                              <span className="visit-name">{v.name}</span>
                              <span className="chip green">Recorded</span>
                            </div>
                            <div className="meta-row">Last Vitals: {v.vitals.sys}/{v.vitals.dia} mmHg • {v.vitals.hr} bpm</div>
                          </div>
                          <div className="visit-actions">
                            <button className="record-btn" onClick={() => setDropdownVisit(open ? null : v.id)}>
                              Edit Vitals ✎
                            </button>
                          </div>
                        </div>

                        {open && (
                          <div className="vitals-horizontal">
                            <div className="vital-item">
                              <label>Sys (mmHg)</label>
                              <input type="number" value={vitals[v.id].sys} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], sys: e.target.value } }))} />
                            </div>
                            <div className="vital-item">
                              <label>Dia (mmHg)</label>
                              <input type="number" value={vitals[v.id].dia} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], dia: e.target.value } }))} />
                            </div>
                            <div className="vital-item">
                              <label>HR (bpm)</label>
                              <input type="number" value={vitals[v.id].hr} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], hr: e.target.value } }))} />
                            </div>
                            <div className="vital-item">
                              <label>SpO2 (%)</label>
                              <input type="number" value={vitals[v.id].spo2} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], spo2: e.target.value } }))} />
                            </div>
                            <div className="vital-item">
                              <label>Temp (°F)</label>
                              <input type="number" value={vitals[v.id].temp} onChange={(e) => setVitals((p) => ({ ...p, [v.id]: { ...p[v.id], temp: e.target.value } }))} />
                            </div>
                            <button className="vital-submit" onClick={() => { addToast(`Vitals updated for ${v.name}`, 'success'); setDropdownVisit(null) }}>Update</button>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {section === 'inventory' && (
            <div className="tp-page">
              <div className="tp-page-title">Medicine Inventory</div>
              <div className="tp-subtitle">{today} – Ramgarh Block</div>

              <div className="tabs">
                {inventoryCenters.map((c) => (
                  <button key={c} className={`tab ${centerTab === c ? 'active' : ''}`} onClick={() => setCenterTab(c)}>
                    {c}
                  </button>
                ))}
                <div style={{ flex: 1 }} />
                <button className="success" onClick={() => addToast(`Restock Requested for ${centerTab}`, 'success')}>+ Request Restock</button>
              </div>

              <div className="stats-row inventory-stats">
                <div className="stat-card"><div className="stat-title">Total Items</div><div className="stat-value">{stats.total}</div></div>
                <div className="stat-card"><div className="stat-title">Adequate</div><div className="stat-value">{stats.adequate}</div></div>
                <div className="stat-card"><div className="stat-title">Low Stock</div><div className="stat-value">{stats.low}</div></div>
                <div className="stat-card"><div className="stat-title">Out of Stock</div><div className="stat-value">{stats.out}</div></div>
              </div>

              <div className="alert red">{stats.low + stats.out} medicine(s) are at low or zero stock. Submit a restock request.</div>

              <div className="search-wrap">
                <span className="mag">🔎</span>
                <input className="search" placeholder="Search medicines by name or category..." value={search} onChange={(e) => setSearch(e.target.value)} />
              </div>

              <div className="table">
                <div className="thead">
                  <div>Medicine</div><div>Category</div><div>Stock</div><div>Unit</div><div>Level</div><div>Status</div><div>Action</div>
                </div>
                {filteredMeds.map((m) => {
                  const pct = Math.min(100, Math.round((m.stock / 240) * 100))
                  const status = m.stock === 0 ? 'Out of Stock' : m.adequate ? 'Adequate' : 'Low Stock'
                  return (
                    <div key={m.id} className="trow">
                      <div className="med-name">{m.name}</div>
                      <div className="med-cat">{m.category}</div>
                      <div>{m.stock}</div>
                      <div>{m.unit}</div>
                      <div>
                        <div className="progress"><div className={`bar ${m.stock === 0 ? '' : m.adequate ? '' : 'warn'}`} style={{ width: `${pct}%` }} /></div>
                      </div>
                      <div><span className={`chip ${status === 'Adequate' ? 'green' : status === 'Low Stock' ? 'amber' : 'red'}`}>{status}</span></div>
                      <div>
                        <button className="restock" onClick={() => addToast(`${m.name} has been reordered`, 'info')}>Reorder</button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {section === 'camps' && (
            <div className="tp-page">
              <div className="tp-page-title">Specialist Camps</div>
              <div className="tp-subtitle">{today} – Ramgarh Block</div>

              <div className="camps-alert">
                <div>
                  <strong>Upcoming specialist camps in your block</strong>
                  <div>3 camps scheduled - 2 confirmed</div>
                </div>
                <button className="register-btn" onClick={() => setRegisterModalOpen(true)}>+ Register Patient</button>
              </div>

              <div className="camp-list">
                <div className="camp-card">
                  <div className="camp-head">
                    <div className="camp-title">
                      <span className="icon-circle green">👁</span> Eye Care Camp <span className="chip green-soft">Confirmed</span>
                    </div>
                  </div>
                  <div className="camp-doc">Dr. Anand Sharma · Ophthalmologist, AIIMS Patna</div>
                  
                  <div className="camp-grid">
                    <div>
                      <div className="label">Date</div>
                      <div className="value">Feb 26, 2026<br/>Thursday</div>
                    </div>
                    <div>
                      <div className="label">Time</div>
                      <div className="value">9:00 AM – 3:00 PM</div>
                    </div>
                    <div>
                      <div className="label">Venue</div>
                      <div className="value">Community Hall, Ramgarh</div>
                    </div>
                    <div>
                      <div className="label">Registered</div>
                      <div className="value">38 / 60</div>
                      <div className="progress"><div className="bar" style={{ width: '63%' }}></div></div>
                    </div>
                  </div>

                  <div className="camp-tasks">
                    <div className="task-head">My Preparation Tasks <span className="task-count">0/3 done</span></div>
                    <div className="task-item"><input type="checkbox" /> Notify registered patients</div>
                    <div className="task-item"><input type="checkbox" /> Arrange chairs & tables</div>
                    <div className="task-item"><input type="checkbox" /> Prepare patient list</div>
                  </div>

                  <div className="camp-note info">
                    ℹ Bring ASHA register. Referral slips from Dr. Verma required.
                  </div>
                </div>

                <div className="camp-card">
                  <div className="camp-head">
                    <div className="camp-title">
                      <span className="icon-circle green">🦷</span> Dental Health Camp <span className="chip green-soft">Confirmed</span>
                    </div>
                  </div>
                  <div className="camp-doc">Dr. Priya Mehta · BDS, District Hospital</div>
                  
                  <div className="camp-grid">
                    <div>
                      <div className="label">Date</div>
                      <div className="value">Mar 3, 2026<br/>Tuesday</div>
                    </div>
                    <div>
                      <div className="label">Time</div>
                      <div className="value">10:00 AM – 2:00 PM</div>
                    </div>
                    <div>
                      <div className="label">Venue</div>
                      <div className="value">PHC Bhalupur</div>
                    </div>
                    <div>
                      <div className="label">Registered</div>
                      <div className="value">22 / 40</div>
                      <div className="progress"><div className="bar" style={{ width: '55%' }}></div></div>
                    </div>
                  </div>

                  <div className="camp-tasks">
                    <div className="task-head">My Preparation Tasks <span className="task-count">0/3 done</span></div>
                    <div className="task-item"><input type="checkbox" /> Pre-screening of patients</div>
                    <div className="task-item"><input type="checkbox" /> Collect dental kits</div>
                    <div className="task-item"><input type="checkbox" /> Update camp register</div>
                  </div>

                  <div className="camp-note info">
                    ℹ Focus on children 6–14 years and elderly above 60.
                  </div>
                </div>

                <div className="camp-card">
                  <div className="camp-head">
                    <div className="camp-title">
                      <span className="icon-circle amber">❤</span> Maternal Health Camp <span className="chip amber-soft">Pending</span>
                    </div>
                  </div>
                  <div className="camp-doc">Dr. Shalini Rao · Gynaecologist, CHC Rewa</div>
                  
                  <div className="camp-grid">
                    <div>
                      <div className="label">Date</div>
                      <div className="value">Mar 10, 2026<br/>Tuesday</div>
                    </div>
                    <div>
                      <div className="label">Time</div>
                      <div className="value">8:30 AM – 1:00 PM</div>
                    </div>
                    <div>
                      <div className="label">Venue</div>
                      <div className="value">Anganwadi Centre, Semra</div>
                    </div>
                    <div>
                      <div className="label">Registered</div>
                      <div className="value">14 / 30</div>
                      <div className="progress"><div className="bar" style={{ width: '46%' }}></div></div>
                    </div>
                  </div>

                  <div className="camp-tasks">
                    <div className="task-head">My Preparation Tasks <span className="task-count">0/3 done</span></div>
                    <div className="task-item"><input type="checkbox" /> Register pregnant women</div>
                    <div className="task-item"><input type="checkbox" /> Prepare USG referral forms</div>
                    <div className="task-item"><input type="checkbox" /> Iron-Folic stock check</div>
                  </div>

                  <div className="camp-note info">
                    ℹ Requires confirmation from District Health Officer.
                  </div>
                </div>
              </div>
            </div>
          )}

          {section === 'settings' && (
            <div className="tp-page">
              <div className="tp-page-title">Settings</div>
              <div className="tp-subtitle">Manage your Trainee preferences</div>

              <div className="camp-card">
                 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                   <div>
                     <div className="camp-title">Dark Mode Theme</div>
                     <div className="camp-doc" style={{ paddingLeft: 0, marginBottom: 0 }}>Switch interface to a low-light dark aesthetic across all dashboards.</div>
                   </div>
                   <div 
                     style={{
                       cursor: 'pointer',
                       background: 'rgba(0,0,0,0.05)',
                       borderRadius: 999,
                       padding: 4,
                       display: 'flex',
                       alignItems: 'center',
                       position: 'relative',
                       width: 80,
                       height: 40
                     }}
                     className={isDarkMode ? 'dark-theme-pad' : ''}
                     onClick={() => setIsDarkMode(!isDarkMode)}
                   >
                     {isDarkMode && <style>{`.dark-theme-pad { background: rgba(255,255,255,0.1) !important; }`}</style>}
                     <div style={{
                       position: 'absolute',
                       width: 32,
                       height: 32,
                       background: 'var(--panel)',
                       color: 'var(--text)',
                       borderRadius: '50%',
                       transition: 'transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1)',
                       boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                       display: 'flex',
                       alignItems: 'center',
                       justifyContent: 'center',
                       fontSize: 16,
                       transform: isDarkMode ? 'translateX(40px)' : 'translateX(0)'
                     }}>
                       {isDarkMode ? '🌙' : '☀️'}
                     </div>
                   </div>
                 </div>
              </div>
            </div>
          )}
        </main>
      </div>
      <div className="toast-wrap">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.type}`}>
            {t.message}
          </div>
        ))}
      </div>
    </div>
  )
}
