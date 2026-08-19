import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../supabaseClient'
import './doctor.css'

export default function DoctorDashboard() {
  const navigate = useNavigate()
  
  // State for Tab and Theme
  const [activeTab, setActiveTab] = useState('patients'); // 'patients' | 'settings'
  const [isDarkMode, setIsDarkMode] = useState(() => localStorage.getItem('theme') === 'dark');
  const [isOnline, setIsOnline] = useState(true);

  // Toggle Theme Class on Root
  React.useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark-theme');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark-theme');
      localStorage.setItem('theme', 'light');
    }
  }, [isDarkMode]);

  // State for Toast Notifications
  const [toasts, setToasts] = useState([])
  const addToast = (message, type = 'success') => {
    const id = Math.random().toString(36).slice(2)
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => {
      setToasts((t) => t.filter((x) => x.id !== id))
    }, 3000)
  }

  // Emergency Modal State
  const [showEmergencyModal, setShowEmergencyModal] = useState(false)
  const emergencies = [
    {
      id: 'e1',
      name: 'Rajesh Kumar',
      age: 45,
      gender: 'Male',
      village: 'Dharampur',
      phone: '+91 98765 43210',
      symptoms: ['Chest pain', 'Shortness of breath', 'Dizziness', 'Sweating'],
      aiSummary: 'Patient reports severe chest pain radiating to left arm, shortness of breath, and dizziness. Symptoms started 45 minutes ago. Patient has history of hypertension.'
    },
    {
      id: 'e2',
      name: 'Pooja Verma',
      age: 12,
      gender: 'Female',
      village: 'Rampur',
      phone: '+91 87612 34567',
      symptoms: ['High fever 103F', 'Rash', 'Vomiting'],
      aiSummary: 'Pediatric patient presenting with 103F fever, generalized maculopapular rash, and 2 episodes of vomiting. Suspected viral infection or dengue.'
    }
  ]
  // currentEmergency variable removed to allow mapping all emergencies

  // State from API
  const [patients, setPatients] = useState([])
  const [traineeReports, setTraineeReports] = useState([])
  const [availableMedicines, setAvailableMedicines] = useState([
    { id: 'm1', name: 'Paracetamol 500mg', desc: 'Fever and pain relief', stock: 240, type: 'ok', unit: 'L1 unit' },
    { id: 'm2', name: 'Amoxicillin 250mg', desc: 'Antibiotic for infections', stock: 45, type: 'ok', unit: 'L1 unit' },
    { id: 'm3', name: 'Ibuprofen 400mg', desc: 'NSAID for swelling', stock: 5, type: 'low', unit: 'L1 unit' },
    { id: 'm4', name: 'Ceftriaxone Inj 1g', desc: 'IV Antibiotic', stock: 12, type: 'ok', unit: 'L2 unit' },
    { id: 'm5', name: 'ORS Packets', desc: 'Rehydration salts', stock: 50, type: 'ok', unit: 'L1 unit' }
  ])
  const [selectedId, setSelectedId] = useState(null)
  const [selectedReportId, setSelectedReportId] = useState(null)
  const [outbreaks, setOutbreaks] = useState([])

  useEffect(() => {
    const fetchOutbreaks = async () => {
      try {
        const response = await fetch('https://curago-backend.onrender.com/api/analytics/outbreaks');
        const data = await response.json();
        if (data.outbreaks) {
          setOutbreaks(data.outbreaks);
        }
      } catch (err) {
        console.error("Failed to fetch outbreak analytics:", err);
      }
    };
    fetchOutbreaks();
    // Poll every minute
    const interval = setInterval(fetchOutbreaks, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const { data: ticketsData, error: ticketsError } = await supabase
          .from('tickets')
          .select('*, patients(*)')
          .order('created_at', { ascending: false });

        if (ticketsError) throw ticketsError;
        
        const formatted = (ticketsData || []).map(t => {
          const pInfo = t.patients || {};
          return {
            id: t.id,
            name: pInfo.name || 'Unknown Patient',
            age: pInfo.age || 'N/A',
            gender: pInfo.gender || 'Not Specified',
            village: pInfo.village || 'N/A',
            phone: pInfo.phone_number || 'N/A',
            severity: t.severity || 'Medium',
            timeAgo: t.created_at ? new Date(t.created_at).toLocaleTimeString() : 'Just now',
            previousVisits: 0,
            symptoms: t.symptoms_summary ? [t.symptoms_summary] : ['Unspecified symptoms'],
            aiSummary: t.symptoms_summary || 'No AI summary available.',
            rawTicket: t
          };
        });

        setPatients(formatted);
        if (formatted.length > 0) setSelectedId(formatted[0].id);
      } catch (err) {
        console.error('Error fetching patients from Supabase:', err);
      }
    };

    const fetchTrainees = async () => {
      try {
        const { data: ticketsData, error: ticketsError } = await supabase
          .from('tickets')
          .select('*')
          .not('assigned_trainee_id', 'is', null);

        if (ticketsError) throw ticketsError;
        
        // Fetch patient details from Supabase using the patient_ids from the tickets
        const patientIds = [...new Set(ticketsData.map(t => t.patient_id))].filter(Boolean);
        let patientsData = [];
        
        if (patientIds.length > 0) {
          const { data: pData, error: pError } = await supabase
            .from('patients')
            .select('*')
            .in('id', patientIds); 
            
          if (!pError && pData) {
            patientsData = pData;
          }
        }
        
        // Map the patient info by ID for quick lookup
        const patientMap = {};
        patientsData.forEach(p => {
          const id = p.id;
          patientMap[id] = p;
        });

         const formatted = ticketsData.map(t => {
           const pInfo = patientMap[t.patient_id] || {};
           return {
             id: t.id,
             name: pInfo.name || 'Patient ' + t.patient_id?.slice(0, 4),
             age: pInfo.age || 45,
             gender: pInfo.gender || 'Not Specified',
             village: pInfo.village || 'N/A',
             phone: pInfo.phone_number || 'N/A',
             timeAgo: t.created_at ? new Date(t.created_at).toLocaleTimeString() : 'Unknown',
             previousVisits: pInfo.previousVisits || 0,
             trainee: 'Trainee ' + (t.assigned_trainee_id?.slice(0,4) || 'Unknown'),
             vitals: t.vitals_data ? {
                bp: t.vitals_data.blood_pressure || '',
                spo2: t.vitals_data.spo2 || '',
                temp: t.vitals_data.temperature || ''
             } : null,
             physicalNotes: 'Status: ' + t.status,
             symptomsSummary: t.symptoms_summary || '',
             isUrgent: t.severity === 'High',
             photoUrls: t.vitals_data?.photo_urls || []
           };
        });

        setTraineeReports(formatted);
        if (formatted.length > 0) setSelectedReportId(formatted[0].id);
      } catch (err) {
        console.error('Error fetching reports from Supabase:', err);
      }
    };


    const ticketsSub = supabase
      .channel('doctor-tickets')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'tickets' }, payload => {
        fetchPatients();
        fetchTrainees();
      })
      .subscribe();

    fetchPatients();
    fetchTrainees();

    return () => {
      supabase.removeChannel(ticketsSub);
    }
  }, [])

  const patient = patients.find(p => p.id === selectedId) || null
  const report = traineeReports.find(r => r.id === selectedReportId) || null

  const [prescriptions, setPrescriptions] = useState({})
  
  const [searchMed, setSearchMed] = useState('')
  const [showSearchDropdown, setShowSearchDropdown] = useState(false)

  // Escalation Management
  const [selectedCamp, setSelectedCamp] = useState("")
  const [selectedReportCamp, setSelectedReportCamp] = useState("")

  // Filter medicines based on search input
  const filteredMedicines = searchMed.trim() === '' 
    ? availableMedicines 
    : availableMedicines.filter(m => m.name.toLowerCase().includes(searchMed.toLowerCase()) || m.desc.toLowerCase().includes(searchMed.toLowerCase()))

  const handleSelectMedicineInfo = (newMed, isReport = false) => {
    const currentId = isReport ? selectedReportId : selectedId;
    setPrescriptions(prev => {
      const current = prev[currentId] || []
      // Check if already prescribed
      if (current.find(m => m.id === newMed.id)) {
        addToast(`${newMed.name} is already prescribed`, 'error')
        return prev
      }
      return { ...prev, [currentId]: [...current, newMed] }
    })
    setSearchMed('')
    setShowSearchDropdown(false)
    addToast(`${newMed.name} added to prescription`)
  }

  const handleAddMedicine = (e, isReport = false) => {
    if(e) e.preventDefault()
    
    if(!searchMed) {
      addToast('Please search and select a medicine', 'error')
      return
    }

    // Fallback: If they press enter, try to pick the first filtered result or create custom
    if (filteredMedicines.length > 0) {
       handleSelectMedicineInfo(filteredMedicines[0], isReport)
    } else {
       const customMed = { 
         id: Math.random().toString(), 
         name: searchMed, 
         desc: 'Custom prescription', 
         stock: 100, 
         type: 'ok', 
         unit: 'units (L1)' 
       }
       handleSelectMedicineInfo(customMed, isReport)
    }
  }

  const handleRemoveMedicine = (medId, isReport = false) => {
    const currentId = isReport ? selectedReportId : selectedId;
    setPrescriptions(prev => {
      const current = prev[currentId] || []
      return { ...prev, [currentId]: current.filter(m => m.id !== medId) }
    })
  }

  const patientPrescriptions = prescriptions[selectedId] || []
  const hasLowStock = patientPrescriptions.some(m => m.type === 'low')

  const handleApprove = async () => {
    if (patientPrescriptions.length === 0) {
      addToast('Cannot approve without prescribing medicines.', 'error')
      return
    }

    try {
      const { error } = await supabase
        .from('tickets')
        .update({ status: 'approved' })
        .eq('id', selectedId);
        
      if (error) throw error;

      // Create an order record
      const { error: orderError } = await supabase
        .from('orders')
        .insert({
          id: crypto.randomUUID(),
          ticket_id: selectedId,
          payment_method: 'Cash',
          total_bill: Math.floor(Math.random() * 500) + 50 // random bill between 50-550
        });
        
      if (orderError) console.error("Failed to create order record:", orderError);

      addToast(`${patient.name}'s ticket approved and dispatched.`, 'success')
      
      setPrescriptions(prev => {
        const copy = { ...prev }
        delete copy[selectedId]
        return copy
      })
      setSearchMed('')
      setShowSearchDropdown(false)
      setSelectedCamp("")

      const newPatients = patients.filter(p => p.id !== selectedId)
      setPatients(newPatients)
      
      if (newPatients.length > 0) {
        setSelectedId(newPatients[0].id)
      } else {
        setSelectedId(null)
      }
    } catch (err) {
      console.error(err);
      addToast('Failed to approve ticket.', 'error')
    }
  }

  const handleApproveReport = async () => {
    const reportPrescriptions = prescriptions[selectedReportId] || []
    if (reportPrescriptions.length === 0) {
      addToast('Cannot approve without prescribing medicines.', 'error')
      return
    }

    try {
      const { error } = await supabase
        .from('tickets')
        .update({ status: 'approved' })
        .eq('id', selectedReportId);

      if (error) throw error;
      
      const { error: orderError } = await supabase
        .from('orders')
        .insert({
          id: crypto.randomUUID(),
          ticket_id: selectedReportId,
          payment_method: 'Cash',
          total_bill: Math.floor(Math.random() * 500) + 50
        });
        
      if (orderError) console.error("Failed to create order record:", orderError);

      addToast(`${report.name}'s report approved and dispatched.`, 'success')
      
      setPrescriptions(prev => {
        const copy = { ...prev }
        delete copy[selectedReportId]
        return copy
      })
      setSearchMed('')
      setShowSearchDropdown(false)
      setSelectedReportCamp("")

      const newReports = traineeReports.filter(p => p.id !== selectedReportId)
      setTraineeReports(newReports)
      
      if (newReports.length > 0) {
        setSelectedReportId(newReports[0].id)
      } else {
        setSelectedReportId(null)
      }
    } catch (err) {
      console.error(err);
      addToast('Failed to approve report.', 'error')
    }
  }

  return (
    <div className="doc-layout" style={{ flexDirection: 'column' }}>
      {/* TOPBAR */}
      <header className="doc-topbar">
        <div className="topbar-brand">Phygital Telemedicine - Doctor Dashboard</div>
      </header>

      <div className="doc-main-container">
        {/* SIDEBAR */}
        <aside className="doc-sidebar">
          <div className="nav-section">
            <div 
              className={`nav-item ${activeTab === 'patients' ? 'active' : ''}`}
              onClick={() => setActiveTab('patients')}
            >
              <span>✆ General Patients</span>
              <span className="nav-badge">{patients.length}</span>
            </div>
            <div 
              className={`nav-item ${activeTab === 'trainee-reports' ? 'active' : ''}`}
              onClick={() => setActiveTab('trainee-reports')}
            >
              <span>📄 Trainee Reports</span>
              <span className="nav-badge blue">{traineeReports.length}</span>
            </div>
            <div 
              className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              <span>⚙ Settings</span>
            </div>
          </div>

          <div className="nav-section">
            <div className="nav-label">EPIDEMIC TRACKING</div>
            <div 
              className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveTab('analytics')}
            >
              <span>📊 Analytics</span>
            </div>
          </div>

          <div className="sidebar-bottom">
            <div className="profile-card">
              <div className="avatar">👤</div>
              <div className="profile-info">
                <span className="profile-name">Dr. Sharma</span>
                <span className="profile-role">Physician</span>
              </div>
            </div>
            <div className="status-row">
              <span>Status</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className="toggle-switch" onClick={() => setIsOnline(!isOnline)} style={{ cursor: 'pointer', background: isOnline ? 'var(--primary)' : 'var(--muted)' }}>
                  <div className="toggle-knob" style={{ transform: isOnline ? 'translateX(0)' : 'translateX(-16px)', left: isOnline ? 'auto' : '2px', right: isOnline ? '2px' : 'auto' }}></div>
                </div>
                <span style={{ color: isOnline ? '#10b981' : '#9ca3af' }}>{isOnline ? 'Online' : 'Offline'}</span>
              </div>
            </div>
            <div className="emergencies" onClick={() => setShowEmergencyModal(true)} style={{ cursor: 'pointer', padding: '8px', margin: '-8px', borderRadius: '8px', transition: 'background 0.2s' }}>
              <span>Emergencies</span>
              <span className="alert-badge">{emergencies.length}</span>
            </div>
            <button className="exit-btn" onClick={() => navigate('/')}>
              Exit Dashboard
            </button>
          </div>
        </aside>

        {activeTab === 'patients' ? (
        <>
        {/* PATIENT LIST */}
        <div className="doc-list">
          {outbreaks.length > 0 && (
            <div style={{ backgroundColor: '#fee2e2', color: '#dc2626', padding: '12px', marginBottom: '16px', borderRadius: '8px', fontWeight: 'bold', display: 'flex', gap: '8px', alignItems: 'center', border: '1px solid #fca5a5' }}>
              <span>⚠️</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {outbreaks.map((ob, i) => <span key={i}>{ob.message}</span>)}
              </div>
            </div>
          )}
          <div className="list-header">
            <h2 className="list-title">General Patients</h2>
            <div className="list-subtitle">{patients.length} pending AI tickets</div>
          </div>
          
          <div className="patient-scroll">
            {patients.length === 0 ? (
               <div style={{ textAlign: 'center', padding: '40px 20px', color: '#6b7280' }}>
                 No pending tickets. Great job!
               </div>
            ) : (
              patients.map(p => (
                <div 
                  key={p.id} 
                  className={`patient-card ${selectedId === p.id ? 'active' : ''}`}
                  onClick={() => setSelectedId(p.id)}
                >
                  <div className="pc-head">
                    <span className="pc-name">{p.name}</span>
                    <span className={`severity-chip ${p.severity.toLowerCase()}`}>{p.severity}</span>
                  </div>
                  <div className="pc-meta">{p.age}y, {p.gender} <br/> {p.village}</div>
                  <div className="pc-time">⏱ {p.timeAgo}</div>
                  <div className="pc-symptoms">{p.symptoms.join('. ')}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* PATIENT DETAILS */}
        <main className="doc-details">
          {patient ? (
            <div className="details-inner">
              {/* Info Card */}
              <div className="panel-card">
                <div className="panel-title">👤 Patient Information</div>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Name</span>
                    <span className="info-value">{patient.name}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Age / Gender</span>
                    <span className="info-value">{patient.age}y, {patient.gender}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Village</span>
                    <span className="info-value">{patient.village}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Contact</span>
                    <span className="info-value">{patient.phone}</span>
                  </div>
                </div>
                <div className="info-banner">
                  📅 Previous Visits: {patient.previousVisits}
                </div>
              </div>

              {/* Physical Vitals (if Trainee submitted them) */}
              {patient.rawTicket?.vitals_data && Object.keys(patient.rawTicket.vitals_data).length > 0 && (
                <div className="panel-card" style={{ borderColor: '#3b82f6', borderWidth: '2px' }}>
                  <div className="panel-title" style={{ color: '#2563eb' }}>🩺 Physical Vitals (Recorded by Trainee)</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginTop: '12px' }}>
                    {Object.entries(patient.rawTicket.vitals_data).map(([key, val]) => (
                       <div key={key} style={{ background: '#eff6ff', padding: '8px 12px', borderRadius: '8px' }}>
                          <div style={{ fontSize: '11px', color: '#60a5fa', textTransform: 'uppercase', fontWeight: 600 }}>{key}</div>
                          <div style={{ fontSize: '15px', color: '#1e3a8a', fontWeight: 500 }}>{val}</div>
                       </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Summary Card */}
              <div className="panel-card">
                <div className="panel-title">AI-Generated Medical Summary</div>
                <div className="ai-summary">{patient.aiSummary}</div>
                
                {patient.rawTicket?.extracted_symptoms?.advanced_diagnosis && (
                  <div style={{ marginTop: '16px', padding: '12px', background: '#f8fafc', borderRadius: '8px', borderLeft: '4px solid #8b5cf6' }}>
                    <div style={{ fontSize: '12px', color: '#7c3aed', fontWeight: 600, marginBottom: '4px' }}>✨ ADVANCED AI DIAGNOSIS</div>
                    <div style={{ color: '#334155', fontSize: '14px', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{patient.rawTicket.extracted_symptoms.advanced_diagnosis}</div>
                  </div>
                )}
                
                <div className="symptoms-title">Reported Symptoms:</div>
                <div className="symptoms-row">
                  {patient.symptoms.map((s, i) => (
                    <span key={i} className="symptom-tag">{s}</span>
                  ))}
                </div>
              </div>

              {/* Prescription Card */}
            <div className="panel-card" style={{ zIndex: 10 }}>
              <div className="panel-title">
                <span>Prescription</span>
              </div>
              
              <div className="search-wrapper">
                <form onSubmit={handleAddMedicine}>
                  <input 
                    type="text" 
                    className="med-search" 
                    placeholder="Search L1/L2 inventory... (Type to filter)"
                    value={searchMed}
                    onChange={e => {
                      setSearchMed(e.target.value)
                      setShowSearchDropdown(true)
                    }}
                    onFocus={() => setShowSearchDropdown(true)}
                    onBlur={() => setTimeout(() => setShowSearchDropdown(false), 200)}
                  />
                </form>

                {showSearchDropdown && (
                  <div className="search-dropdown">
                    {filteredMedicines.length === 0 ? (
                      <div style={{ padding: '16px', color: 'var(--muted)', textAlign: 'center', fontSize: 13 }}>
                        No medicines found in inventory. Press Enter to add as custom.
                      </div>
                    ) : (
                      filteredMedicines.map(med => (
                        <div key={'search-' + med.id} className="search-item" onMouseDown={(e) => { e.preventDefault(); handleSelectMedicineInfo(med); }}>
                          <span className="si-name">{med.name}</span>
                          <div className="si-meta">
                            <span>{med.desc}</span>
                            <span className={`si-stock ${med.type}`}>Stock: {med.stock} {med.unit}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              <div className="prescribed-list">
                  {patientPrescriptions.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '20px', color: '#9ca3af', border: '1px dashed #e5e7eb', borderRadius: 12 }}>
                      No medicines prescribed yet.
                    </div>
                  ) : (
                    patientPrescriptions.map((med, index) => (
                      <div key={med.id + index} className="medicine-card">
                        <div className="med-info">
                          <span className="med-name">{med.name}</span>
                          <span className="med-desc">{med.desc}</span>
                          <span className={`med-stock ${med.type === 'low' ? 'red' : 'green'}`}>
                            Stock: {med.stock} {med.unit}
                          </span>
                        </div>
                        <button className="remove-btn" onClick={() => handleRemoveMedicine(med.id)}>×</button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Stock Availability */}
              <div className="panel-card">
                 <div className="panel-title">Stock Availability</div>
                 {hasLowStock ? (
                   <div className="warning-banner">
                     <div className="warning-icon">!</div>
                     <div>
                       <div className="warning-title">Low stock warning</div>
                       <div>Some prescribed medicines have limited quantities at L1/L2.</div>
                     </div>
                   </div>
                 ) : (
                   <div style={{ color: '#6b7280', fontSize: 14 }}>All prescribed medicines are sufficiently stocked.</div>
                 )}
              </div>

              {/* Specialist Escalation */}
              <div className="escalation-box">
                <div className="escalation-title">Specialist Camp Escalation</div>
                <div className="escalation-desc">Refer patient to upcoming specialist camps for advanced care</div>
                <select className="camp-select" value={selectedCamp} onChange={(e) => setSelectedCamp(e.target.value)}>
                  <option value="" disabled>Select a specialist camp...</option>
                  <option value="eye">Eye Care Camp (Sun, 1 Mar)</option>
                  <option value="diabetes">Diabetes Screening (Thu, 5 Mar)</option>
                  <option value="cardio">Cardiology Check-up (Sun, 8 Mar)</option>
                </select>
                <button className="camp-btn" onClick={() => {
                  if(!selectedCamp) {
                    addToast('Please select a specialist camp', 'error')
                    return
                  }
                  addToast('Patient assigned to Specialist Camp Pool')
                }}>
                  Send to Specialist Camp Pool
                </button>
              </div>

              {/* Actions */}
              <div className="action-bar">
                <button 
                  className="approve-btn"
                  onClick={handleApprove}
                  disabled={patientPrescriptions.length === 0}
                  title={patientPrescriptions.length === 0 ? "Prescribe at least one medicine to approve" : ""}
                >
                  Approve & Dispatch Order
                </button>
              </div>
              
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--muted)', fontSize: 18, fontWeight: 600 }}>
              Select a patient from the list to view details
            </div>
          )}
        </main>
        </>
        ) : activeTab === 'trainee-reports' ? (
        <>
        {/* TRAINEE REPORTS LIST */}
        <div className="doc-list">
          <div className="list-header">
            <h2 className="list-title">Trainee Reports</h2>
            <div className="list-subtitle">{traineeReports.length} vitals captured</div>
          </div>
          
          <div className="patient-scroll">
            {traineeReports.length === 0 ? (
               <div style={{ textAlign: 'center', padding: '40px 20px', color: '#6b7280' }}>
                 No trainee reports pending.
               </div>
            ) : (
              traineeReports.map(r => (
                <div 
                  key={r.id} 
                  className={`patient-card ${selectedReportId === r.id ? 'active' : ''}`}
                  onClick={() => setSelectedReportId(r.id)}
                >
                  <div className="pc-head">
                    <span className="pc-name">{r.name}</span>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      {r.isUrgent && <span className="severity-chip high">Urgent</span>}
                      <span className="severity-chip blue" style={{ background: 'var(--blue)', color: 'white' }}>~ Vitals</span>
                    </div>
                  </div>
                  <div className="pc-meta">{r.age}y, {r.gender} <br/> {r.village}</div>
                  <div className="pc-time" style={{ marginBottom: '12px' }}>⏱ {r.timeAgo}</div>
                  
                  <div style={{ fontSize: '13px', color: 'var(--text)', marginBottom: '4px' }}>
                    Trainee: {r.trainee}
                  </div>
                  {r.vitals && (r.vitals.sys || r.vitals.hr || r.vitals.spo2 || r.vitals.temp) ? (
                    <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                      BP: {r.vitals.sys || '-'}/{r.vitals.dia || '-'} | SpO2: {r.vitals.spo2 || '-'}%
                    </div>
                  ) : (
                    <div style={{ fontSize: '12px', color: 'var(--amber)' }}>
                      Vitals Pending
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* TRAINEE REPORT DETAILS */}
        <main className="doc-details">
          {report ? (
            <div className="details-inner">
              {/* Info Card */}
              <div className="panel-card">
                <div className="panel-title">👤 Patient Information</div>
                <div className="info-grid data-grid">
                  <div className="data-item">
                    <span className="data-label">Name</span>
                    <span className="data-val">{report.name}</span>
                  </div>
                  <div className="data-item">
                    <span className="data-label">Age / Gender</span>
                    <span className="data-val">{report.age}y, {report.gender}</span>
                  </div>
                  <div className="data-item">
                    <span className="data-label">Village</span>
                    <span className="data-val">{report.village}</span>
                  </div>
                  <div className="data-item">
                    <span className="data-label">Contact</span>
                    <span className="data-val">{report.phone}</span>
                  </div>
                </div>
                <div className="info-banner" style={{ marginTop: '20px' }}>
                  📅 Previous Visits: {report.previousVisits}
                </div>
              </div>

              {/* Field Vitals Report Card */}
              <div className="panel-card">
                <div className="panel-title">Field Vitals Report</div>
                <div style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '20px' }}>
                  Submitted by {report.trainee}
                </div>
                
                 {report.vitals && (report.vitals.sys || report.vitals.hr || report.vitals.spo2 || report.vitals.temp) ? (
                  <div className="data-grid" style={{ marginBottom: '24px' }}>
                     <div className="data-item">
                       <span className="data-label" style={{ color: 'var(--text)', textTransform: 'none' }}>~ Blood Pressure</span>
                       <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                         <span style={{ fontSize: '24px', fontWeight: 800 }}>{report.vitals.sys || '-'}/{report.vitals.dia || '-'}</span>
                         <span style={{ fontSize: '12px', color: 'var(--muted)' }}>mmHg</span>
                       </div>
                     </div>
                     <div className="data-item">
                       <span className="data-label" style={{ color: 'var(--red)', textTransform: 'none' }}>♡ Heart Rate</span>
                       <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                         <span style={{ fontSize: '24px', fontWeight: 800 }}>{report.vitals.hr || '-'}</span>
                         <span style={{ fontSize: '12px', color: 'var(--muted)' }}>bpm</span>
                       </div>
                     </div>
                     <div className="data-item">
                       <span className="data-label" style={{ color: 'var(--blue)', textTransform: 'none' }}>○ Oxygen Saturation</span>
                       <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                         <span style={{ fontSize: '24px', fontWeight: 800 }}>{report.vitals.spo2 || '-'}</span>
                         <span style={{ fontSize: '12px', color: 'var(--muted)' }}>%</span>
                       </div>
                     </div>
                     <div className="data-item">
                       <span className="data-label" style={{ color: 'var(--amber)', textTransform: 'none' }}>🌡 Temperature</span>
                       <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                         <span style={{ fontSize: '24px', fontWeight: 800 }}>{report.vitals.temp || '-'}</span>
                         <span style={{ fontSize: '12px', color: 'var(--muted)' }}>°F</span>
                       </div>
                     </div>
                  </div>
                 ) : (
                   <div style={{ padding: '20px', background: '#fef3c7', color: '#92400e', borderRadius: '8px', marginBottom: '24px' }}>
                     Patient vitals not yet recorded by trainee.
                   </div>
                 )}

                <div className="section-subtitle">Physical Notes:</div>
                <div className="detail-text">{report.physicalNotes}</div>

                <div className="section-subtitle">Symptoms Summary:</div>
                <div className="detail-text" style={{ marginBottom: 0 }}>{report.symptomsSummary}</div>
              </div>

              {/* Prescription Card */}
              <div className="panel-card" style={{ zIndex: 10 }}>
                <div className="panel-title">
                  <span>Prescription</span>
                </div>
                
                <div className="search-wrapper">
                  <form onSubmit={(e) => handleAddMedicine(e, true)}>
                    <input 
                      type="text" 
                      className="med-search" 
                      placeholder="Search L1/L2 inventory... (Type to filter)"
                      value={searchMed}
                      onChange={e => {
                        setSearchMed(e.target.value)
                        setShowSearchDropdown(true)
                      }}
                      onFocus={() => setShowSearchDropdown(true)}
                      onBlur={() => setTimeout(() => setShowSearchDropdown(false), 200)}
                    />
                  </form>

                  {showSearchDropdown && (
                    <div className="search-dropdown">
                      {filteredMedicines.length === 0 ? (
                        <div style={{ padding: '16px', color: 'var(--muted)', textAlign: 'center', fontSize: 13 }}>
                          No medicines found in inventory. Press Enter to add as custom.
                        </div>
                      ) : (
                        filteredMedicines.map(med => (
                          <div key={'search-' + med.id} className="search-item" onMouseDown={(e) => { e.preventDefault(); handleSelectMedicineInfo(med, true); }}>
                            <span className="si-name">{med.name}</span>
                            <div className="si-meta">
                              <span>{med.desc}</span>
                              <span className={`si-stock ${med.type}`}>Stock: {med.stock} {med.unit}</span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>

                <div className="prescribed-list">
                    {(prescriptions[selectedReportId] || []).length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '20px', color: '#9ca3af', border: '1px dashed var(--border)', borderRadius: 12 }}>
                        No medicines prescribed yet.
                      </div>
                    ) : (
                      (prescriptions[selectedReportId] || []).map((med, index) => (
                        <div key={med.id + index} className="medicine-card">
                          <div className="med-info">
                            <span className="med-name">{med.name}</span>
                            <span className="med-desc">{med.desc}</span>
                            <span className={`med-stock ${med.type === 'low' ? 'red' : 'green'}`}>
                              Stock: {med.stock} {med.unit}
                            </span>
                          </div>
                          <button className="remove-btn" onClick={() => handleRemoveMedicine(med.id, true)}>×</button>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Stock Availability */}
                <div className="panel-card">
                   <div className="panel-title">Stock Availability</div>
                   {(prescriptions[selectedReportId] || []).some(m => m.type === 'low') ? (
                     <div className="warning-banner">
                       <div className="warning-icon">!</div>
                       <div>
                         <div className="warning-title">Low stock warning</div>
                         <div>Some prescribed medicines have limited quantities at L1/L2.</div>
                       </div>
                     </div>
                   ) : (
                     <div style={{ color: '#6b7280', fontSize: 14 }}>All prescribed medicines are sufficiently stocked.</div>
                   )}
                </div>

                {/* Specialist Escalation */}
                <div className="escalation-box">
                  <div className="escalation-title">Specialist Camp Escalation</div>
                  <div className="escalation-desc">Refer patient to upcoming specialist camps for advanced care</div>
                  <select className="camp-select" value={selectedReportCamp} onChange={(e) => setSelectedReportCamp(e.target.value)}>
                    <option value="" disabled>Select a specialist camp...</option>
                    <option value="eye">Eye Care Camp (Sun, 1 Mar)</option>
                    <option value="diabetes">Diabetes Screening (Thu, 5 Mar)</option>
                    <option value="cardio">Cardiology Check-up (Sun, 8 Mar)</option>
                  </select>
                  <button className="camp-btn" onClick={() => {
                    if(!selectedReportCamp) {
                      addToast('Please select a specialist camp', 'error')
                      return
                    }
                    addToast('Patient assigned to Specialist Camp Pool')
                  }}>
                    Send to Specialist Camp Pool
                  </button>
                </div>

                {/* Actions */}
                <div className="action-bar">
                  <button 
                    className="approve-btn"
                    onClick={handleApproveReport}
                    disabled={(prescriptions[selectedReportId] || []).length === 0}
                    title={(prescriptions[selectedReportId] || []).length === 0 ? "Prescribe at least one medicine to approve" : ""}
                  >
                    Approve & Dispatch Order
                  </button>
                </div>
            </div>
          ) : null}
        </main>
        </>
        ) : activeTab === 'analytics' ? (
          /* ANALYTICS VIEW */
          <main className="doc-details" style={{ alignItems: 'flex-start' }}>
            <div className="settings-container" style={{ width: '100%', maxWidth: '1000px' }}>
               <h2 style={{ fontSize: 24, fontWeight: 800, margin: '0 0 24px 0', color: 'var(--text)' }}>Epidemic Analytics & Outbreaks</h2>
               
               {outbreaks.length === 0 ? (
                 <div style={{ textAlign: 'center', padding: '40px', color: 'var(--muted)', background: 'var(--surface-light)', borderRadius: '12px' }}>
                    No significant outbreaks detected in the last 4 days.
                 </div>
               ) : (
                 <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                   {outbreaks.map((outbreak, idx) => (
                     <div key={idx} style={{ background: 'var(--surface-light)', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #ef4444' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <h3 style={{ margin: 0, fontSize: '18px', color: 'var(--text)' }}>{outbreak.symptom.charAt(0).toUpperCase() + outbreak.symptom.slice(1)} Outbreak</h3>
                          <span style={{ background: '#fef2f2', color: '#ef4444', padding: '4px 12px', borderRadius: '20px', fontSize: '14px', fontWeight: 'bold' }}>
                            {outbreak.count} Cases
                          </span>
                        </div>
                        <p style={{ margin: '0 0 8px 0', color: 'var(--muted)' }}>Detected across <strong>{outbreak.villages.length}</strong> villages:</p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {outbreak.villages.map((v, i) => (
                            <span key={i} style={{ background: 'var(--border)', padding: '4px 10px', borderRadius: '6px', fontSize: '13px' }}>{v}</span>
                          ))}
                        </div>
                     </div>
                   ))}
                 </div>
               )}
            </div>
          </main>
        ) : (
          /* SETTINGS VIEW */
          <main className="doc-details" style={{ alignItems: 'center' }}>
            <div className="settings-container" style={{ width: '100%' }}>
               <h2 style={{ fontSize: 24, fontWeight: 800, margin: 0, color: 'var(--text)' }}>Settings</h2>
               
               <div className="settings-group">
                 <div className="setting-item">
                   <div className="si-content">
                     <span className="si-title">Dark Mode Theme</span>
                     <span className="si-desc">Switch interface to a low-light dark aesthetic</span>
                   </div>
                   <div 
                     className="theme-toggle-pad" 
                     onClick={() => setIsDarkMode(!isDarkMode)}
                   >
                     <div className={`theme-slider ${isDarkMode ? 'right' : ''}`}>
                       {isDarkMode ? '🌙' : '☀️'}
                     </div>
                   </div>
                 </div>

                 <div className="setting-item">
                   <div className="si-content">
                     <span className="si-title">Availability Status</span>
                     <span className="si-desc">Toggle your availability for Trainee escalations</span>
                   </div>
                   <div className="toggle-switch" onClick={() => setIsOnline(!isOnline)} style={{ cursor: 'pointer', background: isOnline ? 'var(--primary)' : 'var(--muted)', width: 48, height: 28, borderRadius: 14 }}>
                     <div className="toggle-knob" style={{ width: 22, height: 22, top: 3, transform: isOnline ? 'translateX(0)' : 'translateX(-20px)', left: isOnline ? 'auto' : '3px', right: isOnline ? '3px' : 'auto' }}></div>
                   </div>
                 </div>

                 <div className="setting-item">
                   <div className="si-content">
                     <span className="si-title">Notification Sounds</span>
                     <span className="si-desc">Play a sound for incoming urgent medical tickets</span>
                   </div>
                   <button className="add-med-btn" style={{ padding: '8px 16px' }}>Config</button>
                 </div>
               </div>

            </div>
          </main>
        )}
      </div>

      {/* EMERGENCY MODAL */}
      {showEmergencyModal && (
        <div className="emergency-overlay">
          <div className="emergency-modal">
            <header className="emergency-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '22px' }}>⚠️</span>
                <span>EMERGENCY: High Severity Patient</span>
              </div>
              <button className="close-btn" onClick={() => setShowEmergencyModal(false)}>✕</button>
            </header>

            <div className="emergency-body" style={{ padding: '24px 12px 24px 32px' }}>
              {emergencies.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', maxHeight: '65vh', overflowY: 'auto', paddingRight: '20px' }} className="patient-scroll">
                  {emergencies.map((em, index) => (
                    <div key={em.id} style={{ borderBottom: index < emergencies.length - 1 ? '1px solid var(--border)' : 'none', paddingBottom: index < emergencies.length - 1 ? '32px' : '0' }}>
                      <div className="patient-critical-info">
                        <div className="critical-name">{em.name}</div>
                        <div className="critical-details">
                          Age: {em.age} | Gender: {em.gender} | Village: {em.village} <br/>
                          Contact: {em.phone}
                        </div>
                      </div>

                      <div className="critical-symptoms-wrapper" style={{ marginTop: '16px' }}>
                        <div className="critical-label">Critical Symptoms:</div>
                        <div className="symptoms-red-row">
                          {em.symptoms.map((s, i) => (
                            <span key={i} className="symptom-pill-red">{s}</span>
                          ))}
                        </div>
                      </div>

                      <div className="action-row" style={{ marginTop: '20px' }}>
                        <button
                          className="emergency-action-btn"
                          onClick={() => {
                            addToast(`Callback Initiated for ${em.name}`)
                            setShowEmergencyModal(false)
                          }}
                        >
                          <span style={{ fontSize: '18px' }}>📞</span> Initiate Emergency Callback Now
                        </button>
                        <div className="emergency-footer" style={{ marginTop: '12px' }}>
                          This patient requires immediate attention. Click above to start a priority call.
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--muted)', padding: '32px' }}>No active emergencies.</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Toasts */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`doc-toast ${t.type}`}>
            {t.type === 'success' ? '✓' : '⚠'} {t.message}
          </div>
        ))}
      </div>
    </div>
  )
}
