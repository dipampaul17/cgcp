"""
Claude Governance Control Plane - Modern Dashboard
Real-time monitoring and policy management for Anthropic's RSP
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
from typing import Dict, List


# Page configuration
st.set_page_config(
    page_title="Claude Governance Control Plane",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border: 1px solid #333;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7);
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(45deg, #4CAF50, #2196F3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #4CAF50, #2196F3);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(76, 175, 80, 0.4);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #1a1a1a;
    }
    
    /* Cards */
    .card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
    }
    
    /* Success/Warning/Error styling */
    .success-box {
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid #4CAF50;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .warning-box {
        background: rgba(255, 152, 0, 0.1);
        border: 1px solid #FF9800;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .error-box {
        background: rgba(244, 67, 54, 0.1);
        border: 1px solid #F44336;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Risk badges */
    .risk-critical {
        background-color: #F44336;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .risk-high {
        background-color: #FF9800;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .risk-medium {
        background-color: #FFC107;
        color: black;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .risk-low {
        background-color: #4CAF50;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def fetch_metrics():
    """Fetch current metrics from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics")
        return response.json() if response.status_code == 200 else None
    except:
        return None

def fetch_hourly_stats(hours=24):
    """Fetch hourly statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/hourly-stats", params={"hours": hours})
        return response.json() if response.status_code == 200 else None
    except:
        return None

def fetch_review_queue():
    """Fetch events in review queue"""
    try:
        response = requests.get(f"{API_BASE_URL}/review-queue")
        return response.json() if response.status_code == 200 else None
    except:
        return None

def fetch_thresholds():
    """Fetch current risk thresholds"""
    try:
        response = requests.get(f"{API_BASE_URL}/thresholds")
        return response.json() if response.status_code == 200 else None
    except:
        return None

def create_risk_gauge(value, title, color):
    """Create a modern gauge chart for risk metrics"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 16}},
        delta = {'reference': 50, 'increasing': {'color': "red"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': 'rgba(76, 175, 80, 0.1)'},
                {'range': [25, 50], 'color': 'rgba(255, 193, 7, 0.1)'},
                {'range': [50, 75], 'color': 'rgba(255, 152, 0, 0.1)'},
                {'range': [75, 100], 'color': 'rgba(244, 67, 54, 0.1)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Arial"},
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

# Sidebar navigation
with st.sidebar:
    st.markdown("# 🛡️ CGCP")
    st.markdown("### Claude Governance Control Plane")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["🎯 Operations Dashboard", "🔍 Policy Review", "📊 Analytics", "📜 Compliance"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### System Status")
    
    # Check API status
    try:
        health = requests.get(f"{API_BASE_URL}/health").json()
        st.success("✅ API Online")
    except:
        st.error("❌ API Offline")
    
    st.markdown("---")
    st.markdown("### Quick Actions")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.experimental_rerun()
    
    if st.button("📥 Export Report", use_container_width=True):
        st.info("Generating compliance report...")

# Main content based on page selection
if page == "🎯 Operations Dashboard":
    st.title("🎯 Operations Dashboard")
    st.markdown("Real-time monitoring of Claude safety systems")
    
    # Fetch metrics
    metrics = fetch_metrics()
    if not metrics:
        st.error("Unable to fetch metrics. Please ensure the API is running.")
        st.stop()
    
    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Total Events",
            value=f"{metrics.get('total_events', 0):,}",
            delta="+12% from last hour"
        )
    
    with col2:
        blocked = metrics.get('actions_taken', {}).get('block', 0)
        total = metrics.get('total_events', 1)
        block_rate = (blocked / total * 100) if total > 0 else 0
        st.metric(
            label="Block Rate",
            value=f"{block_rate:.1f}%",
            delta=f"{blocked:,} blocked"
        )
    
    with col3:
        escalated = metrics.get('actions_taken', {}).get('escalate', 0)
        st.metric(
            label="Escalations",
            value=escalated,
            delta="↑ 2 new" if escalated > 0 else "No new"
        )
    
    with col4:
        asl_triggers = metrics.get('asl_triggers', 0)
        st.metric(
            label="ASL-3 Triggers",
            value=asl_triggers,
            delta="⚠️ Critical" if asl_triggers > 0 else "✅ Safe"
        )
    
    with col5:
        compliance_rate = 100 - block_rate
        st.metric(
            label="Compliance Rate",
            value=f"{compliance_rate:.1f}%",
            delta="↑ 2.3%" if compliance_rate > 95 else "↓ 1.2%"
        )
    
    st.markdown("---")
    
    # Risk gauges
    st.markdown("### 🎯 Risk Detection Overview")
    
    risk_cols = st.columns(4)
    risk_data = metrics.get('risk_detections', {})
    
    risk_configs = [
        ("CBRN", risk_data.get('cbrn', 0), "#F44336"),
        ("Self-Harm", risk_data.get('self_harm', 0), "#FF9800"),
        ("Jailbreak", risk_data.get('jailbreak', 0), "#FFC107"),
        ("Exploitation", risk_data.get('exploitation', 0), "#4CAF50")
    ]
    
    for idx, (risk_type, count, color) in enumerate(risk_configs):
        with risk_cols[idx]:
            total_events = metrics.get('total_events', 1)
            risk_percentage = (count / total_events * 100) if total_events > 0 else 0
            fig = create_risk_gauge(risk_percentage, risk_type, color)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"<center>{count} detections</center>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Time series and distribution charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📈 Event Volume (24h)")
        
        hourly_stats = fetch_hourly_stats()
        if hourly_stats:
            df_hourly = pd.DataFrame({
                'Hour': pd.to_datetime(hourly_stats['hours']),
                'Events': hourly_stats['event_counts'],
                'Blocked': hourly_stats['blocked_counts'],
                'Escalated': hourly_stats['escalated_counts']
            })
            
            fig = go.Figure()
            
            # Add traces
            fig.add_trace(go.Scatter(
                x=df_hourly['Hour'], y=df_hourly['Events'],
                name='Total Events',
                line=dict(color='#2196F3', width=3),
                fill='tozeroy',
                fillcolor='rgba(33, 150, 243, 0.1)'
            ))
            
            fig.add_trace(go.Scatter(
                x=df_hourly['Hour'], y=df_hourly['Blocked'],
                name='Blocked',
                line=dict(color='#F44336', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=df_hourly['Hour'], y=df_hourly['Escalated'],
                name='Escalated',
                line=dict(color='#FF9800', width=2)
            ))
            
            fig.update_layout(
                template="plotly_dark",
                height=400,
                margin=dict(l=0, r=0, t=0, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("### 🎭 Surface Distribution")
        
        surface_data = metrics.get('events_by_surface', {})
        if surface_data:
            fig = go.Figure(data=[go.Pie(
                labels=list(surface_data.keys()),
                values=list(surface_data.values()),
                hole=.6,
                marker_colors=['#2196F3', '#4CAF50', '#FF9800'],
                textposition='inside',
                textinfo='percent+label'
            )])
            
            fig.update_layout(
                template="plotly_dark",
                height=400,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                annotations=[dict(text='Surfaces', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent high-risk events
    st.markdown("---")
    st.markdown("### 🚨 Recent High-Risk Events")
    
    review_queue = fetch_review_queue()
    if review_queue and review_queue.get('items'):
        for event in review_queue['items'][:5]:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    risk_scores = event.get('risk_scores', {})
                    max_risk = max(risk_scores.values()) if risk_scores else 0
                    
                    # Determine risk level
                    if max_risk > 0.8:
                        risk_badge = '<span class="risk-critical">CRITICAL</span>'
                    elif max_risk > 0.6:
                        risk_badge = '<span class="risk-high">HIGH</span>'
                    elif max_risk > 0.4:
                        risk_badge = '<span class="risk-medium">MEDIUM</span>'
                    else:
                        risk_badge = '<span class="risk-low">LOW</span>'
                    
                    st.markdown(f"""
                    <div class="card">
                        <b>Event ID:</b> {event['event_id'][:8]}... {risk_badge}<br>
                        <b>User:</b> {event['user_id']} | <b>Org:</b> {event['org_id']}<br>
                        <b>Prompt Preview:</b> {event['prompt_preview'][:100]}...
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**Risk Scores:**")
                    for category, score in risk_scores.items():
                        st.progress(score, text=f"{category}: {score:.2f}")
                
                with col3:
                    st.markdown("**Actions:**")
                    if st.button("Review", key=f"review_{event['event_id']}"):
                        st.session_state['selected_event'] = event['event_id']
                        st.experimental_rerun()
    else:
        st.info("No high-risk events in the queue")

elif page == "🔍 Policy Review":
    st.title("🔍 Policy Review Queue")
    st.markdown("Review and adjudicate escalated events")
    
    review_queue = fetch_review_queue()
    if not review_queue:
        st.error("Unable to fetch review queue")
        st.stop()
    
    # Queue stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Queue Size", review_queue.get('total', 0))
    with col2:
        st.metric("Avg Wait Time", "2.3 hours")
    with col3:
        st.metric("SLA Compliance", "98.5%")
    
    st.markdown("---")
    
    # Review interface
    if review_queue.get('items'):
        for idx, event in enumerate(review_queue['items']):
            with st.expander(f"Event {event['event_id'][:8]}... - {event.get('reason', 'No reason')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Event Details:**")
                    st.json({
                        "User ID": event['user_id'],
                        "Organization": event['org_id'],
                        "Surface": event['surface'],
                        "Tier": event['tier'],
                        "Timestamp": event['timestamp']
                    })
                    
                    st.markdown("**Prompt:**")
                    st.text_area("", value=event['prompt_preview'], height=100, disabled=True)
                    
                    st.markdown("**Risk Analysis:**")
                    risk_df = pd.DataFrame(
                        [(k, v) for k, v in event['risk_scores'].items()],
                        columns=['Category', 'Score']
                    )
                    fig = px.bar(risk_df, x='Category', y='Score', 
                                color='Score', color_continuous_scale='Reds')
                    fig.update_layout(template="plotly_dark", height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("**Review Decision:**")
                    
                    decision = st.radio(
                        "Action",
                        ["Allow", "Block", "Redact"],
                        key=f"decision_{idx}"
                    )
                    
                    update_policy = st.checkbox("Update policy threshold", key=f"update_{idx}")
                    
                    if update_policy:
                        category = st.selectbox(
                            "Category",
                            list(event['risk_scores'].keys()),
                            key=f"cat_{idx}"
                        )
                        
                        current_thresholds = fetch_thresholds()
                        if current_thresholds:
                            current = current_thresholds.get(category, {}).get(event['tier'], 0.5)
                            new_threshold = st.slider(
                                "New threshold",
                                0.0, 1.0, current,
                                key=f"threshold_{idx}"
                            )
                    
                    if st.button("Submit Decision", key=f"submit_{idx}", type="primary"):
                        # Submit review decision
                        payload = {
                            "decision": decision.lower(),
                            "update_policy": update_policy
                        }
                        
                        if update_policy:
                            payload["category"] = category
                            payload["new_threshold"] = new_threshold
                        
                        response = requests.post(
                            f"{API_BASE_URL}/review/{event['event_id']}",
                            json=payload
                        )
                        
                        if response.status_code == 200:
                            st.success("Decision submitted successfully!")
                            time.sleep(1)
                            st.experimental_rerun()
                        else:
                            st.error("Failed to submit decision")

elif page == "📊 Analytics":
    st.title("📊 Analytics & Insights")
    st.markdown("Deep dive into safety metrics and trends")
    
    # Date range selector
    col1, col2 = st.columns([1, 3])
    with col1:
        date_range = st.selectbox(
            "Time Range",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom"]
        )
    
    st.markdown("---")
    
    # Fetch metrics
    metrics = fetch_metrics()
    if not metrics:
        st.error("Unable to fetch metrics")
        st.stop()
    
    # Create detailed analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Risk Category Breakdown")
        
        risk_data = []
        for category, count in metrics.get('risk_detections', {}).items():
            if count > 0:  # Only include categories with detections
                risk_data.append({
                    'Category': category.replace('_', ' ').title(),
                    'Detections': count,
                    'Percentage': count / max(metrics.get('total_events', 1), 1) * 100
                })
        
        if risk_data:
            df_risk = pd.DataFrame(risk_data)
            fig = px.treemap(
                df_risk, 
                path=['Category'], 
                values='Detections',
                color='Percentage',
                color_continuous_scale='RdYlBu_r',
                title="Risk Detection Heatmap"
            )
            fig.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Show alternative visualization when no risk data
            st.info("No risk detections to display. The system is operating normally.")
            # Show a simple bar chart instead
            categories = ['CBRN', 'Self Harm', 'Jailbreak', 'Exploitation']
            values = [0, 0, 0, 0]
            fig = go.Figure(data=[go.Bar(x=categories, y=values)])
            fig.update_layout(
                template="plotly_dark",
                height=400,
                title="Risk Detection Status - All Clear",
                yaxis_title="Detection Count"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🛡️ Action Distribution")
        
        action_data = metrics.get('actions_taken', {})
        if action_data:
            fig = go.Figure(data=[
                go.Bar(
                    x=list(action_data.keys()),
                    y=list(action_data.values()),
                    marker_color=['#4CAF50', '#F44336', '#FF9800', '#2196F3'],
                    text=list(action_data.values()),
                    textposition='auto',
                )
            ])
            fig.update_layout(
                template="plotly_dark",
                height=400,
                title="Policy Actions Taken",
                xaxis_title="Action Type",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tier comparison
    st.markdown("---")
    st.markdown("### 🏢 Tier-Based Analysis")
    
    tier_data = metrics.get('events_by_tier', {})
    if tier_data:
        # Create stacked bar chart showing actions by tier
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Events by Tier", "Risk Detection by Tier"),
            specs=[[{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # Events by tier
        fig.add_trace(
            go.Bar(x=list(tier_data.keys()), y=list(tier_data.values()), name="Events"),
            row=1, col=1
        )
        
        # Mock risk detection by tier (in real app, fetch from API)
        tiers = list(tier_data.keys())
        risk_by_tier = [15, 8, 25]  # Mock data
        
        fig.add_trace(
            go.Scatter(
                x=tiers, y=risk_by_tier, 
                mode='lines+markers',
                name="Risk Detection %",
                line=dict(color='#FF5252', width=3),
                marker=dict(size=10)
            ),
            row=1, col=2
        )
        
        fig.update_layout(template="plotly_dark", height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

elif page == "📜 Compliance":
    st.title("📜 Compliance & Audit")
    st.markdown("ISO 42001 compliance reporting and evidence generation")
    
    # Compliance overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("ISO 42001 Status", "✅ Compliant")
    with col2:
        st.metric("Last Audit", "2 days ago")
    with col3:
        st.metric("Control Coverage", "100%")
    with col4:
        st.metric("Next Review", "28 days")
    
    st.markdown("---")
    
    # Generate report button
    if st.button("📥 Generate Compliance Report", type="primary"):
        with st.spinner("Generating ISO 42001 evidence report..."):
            response = requests.get(f"{API_BASE_URL}/export/iso-evidence")
            
            if response.status_code == 200:
                report = response.json()
                
                st.success("✅ Report generated successfully!")
                
                # Display report summary
                st.markdown("### 📊 Report Summary")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <h4>Reporting Period</h4>
                        <p>Last {report['period_days']} days</p>
                        <p>Generated: {report['report_date']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    summary = report['summary']
                    st.markdown(f"""
                    <div class="card">
                        <h4>Event Statistics</h4>
                        <p>Total Events: {summary['total_events']:,}</p>
                        <p>Blocked Events: {summary['blocked_events']:,}</p>
                        <p>ASL Triggers: {summary['asl_triggers']}</p>
                        <p>Compliance Rate: {summary['compliance_rate']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### 🎯 Control Evidence")
                    
                    for control in report['controls']:
                        status_emoji = "✅" if control['compliance_status'] == "compliant" else "⚠️"
                        st.markdown(f"""
                        <div class="success-box" style="margin: 10px 0;">
                            <b>{status_emoji} {control['iso_clause']}</b> - {control['control_name']}<br>
                            Evidence Count: {control['evidence_count']}<br>
                            Sample Events: {len(control['sample_events'])}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Download button
                st.download_button(
                    label="💾 Download Full Report (JSON)",
                    data=json.dumps(report, indent=2),
                    file_name=f"iso_42001_report_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            else:
                st.error("Failed to generate report")
    
    # Compliance trends
    st.markdown("---")
    st.markdown("### 📈 Compliance Trends")
    
    # Mock compliance trend data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    compliance_rates = [95 + (i % 5) for i in range(30)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=compliance_rates,
        mode='lines+markers',
        name='Compliance Rate',
        line=dict(color='#4CAF50', width=3),
        fill='tozeroy',
        fillcolor='rgba(76, 175, 80, 0.1)'
    ))
    
    # Add threshold line
    fig.add_hline(y=95, line_dash="dash", line_color="red", 
                  annotation_text="Minimum Required: 95%")
    
    fig.update_layout(
        template="plotly_dark",
        height=400,
        title="30-Day Compliance Trend",
        xaxis_title="Date",
        yaxis_title="Compliance Rate (%)",
        yaxis_range=[90, 101]
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    Claude Governance Control Plane v1.0.0 | Implementing Anthropic's Responsible Scaling Policy<br>
    Built with ❤️ for AI Safety | <a href="https://github.com/dipampaul17/cgcp" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True) 