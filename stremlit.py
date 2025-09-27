import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Synthetic Data Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_supported_domains():
    """Get supported domains from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/supported-domains")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def get_supported_formats():
    """Get supported formats from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/supported-formats")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def generate_synthetic_data(domain, data_format, num_records, context=None):
    """Generate synthetic data via API"""
    payload = {
        "domain": domain,
        "data_format": data_format,
        "num_records": num_records
    }
    if context:
        payload["context"] = context
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-synthetic-data",
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        return response
    except requests.exceptions.RequestException as e:
        return None

def get_file_sample(file_path, num_rows=5):
    """Get sample data from generated file"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/file-sample",
            params={"file_path": file_path, "num_rows": num_rows}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def list_files():
    """List all generated files"""
    try:
        response = requests.get(f"{API_BASE_URL}/list-files")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

# Main app
def main():
    st.markdown("<h1 class='main-header'>🤖 Synthetic Data Generator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Generate high-quality synthetic data using LangGraph and React prompting</p>", unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.markdown("""
        <div class='error-box'>
            <strong>⚠️ API Connection Error</strong><br>
            Cannot connect to the API at <code>http://localhost:8000</code>.<br>
            Please make sure the Docker container is running: <code>docker-compose up</code>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    st.markdown("""
    <div class='success-box'>
        ✅ API is running and healthy!
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    st.sidebar.header("📋 Configuration")
    
    # Get supported options
    domains_data = get_supported_domains()
    formats_data = get_supported_formats()
    
    if not domains_data or not formats_data:
        st.error("Failed to load configuration from API")
        st.stop()
    
    # Domain selection
    domain_options = list(domains_data["domains"])
    selected_domain = st.sidebar.selectbox(
        "🏥 Select Domain",
        domain_options,
        help="Choose the domain for synthetic data generation"
    )
    
    # Show domain description
    if selected_domain and selected_domain in domains_data["details"]:
        domain_desc = domains_data["details"][selected_domain]["description"]
        st.sidebar.info(f"**{selected_domain.title()}**: {domain_desc}")
    
    # Format selection
    format_options = list(formats_data["formats"])
    selected_format = st.sidebar.selectbox(
        "📊 Select Data Format",
        format_options,
        help="Choose the output format for synthetic data"
    )
    
    # Show format description
    if selected_format and selected_format in formats_data["details"]:
        format_desc = formats_data["details"][selected_format]["description"]
        st.sidebar.info(f"**{selected_format.replace('_', ' ').title()}**: {format_desc}")
    
    # Number of records
    num_records = st.sidebar.slider(
        "📈 Number of Records",
        min_value=5,
        max_value=100,
        value=20,
        step=5,
        help="Number of synthetic records to generate (max 100 for demo)"
    )
    
    # Optional context
    context = st.sidebar.text_area(
        "💬 Additional Context (Optional)",
        placeholder="e.g., focus on emergency procedures, financial risk assessment, etc.",
        help="Provide additional context to specialize the generated data"
    )
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["🚀 Generate Data", "📁 File Browser", "ℹ️ About"])
    
    with tab1:
        st.header("Generate Synthetic Data")
        
        # Summary of selection
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Domain", selected_domain.title())
        with col2:
            st.metric("Format", selected_format.replace('_', ' ').title())
        with col3:
            st.metric("Records", num_records)
        
        if context:
            st.markdown(f"**Context**: {context}")
        
        # Generate button
        if st.button("🚀 Generate Synthetic Data", type="primary", use_container_width=True):
            with st.spinner("Generating synthetic data... This may take a few minutes."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Update progress
                for i in range(20):
                    progress_bar.progress((i + 1) * 5)
                    status_text.text(f"Processing... {(i + 1) * 5}%")
                    time.sleep(0.1)
                
                # Generate data
                response = generate_synthetic_data(selected_domain, selected_format, num_records, context)
                
                if response and response.status_code == 200:
                    result = response.json()
                    progress_bar.progress(100)
                    status_text.text("Generation completed!")
                    
                    st.success("✅ Data generation completed successfully!")
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Status", result["status"])
                        st.metric("Records Generated", result["total_records"])
                    with col2:
                        st.metric("Generation Time", result["generation_time"])
                        st.metric("File Path", result["file_path"])
                    
                    # Store file path in session state for preview
                    st.session_state.last_generated_file = result["file_path"]
                    
                    # Auto-preview the generated data
                    if st.button("👀 Preview Generated Data"):
                        preview_data = get_file_sample(result["file_path"], 10)
                        if preview_data:
                            st.subheader("📋 Data Preview")
                            df = pd.DataFrame(preview_data["data"])
                            st.dataframe(df, use_container_width=True)
                            
                            # Download info
                            st.info(f"💾 Full dataset saved to: `{result['file_path']}`")
                        else:
                            st.error("Failed to load preview data")
                
                elif response:
                    error_data = response.json()
                    st.error(f"❌ Generation failed: {error_data.get('detail', {}).get('message', 'Unknown error')}")
                    progress_bar.empty()
                    status_text.empty()
                else:
                    st.error("❌ Failed to connect to API")
                    progress_bar.empty()
                    status_text.empty()
    
    with tab2:
        st.header("📁 Generated Files")
        
        if st.button("🔄 Refresh File List"):
            st.rerun()
        
        files_data = list_files()
        if files_data and files_data["files"]:
            st.write(f"Found {files_data['total_files']} generated files:")
            
            for file_info in files_data["files"]:
                with st.expander(f"📄 {file_info['filename']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**File Path**: `{file_info['file_path']}`")
                        st.write(f"**Size**: {file_info['size']} bytes")
                    with col2:
                        st.write(f"**Created**: {file_info['created']}")
                    
                    # Preview button
                    if st.button(f"👀 Preview", key=f"preview_{file_info['filename']}"):
                        preview_data = get_file_sample(file_info['file_path'], 5)
                        if preview_data:
                            st.write(f"**Sample Data** ({preview_data['sample_rows']}/{preview_data['total_records']} records):")
                            df = pd.DataFrame(preview_data["data"])
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.error("Failed to load preview")
        else:
            st.info("No generated files found. Generate some data first!")
    
    with tab3:
        st.header("ℹ️ About")
        
        st.markdown("""
        ### 🤖 Synthetic Data Generator
        
        This application generates high-quality synthetic data using:
        
        - **🧠 LangGraph**: Multi-agent workflow orchestration
        - **🔄 React Prompting**: Thought-Action-Observation-Reflection pattern
        - **🏗️ Structured Outputs**: Guaranteed schema compliance with Pydantic
        - **🌐 Web Research**: Domain context enrichment
        - **✅ Quality Assurance**: Deduplication and validation
        
        ### 🎯 Supported Domains
        - **Healthcare**: Medical procedures, diagnostics, patient care
        - **Finance**: Banking, investments, risk management
        - **Business**: Strategy, operations, management
        - **Law**: Legal procedures, contracts, compliance
        - **Technology**: Software development, AI, cybersecurity
        - **Education**: Learning, curriculum, assessment
        
        ### 📊 Data Formats
        - **Q&A**: Question-answer pairs for training chatbots
        - **Entity Relationships**: Knowledge graph relationships
        - **RAG Chunks**: Content optimized for retrieval systems
        - **Fine-tuning**: Instruction-input-output for model training
        
        ### 🚀 Workflow
        1. **Research**: Web scraping and domain analysis
        2. **Generate**: Batch creation of synthetic records
        3. **Evaluate**: Quality validation and deduplication
        4. **Export**: CSV file generation
        """)
        
        # API Status
        st.subheader("🔧 API Status")
        api_health = check_api_health()
        if api_health:
            st.success("✅ API is healthy and responsive")
        else:
            st.error("❌ API is not responding")
        
        # Quick stats
        files_data = list_files()
        if files_data:
            st.metric("Total Generated Files", files_data["total_files"])

if __name__ == "__main__":
    main()