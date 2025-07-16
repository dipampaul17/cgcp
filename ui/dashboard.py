"""
Claude Governance Control Plane - Executive Dashboard
Aesthetic, real-time monitoring and policy management for Anthropic's RSP
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Optional
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Claude Governance Control Plane",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Enhanced Custom CSS for aesthetic excellence
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styling */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #0e2a4a 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Enhanced metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 
            0 8px 32px rgba(0,0,0,0.3),
            inset 0 1px 0 rgba(255,255,255,0.1);
        backdrop-filter: blur(20px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 
            0 16px 48px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(255,255,255,0.2);
        border-color: rgba(76, 175, 80, 0.3);
    }
    
    [data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #4CAF50, #2196F3, #9C27B0);
        opacity: 0.6;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
    }
    
    h1 { font-size: 2.5rem; font-weight: 700; }
    h2 { font-size: 2rem; }
    h3 { font-size: 1.5rem; }
    
    /* Enhanced buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        border: none;
        padding: 12px 28px;
        border-radius: 12px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(76, 175, 80, 0.4);
        background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1cypcdb {
        background: linear-gradient(180deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 52, 96, 0.95) 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Card components */
    .dashboard-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        backdrop-filter: blur(20px);
        box-shadow: 
            0 8px 32px rgba(0,0,0,0.3),
            inset 0 1px 0 rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover {
        border-color: rgba(76, 175, 80, 0.3);
        transform: translateY(-2px);
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 4px;
    }
    
    .status-online {
        background: rgba(76, 175, 80, 0.2);
        color: #4CAF50;
        border: 1px solid rgba(76, 175, 80, 0.3);
    }
    
    .status-offline {
        background: rgba(244, 67, 54, 0.2);
        color: #F44336;
        border: 1px solid rgba(244, 67, 54, 0.3);
    }
    
    .status-warning {
        background: rgba(255, 152, 0, 0.2);
        color: #FF9800;
        border: 1px solid rgba(255, 152, 0, 0.3);
    }
    
    /* Risk level badges */
    .risk-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .risk-critical {
        background: linear-gradient(135deg, #F44336, #D32F2F);
        color: white;
        box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);
    }
    
    .risk-high {
        background: linear-gradient(135deg, #FF9800, #F57C00);
        color: white;
        box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
    }
    
    .risk-medium {
        background: linear-gradient(135deg, #FFC107, #FF8F00);
        color: #1a1a1a;
        box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
    }
    
    .risk-low {
        background: linear-gradient(135deg, #4CAF50, #388E3C);
        color: white;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
    
    /* Data tables */
    .stDataFrame {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        overflow: hidden;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
    }
    
    /* Selectbox and inputs */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 8px;
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        border-radius: 4px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Loading spinner */
    .stSpinner {
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Caching for better performance
@st.cache_data(ttl=30)
def fetch_metrics() -> Optional[Dict]:
    """Fetch current metrics from API with caching"""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return None

@st.cache_data(ttl=60)
def fetch_hourly_stats(hours: int = 24) -> Optional[Dict]:
    """Fetch hourly statistics with caching"""
    try:
        response = requests.get(f"{API_BASE_URL}/hourly-stats", params={"hours": hours}, timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        return None

@st.cache_data(ttl=10)
def fetch_review_queue() -> Optional[Dict]:
    """Fetch events in review queue with caching"""
    try:
        response = requests.get(f"{API_BASE_URL}/review-queue", timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_thresholds() -> Optional[Dict]:
    """Fetch current risk thresholds with caching"""
    try:
        response = requests.get(f"{API_BASE_URL}/thresholds", timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        return None

def create_modern_gauge(value: float, title: str, color: str, max_val: float = 100) -> go.Figure:
    """Create a modern, aesthetic gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 18, 'color': '#ffffff', 'family': 'Inter'}},
        number={'font': {'size': 24, 'color': '#ffffff', 'family': 'Inter'}},
        gauge={
            'axis': {
                'range': [None, max_val],
                'tickwidth': 0,
                'tickcolor': "rgba(255,255,255,0.3)",
                'tickfont': {'size': 12, 'color': 'rgba(255,255,255,0.7)'}
            },
            'bar': {'color': color, 'thickness': 0.8},
            'bgcolor': "rgba(255,255,255,0.1)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, max_val*0.3], 'color': 'rgba(76, 175, 80, 0.1)'},
                {'range': [max_val*0.3, max_val*0.6], 'color': 'rgba(255, 193, 7, 0.1)'},
                {'range': [max_val*0.6, max_val*0.8], 'color': 'rgba(255, 152, 0, 0.1)'},
                {'range': [max_val*0.8, max_val], 'color': 'rgba(244, 67, 54, 0.1)'}
            ],
            'threshold': {
                'line': {'color': "#FF5252", 'width': 3},
                'thickness': 0.75,
                'value': max_val * 0.9
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "#ffffff", 'family': "Inter"},
        height=280,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    return fig

def create_time_series_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Create modern time series chart"""
    fig = go.Figure()
    
    # Add main trace with gradient fill
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Events'],
        name='Total Events',
        line=dict(color='#4CAF50', width=3),
        fill='tozeroy',
        fillcolor='rgba(76, 175, 80, 0.1)',
        hovertemplate='<b>%{y}</b> events<br>%{x}<extra></extra>'
    ))
    
    # Add secondary traces if they exist
    if 'Blocked' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Blocked'],
            name='Blocked',
            line=dict(color='#F44336', width=2),
            hovertemplate='<b>%{y}</b> blocked<br>%{x}<extra></extra>'
        ))
    
    if 'Escalated' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Escalated'],
            name='Escalated',
            line=dict(color='#FF9800', width=2),
            hovertemplate='<b>%{y}</b> escalated<br>%{x}<extra></extra>'
        ))
    
    fig.update_layout(
        template="plotly_dark",
        height=400,
        title=dict(text=title, font=dict(size=20, color='#ffffff', family='Inter')),
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.1)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        ),
        hovermode='x unified',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

def create_donut_chart(data: Dict, title: str, colors: List[str]) -> go.Figure:
    """Create modern donut chart"""
    if not data or sum(data.values()) == 0:
        # Create empty state
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            x=0.5, y=0.5,
            font=dict(size=16, color='rgba(255,255,255,0.6)'),
            showarrow=False
        )
    else:
        fig = go.Figure(data=[go.Pie(
            labels=list(data.keys()),
            values=list(data.values()),
            hole=0.6,
            marker=dict(
                colors=colors,
                line=dict(color='rgba(255,255,255,0.2)', width=2)
            ),
            textposition='outside',
            textinfo='label+percent',
            textfont=dict(size=14, color='#ffffff', family='Inter'),
            hovertemplate='<b>%{label}</b><br>%{value} events<br>%{percent}<extra></extra>'
        )])
        
        # Add center text
        fig.add_annotation(
            text=f"<b>{sum(data.values()):,}</b><br>Total",
            x=0.5, y=0.5,
            font=dict(size=18, color='#ffffff', family='Inter'),
            showarrow=False
        )
    
    fig.update_layout(
        template="plotly_dark",
        height=400,
        title=dict(text=title, font=dict(size=20, color='#ffffff', family='Inter')),
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

def check_api_health() -> bool:
    """Check API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

# Sidebar with modern design
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="font-size: 1.5rem; margin-bottom: 0.5rem;">🛡️ CGCP</h1>
        <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">Claude Governance Control Plane</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation with icons
    page = st.radio(
    "Navigation",
        [
            "🎯 Operations Dashboard",
            "🔍 Policy Review", 
            "📊 Analytics",
            "📜 Compliance"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # System status with modern indicators
    st.markdown("### System Status")
    
    api_healthy = check_api_health()
    if api_healthy:
        st.markdown('<div class="status-indicator status-online">✅ API Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator status-offline">❌ API Offline</div>', unsafe_allow_html=True)
    
    # Quick stats
    if api_healthy:
        metrics = fetch_metrics()
        if metrics:
            st.markdown("### Quick Stats")
            st.metric("Total Events", f"{metrics.get('total_events', 0):,}")
            st.metric("ASL Triggers", metrics.get('asl_triggers', 0))
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### Quick Actions")
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("📥 Export Report", use_container_width=True):
        st.toast("Generating compliance report...", icon="📊")

# Main content area
if page == "🎯 Operations Dashboard":
    st.markdown("# 🎯 Operations Dashboard")
    st.markdown("**Real-time monitoring of Claude safety governance systems**")
    
    # Check API connectivity
    if not check_api_health():
        st.error("🚫 **API Connection Failed** - Please ensure the backend is running at `http://localhost:8000`")
        st.code("python backend/app.py", language="bash")
        st.stop()
    
    # Fetch data
    metrics = fetch_metrics()
    if not metrics:
        st.warning("⚠️ Unable to fetch metrics. Retrying...")
        time.sleep(2)
        st.rerun()
    
    # Executive Summary Cards
    st.markdown("## 📊 Executive Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_events = metrics.get('total_events', 0)
    actions = metrics.get('actions_taken', {})
    blocked = actions.get('block', 0)
    escalated = actions.get('escalate', 0)
    asl_triggers = metrics.get('asl_triggers', 0)
    
    # Calculate rates
    block_rate = (blocked / max(total_events, 1)) * 100
    escalation_rate = (escalated / max(total_events, 1)) * 100
    compliance_rate = 100 - block_rate
    
    with col1:
        st.metric(
            label="📈 Total Events",
            value=f"{total_events:,}",
            delta="+2.1K from yesterday",
            help="Total events processed through the governance system"
        )
    
    with col2:
        st.metric(
            label="🛡️ Block Rate",
            value=f"{block_rate:.1f}%",
            delta=f"-0.2%" if block_rate < 1 else f"+{block_rate-1:.1f}%",
            delta_color="inverse",
            help="Percentage of events blocked for safety violations"
        )
    
    with col3:
        st.metric(
            label="⚡ Escalations",
            value=f"{escalated:,}",
            delta="+3 new",
            help="Events requiring human review"
        )
    
    with col4:
        st.metric(
            label="🚨 ASL-3 Triggers",
            value=f"{asl_triggers:,}",
            delta="Critical" if asl_triggers > 0 else "All Clear",
            delta_color="off" if asl_triggers == 0 else "normal",
            help="Anthropic Safety Level 3 threshold violations"
        )
    
    with col5:
        st.metric(
            label="✅ Compliance",
            value=f"{compliance_rate:.1f}%",
            delta="+0.3%",
            help="Overall system compliance rate"
        )
    
    st.markdown("---")
    
    # Risk Detection Overview
    st.markdown("## 🎯 Risk Detection Overview")
    
    risk_cols = st.columns(4)
    risk_data = metrics.get('risk_detections', {})
    
    risk_configs = [
        ("CBRN", risk_data.get('cbrn', 0), "#F44336", "Chemical, Biological, Radiological, Nuclear threats"),
        ("Self-Harm", risk_data.get('self_harm', 0), "#FF9800", "Self-harm and suicide-related content"),
        ("Jailbreak", risk_data.get('jailbreak', 0), "#FFC107", "Attempts to bypass safety measures"),
        ("Exploitation", risk_data.get('exploitation', 0), "#4CAF50", "Malicious use and exploitation attempts")
    ]
    
    for idx, (risk_type, count, color, description) in enumerate(risk_configs):
        with risk_cols[idx]:
            # Calculate percentage for gauge
            risk_percentage = min((count / max(total_events, 1)) * 1000, 100)  # Scale for visibility
            
            fig = create_modern_gauge(risk_percentage, risk_type, color)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"""
            <div class="dashboard-card" style="text-align: center; padding: 16px;">
                <h4 style="margin: 0; font-size: 1.2rem;">{count:,}</h4>
                <p style="margin: 4px 0 0 0; font-size: 0.8rem; opacity: 0.7;">{description}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Row
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.markdown("### 📈 Event Volume Trends (24h)")
        
        hourly_stats = fetch_hourly_stats()
        if hourly_stats and hourly_stats.get('hours'):
            df_hourly = pd.DataFrame({
                'Hour': pd.to_datetime(hourly_stats['hours']),
                'Events': hourly_stats['event_counts'],
                'Blocked': hourly_stats['blocked_counts'],
                'Escalated': hourly_stats['escalated_counts']
            }).set_index('Hour')
            
            fig = create_time_series_chart(df_hourly, "Event Processing Volume")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No hourly data available. Processing events...")
    
    with col_right:
        st.markdown("### 🎭 Traffic Distribution")
        
        surface_data = metrics.get('events_by_surface', {})
        colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
        
        if surface_data:
            fig = create_donut_chart(surface_data, "By Surface", colors)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No surface data available")
    
    # Recent High-Risk Events
    st.markdown("---")
    st.markdown("## 🚨 Recent High-Risk Events")
    
    review_queue = fetch_review_queue()
    if review_queue and review_queue.get('items'):
        for event in review_queue['items'][:3]:  # Show top 3
            with st.container():
                cols = st.columns([4, 2, 1])
                
                risk_scores = event.get('risk_scores', {})
                max_risk = max(risk_scores.values()) if risk_scores else 0
                
                # Risk level determination
                if max_risk > 0.8:
                    risk_level = "CRITICAL"
                    risk_class = "risk-critical"
                elif max_risk > 0.6:
                    risk_level = "HIGH"
                    risk_class = "risk-high"
                elif max_risk > 0.4:
                    risk_level = "MEDIUM"
                    risk_class = "risk-medium"
                else:
                    risk_level = "LOW"
                    risk_class = "risk-low"
                
                with cols[0]:
                    st.markdown(f"""
                    <div class="dashboard-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <strong>Event {event['event_id'][:8]}...</strong>
                            <span class="risk-badge {risk_class}">{risk_level}</span>
                        </div>
                        <p style="margin: 8px 0; font-size: 0.9rem; opacity: 0.8;">
                            <strong>User:</strong> {event['user_id']} | <strong>Org:</strong> {event['org_id']}
                        </p>
                        <p style="margin: 8px 0; font-size: 0.9rem;">
                            {event['prompt_preview'][:120]}...
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown("**Risk Breakdown**")
                    for category, score in risk_scores.items():
                        st.progress(score, text=f"{category.upper()}: {score:.2f}")
                
                with cols[2]:
                    if st.button("🔍 Review", key=f"review_{event['event_id']}", use_container_width=True):
                        st.session_state['selected_event'] = event['event_id']
                        st.switch_page("🔍 Policy Review")
    else:
        st.success("✅ **All Clear** - No high-risk events requiring immediate attention")

elif page == "🔍 Policy Review":
    st.markdown("# 🔍 Policy Review Queue")
    st.markdown("**Review and adjudicate escalated events requiring human oversight**")
    
    if not check_api_health():
        st.error("🚫 API Connection Failed")
        st.stop()
    
    review_queue = fetch_review_queue()
    if not review_queue:
        st.error("Unable to fetch review queue")
        st.stop()
    
    # Queue Overview
    st.markdown("## 📋 Queue Overview")
    
    col1, col2, col3, col4 = st.columns(4)
        
    with col1:
        st.metric("📥 Queue Size", review_queue.get('total', 0))
    with col2:
        st.metric("⏱️ Avg Wait Time", "2.3 hours")
    with col3:
        st.metric("🎯 SLA Compliance", "98.5%")
    with col4:
        st.metric("👥 Active Reviewers", "3")
    
    st.markdown("---")
    
    # Review Interface
    if review_queue.get('items'):
        st.markdown("## 🔍 Events Requiring Review")
        
        # Tabs for different priority levels
        high_priority = [e for e in review_queue['items'] if max(e.get('risk_scores', {}).values()) > 0.7]
        medium_priority = [e for e in review_queue['items'] if 0.4 <= max(e.get('risk_scores', {}).values()) <= 0.7]
        low_priority = [e for e in review_queue['items'] if max(e.get('risk_scores', {}).values()) < 0.4]
        
        tab1, tab2, tab3 = st.tabs([
            f"🚨 High Priority ({len(high_priority)})",
            f"⚠️ Medium Priority ({len(medium_priority)})", 
            f"📝 Low Priority ({len(low_priority)})"
        ])
        
        def render_review_events(events, tab_context):
            for idx, event in enumerate(events):
                with st.expander(
                    f"🎯 Event {event['event_id'][:8]}... - {event.get('reason', 'No reason provided')}",
                    expanded=idx == 0  # Expand first item
                ):
                    cols = st.columns([2, 1])
                    
                    with cols[0]:
                        # Event Details
                        st.markdown("#### 📋 Event Details")
                        
                        details_df = pd.DataFrame([
                            ["User ID", event['user_id']],
                            ["Organization", event['org_id']],
                            ["Surface", event['surface']],
                            ["Tier", event['tier']],
                            ["Timestamp", event['timestamp']]
                        ], columns=["Field", "Value"])
                        
                        st.dataframe(details_df, use_container_width=True)
                        
                        # Prompt Analysis
                        st.markdown("#### 📝 Prompt Content")
                        st.text_area(
                            "Full prompt text:",
                            value=event.get('prompt_preview', 'No prompt available'),
                            height=120,
                            disabled=True,
                            key=f"prompt_{event['event_id']}_{tab_context}"
                        )
                        
                        # Risk Visualization
                        st.markdown("#### 🎯 Risk Analysis")
                        risk_scores = event.get('risk_scores', {})
                        
                        if risk_scores:
                            risk_df = pd.DataFrame([
                                {"Category": k.upper(), "Score": v, "Status": "🚨 HIGH" if v > 0.7 else "⚠️ MEDIUM" if v > 0.4 else "✅ LOW"}
                                for k, v in risk_scores.items()
                            ])
                            
                            fig = px.bar(
                                risk_df, 
                                x='Category', 
                                y='Score',
                                color='Score',
                                color_continuous_scale='Reds',
                                title="Risk Score Breakdown"
                            )
                            fig.update_layout(
                                template="plotly_dark",
                                height=300,
                                showlegend=False
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with cols[1]:
                        # Review Decision Panel
                        st.markdown("#### ⚖️ Review Decision")
                        
                        # Decision options
                        decision = st.radio(
                            "Select Action:",
                            ["✅ Allow", "🚫 Block", "✂️ Redact"],
                            key=f"decision_{event['event_id']}_{tab_context}",
                            help="Choose the appropriate action for this event"
                        )
                        
                        # Policy update option
                        update_policy = st.checkbox(
                            "📋 Update Policy Threshold",
                            key=f"update_{event['event_id']}_{tab_context}",
                            help="Adjust thresholds based on this review"
                        )
                        
                        if update_policy:
                            category = st.selectbox(
                                "Risk Category:",
                                list(risk_scores.keys()),
                                key=f"cat_{event['event_id']}_{tab_context}"
                            )
                            
                            current_thresholds = fetch_thresholds()
                            if current_thresholds and category:
                                current_val = current_thresholds.get(category, {}).get(event['tier'], 0.5)
                                
                                new_threshold = st.slider(
                                    "New Threshold:",
                                    0.0, 1.0, 
                                    value=float(current_val),
                                    step=0.01,
                                    key=f"threshold_{event['event_id']}_{tab_context}"
                                )
                                
                                st.info(f"Current: {current_val:.2f} → New: {new_threshold:.2f}")
                        
                        # Review notes
                        review_notes = st.text_area(
                            "📝 Review Notes:",
                            placeholder="Add any notes about your decision...",
                            key=f"notes_{event['event_id']}_{tab_context}"
                        )
                        
                        # Submit button
                        if st.button(
                            "✅ Submit Decision", 
                            key=f"submit_{event['event_id']}_{tab_context}",
                            type="primary",
                            use_container_width=True
                        ):
                            # Prepare payload
                            payload = {
                                "decision": decision.split()[-1].lower(),  # Extract action word
                                "update_policy": update_policy,
                                "notes": review_notes
                            }
                            
                            if update_policy and 'category' in locals():
                                payload.update({
                                    "category": category,
                                    "new_threshold": new_threshold
                                })
                            
                            # Submit to API
                            try:
                                response = requests.post(
                                    f"{API_BASE_URL}/review/{event['event_id']}",
                                    json=payload,
                                    timeout=10
                                )
                                
                                if response.status_code == 200:
                                    st.success("✅ Decision submitted successfully!")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to submit: {response.text}")
                            except Exception as e:
                                st.error(f"❌ Submission error: {e}")
        
        with tab1:
            if high_priority:
                render_review_events(high_priority, "high")
            else:
                st.success("✅ No high-priority events in queue")
        
        with tab2:
            if medium_priority:
                render_review_events(medium_priority, "medium")
            else:
                st.info("📝 No medium-priority events in queue")
        
        with tab3:
            if low_priority:
                render_review_events(low_priority, "low")
            else:
                st.info("📝 No low-priority events in queue")
    
    else:
        st.success("🎉 **Review Queue Empty** - All events have been processed!")
        st.balloons()

elif page == "📊 Analytics":
    st.markdown("# 📊 Analytics & Insights")
    st.markdown("**Deep dive analysis of safety metrics and operational trends**")
    
    if not check_api_health():
        st.error("🚫 API Connection Failed")
        st.stop()
    
    # Time range selector
    col1, col2 = st.columns([1, 3])
    with col1:
        time_range = st.selectbox(
            "📅 Analysis Period:",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom Range"],
            help="Select the time period for analysis"
        )
    
    # Fetch data
    metrics = fetch_metrics()
    if not metrics:
        st.warning("⚠️ Unable to fetch analytics data")
        st.stop()
    
    st.markdown("---")
    
    # Key Performance Indicators
    st.markdown("## 🎯 Key Performance Indicators")
    
    kpi_cols = st.columns(6)
    
    total_events = metrics.get('total_events', 0)
    actions = metrics.get('actions_taken', {})
    risk_detections = metrics.get('risk_detections', {})
    
    with kpi_cols[0]:
        st.metric("📊 Processing Rate", "1.2K/hour", "+15%")
    with kpi_cols[1]:
        st.metric("🎯 Accuracy", "99.7%", "+0.1%")
    with kpi_cols[2]:
        st.metric("⚡ Response Time", "47ms", "-3ms")
    with kpi_cols[3]:
        st.metric("🛡️ Prevention Rate", "98.9%", "+0.5%")
    with kpi_cols[4]:
        st.metric("👥 False Positives", "0.3%", "-0.1%")
    with kpi_cols[5]:
        st.metric("🔄 Uptime", "99.99%", "0%")
                
    st.markdown("---")
                
    # Main Analytics Section
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Risk Analysis", 
        "📈 Trend Analysis", 
        "🏢 Organizational View",
        "🔍 Pattern Detection"
    ])
    
    with tab1:
        st.markdown("### 🎯 Risk Category Deep Dive")
        
        col1, col2 = st.columns(2)
        with col1:
            # Risk distribution treemap
            risk_data = []
            total_risks = sum(risk_detections.values())
            
            for category, count in risk_detections.items():
                if count > 0:
                    risk_data.append({
                        'Category': category.replace('_', ' ').title(),
                        'Detections': count,
                        'Percentage': (count / max(total_risks, 1)) * 100
                    })
            
            if risk_data:
                df_risk = pd.DataFrame(risk_data)
                
                # Enhanced treemap
                fig = px.treemap(
                    df_risk,
                    path=['Category'],
                    values='Detections',
                    color='Percentage',
                    color_continuous_scale='RdYlGn_r',
                    title="🗺️ Risk Detection Heatmap"
                )
                fig.update_layout(
                    template="plotly_dark",
                    height=400,
                    font=dict(family="Inter")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ **All Clear** - No significant risk detections")
                
        with col2:
            # Action distribution
            if actions and sum(actions.values()) > 0:
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(actions.keys()),
                        y=list(actions.values()),
                        marker=dict(
                            color=['#4CAF50', '#F44336', '#FF9800', '#2196F3'],
                            line=dict(color='rgba(255,255,255,0.2)', width=1)
                        ),
                        text=list(actions.values()),
                        textposition='auto'
                    )
                ])
                
                fig.update_layout(
                    template="plotly_dark",
                    height=400,
                    title="⚖️ Policy Actions Distribution",
                    xaxis_title="Action Type",
                    yaxis_title="Count",
                    font=dict(family="Inter")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No policy actions recorded yet")
        
        # Risk severity matrix
        st.markdown("### 🎯 Risk Severity Matrix")
        
        # Create mock data for demonstration
        severity_data = {
            'Risk Category': ['CBRN', 'Self-Harm', 'Jailbreak', 'Exploitation'],
            'Low (0.0-0.3)': [45, 23, 67, 34],
            'Medium (0.3-0.6)': [12, 8, 25, 15],
            'High (0.6-0.8)': [3, 2, 8, 4],
            'Critical (0.8-1.0)': [1, 0, 2, 1]
        }
        
        severity_df = pd.DataFrame(severity_data)
        st.dataframe(
            severity_df.set_index('Risk Category'),
            use_container_width=True
        )
    
    with tab2:
        st.markdown("### 📈 Trend Analysis")
        
        # Hourly trends
        hourly_stats = fetch_hourly_stats(hours=48)  # Extended for better trend analysis
        
        if hourly_stats and hourly_stats.get('hours'):
            df_hourly = pd.DataFrame({
                'Hour': pd.to_datetime(hourly_stats['hours']),
                'Events': hourly_stats['event_counts'],
                'Blocked': hourly_stats['blocked_counts'],
                'Escalated': hourly_stats['escalated_counts'],
                'ASL_Triggers': hourly_stats.get('asl_counts', [0] * len(hourly_stats['hours']))
            }).set_index('Hour')
            
            # Multi-line chart
            fig = go.Figure()
            
            metrics_to_plot = [
                ('Events', '#4CAF50', 'Total Events'),
                ('Blocked', '#F44336', 'Blocked Events'),
                ('Escalated', '#FF9800', 'Escalated Events'),
                ('ASL_Triggers', '#9C27B0', 'ASL-3 Triggers')
            ]
            
            for column, color, name in metrics_to_plot:
                fig.add_trace(go.Scatter(
                    x=df_hourly.index,
                    y=df_hourly[column],
                    name=name,
                    line=dict(color=color, width=2),
                    hovertemplate=f'<b>{name}</b><br>%{{y}}<br>%{{x}}<extra></extra>'
                ))
            
            fig.update_layout(
                template="plotly_dark",
                height=500,
                title="📈 48-Hour Trend Analysis",
                xaxis_title="Time",
                yaxis_title="Count",
                hovermode='x unified',
                font=dict(family="Inter")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Trend insights
            st.markdown("#### 🔍 Trend Insights")
            
            insight_cols = st.columns(3)
            
            with insight_cols[0]:
                avg_events = np.mean(df_hourly['Events'])
                st.metric("📊 Avg Events/Hour", f"{avg_events:.0f}")
            
            with insight_cols[1]:
                peak_hour = df_hourly['Events'].idxmax()
                st.metric("⏰ Peak Activity", peak_hour.strftime("%H:%M"))
            
            with insight_cols[2]:
                if len(df_hourly) >= 24:
                    trend_direction = "📈 Increasing" if df_hourly['Events'].iloc[-1] > df_hourly['Events'].iloc[-24] else "📉 Decreasing"
                else:
                    # If less than 24 hours of data, compare first and last
                    trend_direction = "📈 Increasing" if df_hourly['Events'].iloc[-1] > df_hourly['Events'].iloc[0] else "📉 Decreasing"
                st.metric("📊 24h Trend", trend_direction)
        
        else:
            st.info("📊 Insufficient data for trend analysis")
    
    with tab3:
        st.markdown("### 🏢 Organizational Analysis")
        
        # Tier distribution
        tier_data = metrics.get('events_by_tier', {})
        
        if tier_data:
            col1, col2 = st.columns(2)
            with col1:
                # Tier distribution pie chart
                fig = create_donut_chart(
                    tier_data,
                    "📊 Events by Tier",
                    ['#2196F3', '#4CAF50', '#FF9800']
                )
                st.plotly_chart(fig, use_container_width=True)
                    
            with col2:
                # Risk by tier analysis
                tier_risk_data = {
                    'Tier': list(tier_data.keys()),
                    'Events': list(tier_data.values()),
                    'Risk_Rate': [2.1, 5.8, 1.2]  # Mock risk rates
                }
                
                tier_df = pd.DataFrame(tier_risk_data)
                
                fig = px.scatter(
                    tier_df,
                    x='Events',
                    y='Risk_Rate',
                    size='Events',
                    color='Tier',
                    title="🎯 Risk Rate vs Volume by Tier",
                    labels={'Risk_Rate': 'Risk Detection Rate (%)', 'Events': 'Event Volume'}
                )
                
                fig.update_layout(
                    template="plotly_dark",
                    height=400,
                    font=dict(family="Inter")
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Organizational summary table
        st.markdown("#### 📋 Tier Performance Summary")
        
        summary_data = {
            'Tier': ['General', 'Enterprise', 'Research Sandbox'],
            'Total Events': [15420, 8930, 1250],
            'Block Rate (%)': [2.1, 0.8, 0.1],
            'Escalation Rate (%)': [0.5, 3.2, 8.5],
            'Avg Response Time (ms)': [45, 52, 38],
            'Compliance Score': ['98.9%', '99.2%', '99.9%']
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
    
    with tab4:
        st.markdown("### 🔍 Advanced Pattern Detection")
        
        # Anomaly detection simulation
        st.markdown("#### 🚨 Anomaly Detection")
        
        # Generate sample anomaly data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        normal_pattern = 100 + 20 * np.sin(np.arange(30) * 2 * np.pi / 7)  # Weekly pattern
        anomalies = normal_pattern.copy()
        anomalies[15] = 180  # Spike anomaly
        anomalies[22] = 45   # Drop anomaly
        
        fig = go.Figure()
        
        # Normal pattern
        fig.add_trace(go.Scatter(
            x=dates,
            y=normal_pattern,
            name='Expected Pattern',
            line=dict(color='#4CAF50', width=2, dash='dash')
        ))
        
        # Actual with anomalies
        fig.add_trace(go.Scatter(
            x=dates,
            y=anomalies,
            name='Actual Events',
            line=dict(color='#2196F3', width=3),
            fill='tonexty',
            fillcolor='rgba(33, 150, 243, 0.1)'
        ))
        
        # Highlight anomalies
        anomaly_dates = [dates[15], dates[22]]
        anomaly_values = [anomalies[15], anomalies[22]]
        
        fig.add_trace(go.Scatter(
            x=anomaly_dates,
            y=anomaly_values,
            mode='markers',
            name='Detected Anomalies',
            marker=dict(color='#F44336', size=12, symbol='diamond')
        ))
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
            title="🔍 Anomaly Detection - Event Volume",
            xaxis_title="Date",
            yaxis_title="Event Count",
            font=dict(family="Inter")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Pattern insights
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🎯 Detected Patterns")
            st.markdown("""
            - **Weekly Cycle**: Higher activity on weekdays
            - **Daily Peak**: 2-4 PM UTC consistent peak
            - **Anomaly Alert**: Unusual spike on Day 15
            - **Trend**: Overall stable with seasonal variation
            """)
    
        with col2:
            st.markdown("#### 🔧 Recommendations")
            st.markdown("""
            - **Scaling**: Consider auto-scaling during peak hours
            - **Monitoring**: Enhanced monitoring for detected anomaly pattern
            - **Capacity**: Current capacity sufficient for normal load
            - **Alerting**: Set threshold at 150% of baseline
            """)

elif page == "📜 Compliance":
    st.markdown("# 📜 Compliance & Audit")
    st.markdown("**Regulatory compliance reporting and audit evidence generation**")
    
    if not check_api_health():
        st.error("🚫 API Connection Failed")
        st.stop()
    
    # Compliance Overview Dashboard
    st.markdown("## 📋 Compliance Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🏛️ ISO 42001", "✅ Compliant", "100%")
    with col2:
        st.metric("🇺🇸 NIST AI RMF", "✅ Compliant", "100%")
    with col3:
        st.metric("🇪🇺 EU AI Act", "⚠️ Monitoring", "95%")
    with col4:
        st.metric("📊 SOC 2", "🔄 In Progress", "80%")
    with col5:
        st.metric("🛡️ Last Audit", "✅ Passed", "2 days ago")
    
    st.markdown("---")
    
    # Compliance Actions
    st.markdown("## 🎯 Compliance Actions")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("📥 Generate ISO 42001 Report", type="primary", use_container_width=True):
            with st.spinner("🔄 Generating comprehensive compliance report..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/export/iso-evidence", timeout=30)
                    
                    if response.status_code == 200:
                        report = response.json()
                        
                        st.success("✅ **Report Generated Successfully!**")
                        
                        # Enhanced Report Display
                        st.markdown("### 📊 Executive Summary")
                        
                        summary_cols = st.columns(4)
                        summary = report['summary']
                        
                        with summary_cols[0]:
                            st.metric("📅 Reporting Period", f"{report['period_days']} days")
                        with summary_cols[1]:
                            st.metric("📊 Events Analyzed", f"{summary['total_events']:,}")
                        with summary_cols[2]:
                            st.metric("🛡️ Blocked Events", f"{summary['blocked_events']:,}")
                        with summary_cols[3]:
                            st.metric("✅ Compliance Rate", summary['compliance_rate'])
                        
                        # Control Evidence Section
                        st.markdown("### 🎯 ISO 42001 Control Evidence")
                        
                        evidence_data = []
                        for control in report['controls']:
                            evidence_data.append({
                                'ISO Clause': control['iso_clause'],
                                'Control Name': control['control_name'],
                                'Evidence Count': control['evidence_count'],
                                'Sample Events': len(control['sample_events']),
                                'Status': '✅ Compliant' if control['compliance_status'] == 'compliant' else '⚠️ Attention Needed'
                            })
                        
                        evidence_df = pd.DataFrame(evidence_data)
                        st.dataframe(evidence_df, use_container_width=True)
                        
                        # Detailed Control Analysis
                        st.markdown("### 🔍 Detailed Control Analysis")
                        
                        for control in report['controls']:
                            with st.expander(f"📋 {control['iso_clause']} - {control['control_name']}"):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.markdown("**Control Description:**")
                                    control_descriptions = {
                                        "9.2.1": "Ensures proper user access management and authentication controls are in place",
                                        "8.2.3": "Implements technical risk assessment procedures for AI systems",
                                        "9.4.1": "Provides continuous monitoring and information security oversight"
                                    }
                                    st.write(control_descriptions.get(control['iso_clause'], "Standard ISO 42001 control requirement"))
                                    
                                    st.markdown("**Evidence Summary:**")
                                    st.write(f"- Total evidence events: {control['evidence_count']}")
                                    st.write(f"- Sample events available: {len(control['sample_events'])}")
                                    st.write(f"- Compliance status: {control['compliance_status']}")
                                
                                with col2:
                                    # Compliance score visualization
                                    score = 100 if control['compliance_status'] == 'compliant' else 75
                                    
                                    fig = go.Figure(go.Indicator(
                                        mode="gauge+number",
                                        value=score,
                                        title={'text': "Compliance Score"},
                                        gauge={
                                            'axis': {'range': [None, 100]},
                                            'bar': {'color': "#4CAF50" if score == 100 else "#FF9800"},
                                            'steps': [
                                                {'range': [0, 50], 'color': "rgba(244, 67, 54, 0.2)"},
                                                {'range': [50, 85], 'color': "rgba(255, 152, 0, 0.2)"},
                                                {'range': [85, 100], 'color': "rgba(76, 175, 80, 0.2)"}
                                            ]
                                        }
                                    ))
                                    
                                    fig.update_layout(
                                        height=200,
                                        template="plotly_dark",
                                        margin=dict(l=20, r=20, t=40, b=20)
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                        
                        # Download Options
                        st.markdown("### 📥 Export Options")
                        
                        download_cols = st.columns(3)
                        
                        with download_cols[0]:
                            report_json = json.dumps(report, indent=2, default=str)
                            st.download_button(
                                label="📄 Download JSON Report",
                                data=report_json,
                                file_name=f"iso_42001_compliance_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                                mime="application/json"
                            )
                        
                        with download_cols[1]:
                            # Create CSV summary
                            csv_data = pd.DataFrame(evidence_data).to_csv(index=False)
                            st.download_button(
                                label="📊 Download CSV Summary",
                                data=csv_data,
                                file_name=f"compliance_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        
                        with download_cols[2]:
                            st.button("📧 Email Report", help="Send report to compliance team")
                    
                    else:
                        st.error(f"❌ **Report Generation Failed** - Status: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"❌ **Error generating report:** {str(e)}")
    
    with col2:
        st.markdown("### 🎯 Quick Actions")
        
        action_buttons = [
            ("🔍 Audit Trail", "View complete audit log"),
            ("📊 Risk Assessment", "Generate risk assessment report"),
            ("🎯 Control Testing", "Run control effectiveness tests"),
            ("📋 Policy Review", "Review current policies"),
            ("🔄 Update Framework", "Update compliance framework")
        ]
        
        for button_text, help_text in action_buttons:
            if st.button(button_text, help=help_text, use_container_width=True):
                st.toast(f"Executing: {button_text}", icon="🔄")
    
    # Compliance Trends
    st.markdown("---")
    st.markdown("## 📈 Compliance Trends & Monitoring")
    
    # Generate compliance trend data
    dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
    compliance_rates = 95 + 4 * np.random.random(90) + np.sin(np.arange(90) * 2 * np.pi / 30)  # Trending upward with monthly cycle
    
    # Ensure realistic bounds
    compliance_rates = np.clip(compliance_rates, 90, 100)
    
    fig = go.Figure()
    
    # Compliance rate line
    fig.add_trace(go.Scatter(
        x=dates,
        y=compliance_rates,
        name='Compliance Rate',
        line=dict(color='#4CAF50', width=3),
        fill='tozeroy',
        fillcolor='rgba(76, 175, 80, 0.1)',
        hovertemplate='<b>%{y:.1f}%</b><br>%{x}<extra></extra>'
    ))
    
    # Add target line
    fig.add_hline(
        y=95,
        line_dash="dash",
        line_color="#FF9800",
        annotation_text="Target: 95%",
        annotation_position="bottom right"
    )
    
    # Add regulatory milestone markers
    milestones = [
        (dates[30], "Q1 Audit", 98.5),
        (dates[60], "ISO Review", 99.2),
        (dates[75], "External Audit", 99.8)
    ]
    
    for date, event, rate in milestones:
        fig.add_trace(go.Scatter(
            x=[date],
            y=[rate],
            mode='markers+text',
            name=event,
            marker=dict(color='#2196F3', size=12, symbol='diamond'),
            text=[event],
            textposition="top center",
            showlegend=False
        ))
    
    fig.update_layout(
        template="plotly_dark",
        height=500,
        title="📈 90-Day Compliance Trend Analysis",
        xaxis_title="Date",
        yaxis_title="Compliance Rate (%)",
        yaxis_range=[88, 102],
        font=dict(family="Inter"),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Compliance Framework Mapping
    st.markdown("---")
    st.markdown("## 🗺️ Regulatory Framework Mapping")
    
    framework_tabs = st.tabs(["🏛️ ISO 42001", "🇺🇸 NIST AI RMF", "🇪🇺 EU AI Act", "🛡️ SOC 2"])
    
    with framework_tabs[0]:
        st.markdown("### ISO/IEC 42001:2023 - AI Management Systems")
        
        iso_mapping = {
            'Clause': ['4.1', '5.2', '6.1', '7.1', '8.1', '9.2', '10.1'],
            'Requirement': [
                'Understanding the organization and its context',
                'AI management system policy',
                'Actions to address risks and opportunities',
                'Resources for AI management system',
                'Operational planning and control',
                'Internal audit',
                'Continual improvement'
            ],
            'Implementation Status': ['✅ Complete', '✅ Complete', '✅ Complete', '✅ Complete', '✅ Complete', '✅ Complete', '🔄 In Progress'],
            'Evidence Count': [45, 23, 67, 34, 89, 56, 12],
            'Last Verified': ['2024-01-15', '2024-01-14', '2024-01-13', '2024-01-12', '2024-01-11', '2024-01-10', '2024-01-09']
        }
        
        iso_df = pd.DataFrame(iso_mapping)
        st.dataframe(iso_df, use_container_width=True)
    
    with framework_tabs[1]:
        st.markdown("### NIST AI Risk Management Framework 1.0")
        
        nist_functions = {
            'Function': ['GOVERN', 'MAP', 'MEASURE', 'MANAGE'],
            'Description': [
                'Cultivate a risk management culture',
                'Understand AI risks in context',
                'Measure and track AI risks',
                'Respond to and recover from incidents'
            ],
            'Maturity Level': ['Level 4', 'Level 4', 'Level 3', 'Level 4'],
            'Key Controls': [15, 12, 18, 22],
            'Compliance %': ['98%', '96%', '94%', '99%']
        }
        
        nist_df = pd.DataFrame(nist_functions)
        st.dataframe(nist_df, use_container_width=True)
    
    with framework_tabs[2]:
        st.markdown("### EU AI Act Compliance")
        
        eu_requirements = {
            'Risk Category': ['Minimal Risk', 'Limited Risk', 'High Risk', 'Prohibited'],
            'Requirements': [
                'Basic transparency obligations',
                'Specific transparency requirements',
                'Conformity assessment required',
                'Immediate compliance required'
            ],
            'Current Status': ['✅ Compliant', '✅ Compliant', '⚠️ Monitoring', '✅ Compliant'],
            'Key Measures': [8, 15, 45, 3],
            'Next Review': ['Q3 2024', 'Q2 2024', 'Monthly', 'Continuous']
        }
        
        eu_df = pd.DataFrame(eu_requirements)
        st.dataframe(eu_df, use_container_width=True)
    
    with framework_tabs[3]:
        st.markdown("### SOC 2 Type II Controls")
        
        soc2_controls = {
            'Trust Service': ['Security', 'Availability', 'Processing Integrity', 'Confidentiality', 'Privacy'],
            'Control Count': [25, 15, 18, 12, 20],
            'Tested': [23, 15, 16, 11, 18],
            'Exceptions': [2, 0, 2, 1, 2],
            'Status': ['🔄 Remediation', '✅ Clean', '🔄 Remediation', '🔄 Remediation', '🔄 Remediation']
        }
        
        soc2_df = pd.DataFrame(soc2_controls)
        st.dataframe(soc2_df, use_container_width=True)

# Footer with enhanced design
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%); border-radius: 12px; margin-top: 2rem;">
    <h4 style="margin: 0; font-size: 1.1rem; background: linear-gradient(45deg, #4CAF50, #2196F3); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Claude Governance Control Plane v1.0.0
    </h4>
    <p style="margin: 8px 0 0 0; font-size: 0.9rem; opacity: 0.7;">
        Implementing Anthropic's Responsible Scaling Policy • Built with ❤️ for AI Safety
    </p>
    <p style="margin: 4px 0 0 0; font-size: 0.8rem; opacity: 0.6;">
        <a href="https://github.com/dipampaul17/cgcp" target="_blank" style="color: #4CAF50; text-decoration: none;">GitHub Repository</a> •
        <a href="http://localhost:8000/docs" target="_blank" style="color: #2196F3; text-decoration: none;">API Documentation</a>
    </p>
</div>
""", unsafe_allow_html=True) 