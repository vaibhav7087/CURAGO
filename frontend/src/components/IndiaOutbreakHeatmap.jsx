import React, { useState, useMemo } from 'react';

// Geo coordinates & surveillance data mapped to Curago project centers
const DEFAULT_CENTERS = [
  {
    id: 'dharampur',
    village: 'Dharampur',
    state: 'Gujarat / Border Hub',
    lat: 20.54,
    lng: 73.18,
    x: 144,
    y: 378,
    cases: 8,
    baseline: 2.3,
    zScore: 4.96,
    alertLevel: 'Critical',
    disease: 'Dengue Fever',
    symptoms: 'High Fever, Thrombocytopenia, Joint Pain, Rash',
    trend: '+248% Spike vs 4-wk Baseline',
    actionRequired: 'Emergency Vector Fumigation & IV/Paracetamol Dispatch',
    activeCluster: true,
    radius: 38
  },
  {
    id: 'rampur',
    village: 'Rampur',
    state: 'Uttar Pradesh',
    lat: 28.80,
    lng: 79.02,
    x: 239,
    y: 218,
    cases: 5,
    baseline: 1.8,
    zScore: 3.56,
    alertLevel: 'High',
    disease: 'Viral Pyrexia / Flu',
    symptoms: 'Fever, Severe Headache, Myalgia',
    trend: '+178% Spike vs Baseline',
    actionRequired: 'Mobile Diagnostic Kit & Antipyretic Supply',
    activeCluster: true,
    radius: 28
  },
  {
    id: 'sitapur',
    village: 'Sitapur',
    state: 'Uttar Pradesh',
    lat: 27.57,
    lng: 80.68,
    x: 267,
    y: 242,
    cases: 3,
    baseline: 1.5,
    zScore: 2.10,
    alertLevel: 'Moderate',
    disease: 'Gastroenteritis',
    symptoms: 'Dehydration, Abdominal Pain, Acute Diarrhea',
    trend: '+45% vs Baseline',
    actionRequired: 'ORS Packets Distribution & Clean Water Advisory',
    activeCluster: false,
    radius: 18
  },
  {
    id: 'madhopur',
    village: 'Madhopur',
    state: 'Bihar',
    lat: 26.15,
    lng: 85.35,
    x: 342,
    y: 270,
    cases: 3,
    baseline: 1.7,
    zScore: 1.82,
    alertLevel: 'Moderate',
    disease: 'Viral Fever',
    symptoms: 'Mild Fever, Cough',
    trend: '+30% vs Baseline',
    actionRequired: 'Routine Sub-center Monitoring',
    activeCluster: false,
    radius: 16
  },
  {
    id: 'palampur',
    village: 'Palampur',
    state: 'Himachal Pradesh',
    lat: 32.11,
    lng: 76.53,
    x: 199,
    y: 154,
    cases: 2,
    baseline: 1.4,
    zScore: 1.12,
    alertLevel: 'Normal',
    disease: 'Respiratory Infection',
    symptoms: 'Dry Cough, Cold',
    trend: 'Stable',
    actionRequired: 'Routine Care',
    activeCluster: false,
    radius: 12
  },
  {
    id: 'delhi',
    village: 'Vasant Kunj / Saket',
    state: 'Delhi NCR',
    lat: 28.52,
    lng: 77.15,
    x: 209,
    y: 224,
    cases: 2,
    baseline: 2.0,
    zScore: 0.85,
    alertLevel: 'Normal',
    disease: 'Allergic Rhinitis',
    symptoms: 'Sneezing, Congestion',
    trend: 'Normal Baseline',
    actionRequired: 'No Intervention Required',
    activeCluster: false,
    radius: 12
  },
  {
    id: 'lucknow',
    village: 'Gomti Nagar',
    state: 'Uttar Pradesh',
    lat: 26.85,
    lng: 81.00,
    x: 272,
    y: 256,
    cases: 2,
    baseline: 1.9,
    zScore: 1.20,
    alertLevel: 'Normal',
    disease: 'Viral Fever',
    symptoms: 'Low Grade Fever, Body Ache',
    trend: 'Normal Baseline',
    actionRequired: 'Routine Care',
    activeCluster: false,
    radius: 12
  },
  {
    id: 'mumbai',
    village: 'Andheri',
    state: 'Maharashtra',
    lat: 19.11,
    lng: 72.86,
    x: 139,
    y: 405,
    cases: 2,
    baseline: 2.1,
    zScore: 1.15,
    alertLevel: 'Normal',
    disease: 'Upper Respiratory',
    symptoms: 'Cough, Sore Throat',
    trend: 'Normal Baseline',
    actionRequired: 'Standard Pharmacy Supply',
    activeCluster: false,
    radius: 12
  },
  {
    id: 'pune',
    village: 'Kothrud',
    state: 'Maharashtra',
    lat: 18.50,
    lng: 73.81,
    x: 154,
    y: 417,
    cases: 2,
    baseline: 1.6,
    zScore: 1.45,
    alertLevel: 'Normal',
    disease: 'Seasonal Flu',
    symptoms: 'Fever, Fatigue',
    trend: 'Normal Baseline',
    actionRequired: 'Monitoring Active',
    activeCluster: false,
    radius: 12
  },
  {
    id: 'hyderabad',
    village: 'Banjara Hills',
    state: 'Telangana',
    lat: 17.41,
    lng: 78.44,
    x: 230,
    y: 438,
    cases: 1,
    baseline: 1.5,
    zScore: 0.65,
    alertLevel: 'Normal',
    disease: 'General Checkup',
    symptoms: 'Weakness',
    trend: 'Low Incidence',
    actionRequired: 'Routine Care',
    activeCluster: false,
    radius: 10
  },
  {
    id: 'bengaluru',
    village: 'Koramangala',
    state: 'Karnataka',
    lat: 12.93,
    lng: 77.62,
    x: 217,
    y: 525,
    cases: 1,
    baseline: 1.8,
    zScore: 0.54,
    alertLevel: 'Normal',
    disease: 'Migraine / Fatigue',
    symptoms: 'Headache',
    trend: 'Low Incidence',
    actionRequired: 'Routine Care',
    activeCluster: false,
    radius: 10
  },
  {
    id: 'kolkata',
    village: 'Salt Lake',
    state: 'West Bengal',
    lat: 22.58,
    lng: 88.42,
    x: 392,
    y: 338,
    cases: 2,
    baseline: 1.8,
    zScore: 1.10,
    alertLevel: 'Normal',
    disease: 'Gastroenteritis',
    symptoms: 'Mild Stomach Cramps',
    trend: 'Normal Baseline',
    actionRequired: 'Standard Monitoring',
    activeCluster: false,
    radius: 12
  }
];

export default function IndiaOutbreakHeatmap({ liveAlerts = [] }) {
  const [selectedCenter, setSelectedCenter] = useState(DEFAULT_CENTERS[0]); // Dharampur default
  const [filterMode, setFilterMode] = useState('all'); // 'all' | 'outbreak' | 'critical'
  const [viewMode, setViewMode] = useState('heat'); // 'heat' | 'radar'

  // Merge live backend alerts if present
  const centers = useMemo(() => {
    return DEFAULT_CENTERS.map(c => {
      const match = liveAlerts.find(a => 
        (a.village || '').toLowerCase() === c.village.toLowerCase() ||
        (a.region || '').toLowerCase() === c.village.toLowerCase()
      );
      if (match) {
        return {
          ...c,
          cases: match.current_week_cases || match.case_count || c.cases,
          zScore: match.z_score ? parseFloat(match.z_score) : c.zScore,
          alertLevel: match.alert_level || c.alertLevel,
          trend: match.message || c.trend
        };
      }
      return c;
    });
  }, [liveAlerts]);

  const filteredCenters = useMemo(() => {
    if (filterMode === 'critical') return centers.filter(c => c.alertLevel === 'Critical');
    if (filterMode === 'outbreak') return centers.filter(c => c.zScore >= 3.0);
    return centers;
  }, [centers, filterMode]);

  const activeOutbreaksCount = centers.filter(c => c.zScore >= 3.0).length;
  const criticalCount = centers.filter(c => c.alertLevel === 'Critical').length;

  return (
    <div style={{
      background: 'linear-gradient(145deg, #0a1128 0%, #101c3d 50%, #0d1527 100%)',
      borderRadius: '16px',
      border: '1px solid rgba(59, 130, 246, 0.25)',
      boxShadow: '0 12px 40px rgba(0, 0, 0, 0.45), 0 0 30px rgba(37, 99, 235, 0.1)',
      padding: '24px',
      color: '#ffffff',
      marginBottom: '28px',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Top Banner / HUD Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{
              display: 'inline-block',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: '#ef4444',
              boxShadow: '0 0 10px #ef4444',
              animation: 'pulseGlow 1.5s infinite'
            }} />
            <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 800, letterSpacing: '-0.02em', color: '#f8fafc' }}>
              🇮🇳 National Outbreak Surveillance & Geo-Heatmap
            </h3>
          </div>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#94a3b8' }}>
            Multi-center epidemiological anomaly detection via Z-Score rolling window & Isolation Forest
          </p>
        </div>

        {/* Status Badges */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            color: '#f87171'
          }}>
            ⚠️ {criticalCount} Critical Cluster ({centers[0]?.village})
          </div>
          <div style={{
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid rgba(245, 158, 11, 0.4)',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            color: '#fbbf24'
          }}>
            ⚡ {activeOutbreaksCount} Active Anomalies (z ≥ 3.0)
          </div>
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            color: '#34d399'
          }}>
            📡 12 Centers Monitored
          </div>
        </div>
      </div>

      {/* Control Bar: Filters & View Modes */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(15, 23, 42, 0.6)',
        padding: '10px 14px',
        borderRadius: '10px',
        marginBottom: '20px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {/* Filters */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8', marginRight: '6px', fontWeight: 600 }}>Filter:</span>
          {[
            { id: 'all', label: 'All Centers (12)' },
            { id: 'outbreak', label: 'Anomalies (z ≥ 3.0)' },
            { id: 'critical', label: 'Critical Only' }
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setFilterMode(f.id)}
              style={{
                background: filterMode === f.id ? '#2563eb' : 'rgba(255, 255, 255, 0.05)',
                color: filterMode === f.id ? '#ffffff' : '#94a3b8',
                border: '1px solid',
                borderColor: filterMode === f.id ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)',
                borderRadius: '6px',
                padding: '5px 12px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* View Mode Toggle */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8', marginRight: '6px', fontWeight: 600 }}>Visualizer:</span>
          <button
            onClick={() => setViewMode('heat')}
            style={{
              background: viewMode === 'heat' ? 'linear-gradient(135deg, #ef4444, #f59e0b)' : 'rgba(255, 255, 255, 0.05)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              padding: '5px 12px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            🔥 Thermal Heatmap
          </button>
          <button
            onClick={() => setViewMode('radar')}
            style={{
              background: viewMode === 'radar' ? '#0ea5e9' : 'rgba(255, 255, 255, 0.05)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              padding: '5px 12px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            🎯 Radar Vectors
          </button>
        </div>
      </div>

      {/* Main Grid: Map & Live Telemetry Panel */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(320px, 1.4fr) minmax(280px, 1fr)',
        gap: '20px',
        alignItems: 'stretch'
      }}>
        {/* Visual Map Container */}
        <div style={{
          background: 'radial-gradient(circle at 40% 45%, #132247 0%, #090e1f 100%)',
          borderRadius: '12px',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          padding: '16px',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '480px'
        }}>
          {/* Tactical Overlay Grid Lines */}
          <div style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `
              linear-gradient(to right, rgba(59, 130, 246, 0.05) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(59, 130, 246, 0.05) 1px, transparent 1px)
            `,
            backgroundSize: '24px 24px',
            pointerEvents: 'none',
            borderRadius: '12px'
          }} />

          {/* Geo Coordinates HUD Stamp */}
          <div style={{
            position: 'absolute',
            top: '12px',
            left: '14px',
            fontSize: '11px',
            fontFamily: 'monospace',
            color: '#64748b',
            pointerEvents: 'none'
          }}>
            GEODATA: WGS84 [68.0°E - 97.5°E, 7.5°N - 37.5°N]<br />
            PROJECTION: MERCATOR TACTICAL GRID
          </div>

          <div style={{
            position: 'absolute',
            bottom: '12px',
            left: '14px',
            fontSize: '11px',
            fontFamily: 'monospace',
            color: '#64748b',
            pointerEvents: 'none'
          }}>
            OUTBREAK DETECTOR: z-score &gt; 3.0 (p &lt; 0.001)
          </div>

          {/* SVG Map of India */}
          <svg
            viewBox="0 0 540 680"
            style={{ width: '100%', maxHeight: '460px', overflow: 'visible', filter: 'drop-shadow(0 4px 20px rgba(0,0,0,0.5))' }}
          >
            <defs>
              {/* Thermal Heatmap Glow Blur */}
              <filter id="heatBlur" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="18" />
              </filter>
              
              <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="5" />
              </filter>

              {/* Radial Gradients for Thermal Outbreak Epicenters */}
              <radialGradient id="dharampurHeat" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.85" />
                <stop offset="45%" stopColor="#f97316" stopOpacity="0.6" />
                <stop offset="75%" stopColor="#eab308" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
              </radialGradient>

              <radialGradient id="rampurHeat" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#eab308" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
              </radialGradient>

              <radialGradient id="generalHeat" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* Stylized India Landmass Outline */}
            <path
              d="
                M 174 64
                L 231 108
                L 210 150
                L 255 195
                L 320 272
                L 390 263
                L 434 286
                L 459 268
                L 524 224
                L 491 301
                L 451 330
                L 394 350
                L 353 388
                L 272 465
                L 252 562
                L 215 618
                L 190 582
                L 154 485
                L 138 407
                L 101 359
                L 68 321
                L 93 253
                L 190 166
                L 158 118
                Z
              "
              fill="rgba(30, 41, 59, 0.65)"
              stroke="rgba(96, 165, 250, 0.4)"
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeDasharray="none"
              style={{ filter: 'drop-shadow(0 0 10px rgba(59, 130, 246, 0.2))' }}
            />

            {/* Internal State / Regional Boundaries Accent Lines */}
            <g stroke="rgba(148, 163, 184, 0.18)" strokeWidth="1" strokeDasharray="3,3" fill="none">
              <path d="M 190 166 L 255 195 L 267 242 L 320 272" />
              <path d="M 101 359 L 144 378 L 230 438 L 272 465" />
              <path d="M 144 378 L 154 417 L 217 525 L 252 562" />
              <path d="M 239 218 L 272 256 L 342 270 L 392 338" />
              <path d="M 390 263 L 459 268 L 491 301" />
            </g>

            {/* THERMAL HEATMAP LAYER (Active when viewMode === 'heat') */}
            {viewMode === 'heat' && (
              <g filter="url(#heatBlur)">
                {/* Major Epidemic Thermal Blobs */}
                <circle cx="144" cy="378" r="75" fill="url(#dharampurHeat)" />
                <circle cx="239" cy="218" r="55" fill="url(#rampurHeat)" />
                <circle cx="267" cy="242" r="35" fill="url(#rampurHeat)" opacity="0.6" />
                <circle cx="342" cy="270" r="30" fill="url(#generalHeat)" />
                <circle cx="154" cy="417" r="30" fill="url(#generalHeat)" />
                <circle cx="217" cy="525" r="25" fill="url(#generalHeat)" />
                <circle cx="392" cy="338" r="25" fill="url(#generalHeat)" />
              </g>
            )}

            {/* RADAR SWEEP RINGS (For Outbreak Hotspots) */}
            {filteredCenters.filter(c => c.activeCluster).map(cluster => (
              <g key={`radar-${cluster.id}`}>
                <circle
                  cx={cluster.x}
                  cy={cluster.y}
                  r={cluster.radius}
                  fill="none"
                  stroke={cluster.alertLevel === 'Critical' ? '#ef4444' : '#f59e0b'}
                  strokeWidth="1.5"
                  opacity="0.8"
                >
                  <animate
                    attributeName="r"
                    values={`${cluster.radius}; ${cluster.radius + 28}`}
                    dur="2s"
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.9; 0"
                    dur="2s"
                    repeatCount="indefinite"
                  />
                </circle>
                <circle
                  cx={cluster.x}
                  cy={cluster.y}
                  r={cluster.radius * 0.7}
                  fill="none"
                  stroke={cluster.alertLevel === 'Critical' ? '#ef4444' : '#f59e0b'}
                  strokeWidth="1.5"
                  opacity="0.6"
                >
                  <animate
                    attributeName="r"
                    values={`${cluster.radius * 0.7}; ${cluster.radius + 14}`}
                    dur="2s"
                    begin="0.7s"
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.7; 0"
                    dur="2s"
                    begin="0.7s"
                    repeatCount="indefinite"
                  />
                </circle>
              </g>
            ))}

            {/* NODE MARKERS FOR CENTERS */}
            {filteredCenters.map(center => {
              const isSelected = selectedCenter?.id === center.id;
              const isCritical = center.alertLevel === 'Critical';
              const isHigh = center.alertLevel === 'High';
              const isMod = center.alertLevel === 'Moderate';

              const nodeColor = isCritical ? '#ef4444' : isHigh ? '#f59e0b' : isMod ? '#38bdf8' : '#10b981';

              return (
                <g
                  key={center.id}
                  onClick={() => setSelectedCenter(center)}
                  style={{ cursor: 'pointer', transition: 'transform 0.2s' }}
                >
                  {/* Selection Ring */}
                  {isSelected && (
                    <circle
                      cx={center.x}
                      cy={center.y}
                      r="16"
                      fill="none"
                      stroke="#ffffff"
                      strokeWidth="2"
                      strokeDasharray="4,2"
                    />
                  )}

                  {/* Core Node Circle */}
                  <circle
                    cx={center.x}
                    cy={center.y}
                    r={isCritical ? 9 : isHigh ? 7 : 5}
                    fill={nodeColor}
                    stroke="#ffffff"
                    strokeWidth={isSelected ? 2.5 : 1.5}
                    style={{
                      filter: isCritical || isHigh ? 'drop-shadow(0 0 8px ' + nodeColor + ')' : 'none'
                    }}
                  />

                  {/* Node Label */}
                  <text
                    x={center.x + 12}
                    y={center.y + 4}
                    fill={isSelected ? '#ffffff' : isCritical ? '#fca5a5' : '#cbd5e1'}
                    fontSize={isCritical ? '13px' : '11px'}
                    fontWeight={isCritical || isSelected ? '700' : '500'}
                    fontFamily="system-ui, -apple-system, sans-serif"
                    style={{
                      pointerEvents: 'none',
                      textShadow: '0 1px 4px rgba(0,0,0,0.9)'
                    }}
                  >
                    {center.village}
                    {isCritical && ' ⚠️ (8)'}
                    {isHigh && ' (5)'}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Interactive Legend in Map */}
          <div style={{
            position: 'absolute',
            bottom: '12px',
            right: '14px',
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            padding: '8px 12px',
            fontSize: '11px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444' }} />
              <span style={{ color: '#f87171', fontWeight: 600 }}>Critical (z &gt; 4.0)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b' }} />
              <span style={{ color: '#fbbf24', fontWeight: 600 }}>High Spike (z &gt; 3.0)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
              <span style={{ color: '#34d399' }}>Normal Baseline</span>
            </div>
          </div>
        </div>

        {/* Live Telemetry / Center Deep-Dive Card */}
        {selectedCenter && (
          <div style={{
            background: 'rgba(15, 23, 42, 0.75)',
            backdropFilter: 'blur(12px)',
            borderRadius: '12px',
            border: selectedCenter.alertLevel === 'Critical'
              ? '1px solid rgba(239, 68, 68, 0.4)'
              : selectedCenter.alertLevel === 'High'
                ? '1px solid rgba(245, 158, 11, 0.4)'
                : '1px solid rgba(59, 130, 246, 0.25)',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}>
            <div>
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8' }}>
                    {selectedCenter.state}
                  </div>
                  <h4 style={{ margin: '2px 0 0 0', fontSize: '20px', fontWeight: 800, color: '#f8fafc' }}>
                    📍 {selectedCenter.village}
                  </h4>
                </div>
                <span style={{
                  padding: '4px 10px',
                  borderRadius: '20px',
                  fontSize: '12px',
                  fontWeight: 700,
                  background: selectedCenter.alertLevel === 'Critical'
                    ? '#ef4444'
                    : selectedCenter.alertLevel === 'High'
                      ? '#f59e0b'
                      : '#10b981',
                  color: '#ffffff'
                }}>
                  {selectedCenter.alertLevel.toUpperCase()}
                </span>
              </div>

              {/* Anomaly Stat Matrix */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '10px',
                marginBottom: '16px'
              }}>
                <div style={{
                  background: 'rgba(255, 255, 255, 0.04)',
                  padding: '12px',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.05)'
                }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>Weekly Cases</div>
                  <div style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff', marginTop: '2px' }}>
                    {selectedCenter.cases}
                    <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 400, marginLeft: '6px' }}>
                      (avg {selectedCenter.baseline}/wk)
                    </span>
                  </div>
                </div>

                <div style={{
                  background: selectedCenter.zScore >= 3.0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(255, 255, 255, 0.04)',
                  padding: '12px',
                  borderRadius: '8px',
                  border: selectedCenter.zScore >= 3.0 ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(255, 255, 255, 0.05)'
                }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>DS Z-Score Anomaly</div>
                  <div style={{
                    fontSize: '24px',
                    fontWeight: 800,
                    color: selectedCenter.zScore >= 3.0 ? '#f87171' : '#38bdf8',
                    marginTop: '2px'
                  }}>
                    +{selectedCenter.zScore.toFixed(2)}σ
                  </div>
                </div>
              </div>

              {/* Clinical Breakdown */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Dominant Disease Vector:
                </div>
                <div style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  borderLeft: `4px solid ${selectedCenter.alertLevel === 'Critical' ? '#ef4444' : selectedCenter.alertLevel === 'High' ? '#f59e0b' : '#10b981'}`
                }}>
                  <div style={{ fontWeight: 700, fontSize: '14px', color: '#f1f5f9' }}>
                    {selectedCenter.disease}
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                    Identified Symptoms: {selectedCenter.symptoms}
                  </div>
                </div>
              </div>

              {/* Trend Note */}
              <div style={{
                background: 'rgba(30, 41, 59, 0.5)',
                padding: '10px 12px',
                borderRadius: '8px',
                marginBottom: '16px',
                fontSize: '12px'
              }}>
                <span style={{ color: '#94a3b8' }}>Surveillance Signal: </span>
                <span style={{ color: '#f8fafc', fontWeight: 600 }}>{selectedCenter.trend}</span>
              </div>
            </div>

            {/* Recommended Protocol Action Box */}
            <div style={{
              background: selectedCenter.alertLevel === 'Critical'
                ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(185, 28, 28, 0.3))'
                : 'rgba(255, 255, 255, 0.05)',
              border: selectedCenter.alertLevel === 'Critical' ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '12px'
            }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#fca5a5', textTransform: 'uppercase', marginBottom: '4px' }}>
                ⚡ Auto-Triggered Intervention:
              </div>
              <div style={{ fontSize: '12px', color: '#ffffff', fontWeight: 500 }}>
                {selectedCenter.actionRequired}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
