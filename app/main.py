import streamlit as st
import traceback
import time
import os
from dotenv import load_dotenv

# Load environment variables explicitly from the project root
load_dotenv(override=True)
key = os.getenv("GROQ_API_KEY")

from utils import clean_text

# Set Page Config
st.set_page_config(layout="wide", page_title="Company Outreach Generator", page_icon="🏫")

# Check for API Key
if not key:
    st.error("⚠️ GROQ_API_KEY not found in environment variables. Please add it to your .env file.")
    st.info("You can get an API key from https://console.groq.com/")
    st.stop()


# Initialize Session State
if 'page' not in st.session_state:
    st.session_state.page = 'landing'
if 'user_details' not in st.session_state:
    st.session_state.user_details = {}
if 'institution_summary' not in st.session_state:
    st.session_state.institution_summary = ""
if 'generated_mail' not in st.session_state:
    st.session_state.generated_mail = ""
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

# CSS for Premium Professional Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    * { font-family: 'Outfit', sans-serif; }
    
    .main {
        background-color: #f8fafc;
    }
    
    /* Premium Gradient Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        padding: 12px 28px;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        width: auto;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
        color: white;
        border: none;
    }
    
    /* Glassmorphism Cards */
    .css-card {
        background: white;
        padding: 40px;
        border-radius: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 24px;
        border: 1px solid #f1f5f9;
    }
    
    .job-card {
        background: white;
        color: #334155;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 16px;
        border-left: 6px solid #6366f1;
    }

    h1 {
        color: #1e293b;
        font-weight: 700;
        letter-spacing: -0.025em;
    }
    
    h2, h3 {
        color: #334155;
        font-weight: 600;
    }

    /* Form Input Styling */
    .stTextInput>div>div>input {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        padding: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# Scraping Helper
def scrape_page_content(url):
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(["script", "style", "nav", "footer", "header", "form"]):
            element.decompose()
            
        text = soup.get_text(separator=' ')
        cleaned = clean_text(text)
        
        if len(cleaned) < 500:
            return None
            
        return cleaned
    except Exception as e:
        print(f"Scraping Error for {url}: {e}")
        return None

def process_institution_url(chain, url):
    cleaned = scrape_page_content(url)
    if cleaned:
        return chain.summarize_institution(cleaned[:10000]) 
    return None

# Navigation Flows
def go_to_setup():
    st.session_state.page = 'setup'

# Resource Caching for Performance and Startup
# @st.cache_resource
def get_chain(api_key=None):
    """Refreshed version 1.0.1"""
    try:
        from chains import Chain
        key = api_key or os.getenv("GROQ_API_KEY")
        # Force reload of the module if needed, but usually creating a new instance is enough if the file changed
        import importlib
        import chains
        importlib.reload(chains)
        from chains import Chain
        return Chain(api_key=key)
    except Exception as e:
        st.error(f"Error initializing Chain: {e}")
        return None

# @st.cache_resource
def get_portfolio():
    try:
        from portfolio import Portfolio
        return Portfolio()
    except Exception as e:
        st.error(f"Error initializing Portfolio: {e}")
        return None

def main():
    # LANDING PAGE
    if st.session_state.page == 'landing':
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.title("Executive Outreach Generator")
        st.write("### The Senior Placement Officer's Strategic Engine")
        st.write("Leverage 10+ years of industrial network intelligence to draft masterful campus partnership proposals.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.button("Begin Strategic Setup", on_click=go_to_setup, use_container_width=True)

    # SETUP PAGE
    elif st.session_state.page == 'setup':
        st.markdown('<div class="css-card"><h2>Institutional Profile Setup</h2></div>', unsafe_allow_html=True)
        
        with st.form("user_setup_form"):
            name = st.text_input("Your Full Name (e.g. Prof. Mohan Kumar)")
            designation = st.text_input("Your Designation (e.g. Head of Corporate Relations)")
            inst_name = st.text_input("Institution Name")
            inst_url = st.text_input("Institution Website URL")
            
            submitted = st.form_submit_button("Continue to Engine")
            
            if submitted:
                if name and designation and inst_name and inst_url:
                    st.session_state.user_details = {
                        "name": name,
                        "designation": designation,
                        "institution_name": inst_name,
                        "institution_url": inst_url
                    }
                    
                    chain = get_chain()
                    if chain:
                        with st.status("Analyzing Institution Workforce Pipeline...") as status:
                            summary = process_institution_url(chain, inst_url)
                            if summary:
                                st.session_state.institution_summary = summary
                                status.update(label="✅ Institution Analysis Complete", state="complete")
                                time.sleep(1)
                                st.session_state.page = 'main'
                                st.rerun()
                            else:
                                status.update(label="⚠️ Scraper Limited. Proceeding with manual context.", state="complete")
                                time.sleep(1)
                                st.session_state.page = 'main'
                                st.rerun()
                else:
                    st.warning("All professional credentials are required for persona initialization.")

    # MAIN PAGE
    elif st.session_state.page == 'main':
        chain = get_chain()
        portfolio = get_portfolio()
        
        if not chain or not portfolio:
            st.error("Engine Initialization Error. Check API Configuration.")
            return

        with st.sidebar:
            st.markdown(f"### 👤 Senior Persona")
            st.info(f"**{st.session_state.user_details.get('name')}**\n\n{st.session_state.user_details.get('designation')}\n\n{st.session_state.user_details.get('institution_name')}")
            if st.button("🔄 Edit Profile", use_container_width=True):
                st.session_state.page = 'setup'
                st.rerun()

        st.title("Strategic Opportunities")
        portfolio.load_portfolio()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            company_query = st.text_input("Target Company (e.g. 'Google', 'Nike', 'Wipro')")
        with col2:
            search_trigger = st.button("Search Intelligence", use_container_width=True)

        if search_trigger and company_query:
            company_query = company_query.strip()
            display_name = company_query.title()
            st.session_state.display_name = display_name
            
            with st.status(f"Scanning Global Opportunities for {display_name}...") as status:
                try:
                    from ddgs import DDGS
                    inst_name = st.session_state.user_details.get('institution_name', '')
                    
                    with DDGS() as ddgs:
                        # Multi-Stage Search
                        results_raw = list(ddgs.text(f"{display_name} careers jobs openings", max_results=8))
                        if not results_raw:
                            results_raw = list(ddgs.text(f"{display_name} careers", max_results=5))
                    
                    if results_raw:
                        snippets = "\n".join([f"- {res['title']}: {res['body']}" for res in results_raw[:5]])
                        report = chain.generate_company_report(display_name, snippets, st.session_state.institution_summary)
                        st.session_state.current_report = report
                        
                        career_url = next((res['href'] for res in results_raw if 'career' in res['href'].lower() or 'job' in res['href'].lower()), results_raw[0]['href'])
                        st.session_state.current_url = career_url
                        
                        data = scrape_page_content(career_url)
                        inst_context = f"Institution: {inst_name}. Summary: {st.session_state.institution_summary}. Company: {display_name}."
                        
                        if data and len(data) > 300:
                            jobs = chain.extract_jobs(data, institution_context=inst_context)
                        else:
                            fallback_data = "\n".join([f"Title: {res['title']}\nSnippet: {res['body']}" for res in results_raw])
                            jobs = chain.extract_jobs(fallback_data, institution_context=inst_context)
                        
                        st.session_state.search_results = jobs
                        status.update(label=f"✅ {display_name} Intelligence Ready", state="complete")
                    else:
                        st.error(f"Unable to locate career data for {display_name}.")
                except Exception as e:
                    st.error(f"Intelligence failure: {e}")

        # PERSISTENT DISPLAY
        if st.session_state.get('current_report'):
            st.subheader(f"📊 Market Analysis: {st.session_state.display_name}")
            st.markdown(f'<div class="job-card">{st.session_state.current_report}</div>', unsafe_allow_html=True)
            
            if st.button("Draft Executive Outreach Email", use_container_width=True):
                st.session_state.selected_job = None
                st.session_state.outreach_mode = True
                st.session_state.generated_mail = None
                st.rerun()

        if st.session_state.get('outreach_mode'):
            st.divider()
            title = f"📧 Pitching to {st.session_state.display_name}"
            if st.session_state.get('selected_job'):
                title += f" ({st.session_state.selected_job.get('role')})"
            st.header(title)
            
            with st.form("outreach_form_premium"):
                col_n, col_d = st.columns(2)
                with col_n:
                    rec_name = st.text_input("Recipient Name", placeholder="e.g. Jane Smith")
                with col_d:
                    rec_desg = st.text_input("Recipient Designation", placeholder="e.g. HR Head")
                    
                intent = st.selectbox("Strategic Intent", 
                                     ["Campus Hiring Drive 2024-25", "Student Internships", "MOU & Partnerships"])
                
                gen_btn = st.form_submit_button("Generate Masterful Draft")
                
                if gen_btn:
                    if not rec_name:
                        st.error("Recipient name is required for executive persona.")
                    else:
                        with st.spinner("Drafting as Senior TPO..."):
                            skills = st.session_state.selected_job.get('skills', []) if st.session_state.get('selected_job') else st.session_state.institution_summary.split()[:5]
                            links = portfolio.query_links(skills)
                            email = chain.write_mail(
                                job=st.session_state.selected_job,
                                links=links,
                                user_details=st.session_state.user_details,
                                recipient_details={"name": rec_name, "designation": rec_desg},
                                intent=intent,
                                company_name=st.session_state.display_name,
                                institution_summary=st.session_state.institution_summary
                            )
                            if email:
                                st.session_state.generated_mail = email
                                st.rerun()

            if st.session_state.get('generated_mail'):
                st.text_area("Final Executive Draft", value=st.session_state.generated_mail, height=450, key="final_outreach_text")
                st.download_button("📩 Download Proposal", st.session_state.generated_mail, 
                                 file_name="proposal.txt", use_container_width=True)
                if st.button("New Action / Clear", use_container_width=True):
                    st.session_state.outreach_mode = False
                    st.session_state.generated_mail = None
                    st.rerun()

        if st.session_state.search_results and not st.session_state.get('outreach_mode'):
            st.divider()
            st.write(f"### Specific Vacancies at {st.session_state.display_name}")
            for idx, job in enumerate(st.session_state.search_results):
                with st.expander(f"📋 {job.get('role', 'Opportunity')}", expanded=(idx==0)):
                    st.write(f"**Brief:** {job.get('description', 'N/A')}")
                    st.write(f"**Skills:** {job.get('skills', 'N/A')}")
                    if st.button(f"Draft Pitch for this Role", key=f"job_btn_{idx}"):
                         st.session_state.selected_job = job
                         st.session_state.outreach_mode = True
                         st.session_state.generated_mail = None
                         st.rerun()

if __name__ == "__main__":
    main()
