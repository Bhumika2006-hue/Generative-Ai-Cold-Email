import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Chain:
    def __init__(self, api_key=None):
        # Use provided key or fallback to env
        final_key = api_key or os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            temperature=0, 
            groq_api_key=final_key, 
            model_name="llama-3.3-70b-versatile"
        )

    def summarize_institution(self, cleaned_text):
        prompt_summary = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM INSTITUTION WEBSITE:
            {page_data}
            
            ### INSTRUCTION:
            You are a Senior Corporate Relations Officer. Summarize this institution's technical strengths, 
            key departments, and overall workforce readiness for a corporate audience. 
            Keep it professional and highlight value propositions for recruiters.
            
            ### SUMMARY (NO PREAMBLE):
            """
        )
        chain_summary = prompt_summary | self.llm
        try:
            res = chain_summary.invoke(input={"page_data": cleaned_text})
            return res.content
        except Exception as e:
            return "Institution summary unavailable due to analysis error."

    def extract_jobs(self, cleaned_text, institution_context=""):
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            
            ### CONTEXT:
            {institution_context}
            
            ### INSTRUCTION:
            The scraped text is from a company's career page or search result.
            Your job is to identify open roles, strategic focus areas, or general hiring intent.
            Return a JSON object with a key `jobs` containing a list of objects.
            Each job object must have: `role`, `experience`, `skills` (as a list), and `description`.
            If no specific jobs are listed, infer the company's likely hiring needs based on the industry and scraped text.
            
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm
        try:
            res = chain_extract.invoke(input={"page_data": cleaned_text, "institution_context": institution_context})
            json_parser = JsonOutputParser()
            parsed_res = json_parser.parse(res.content)
            # Ensure it returns a list
            if isinstance(parsed_res, dict) and 'jobs' in parsed_res:
                return parsed_res['jobs']
            elif isinstance(parsed_res, list):
                return parsed_res
            else:
                return [parsed_res]
        except OutputParserException:
            # Fallback simple extraction if JSON fails
            return [{"role": "General Technology Role", "experience": "Entry Level", "skills": ["Java", "Python", "Communication"], "description": "General hiring opportunity identified via web presence."}]
        except Exception as e:
            return []

    def generate_company_report(self, company_name, search_snippets, institution_summary):
        prompt_report = PromptTemplate.from_template(
            """
            ### CONTEXT:
            You are a Senior Placement Officer (10+ years exp) analyzing a target company for a strategic partnership.
            
            Target Company: {company_name}
            Search Snippets: {search_snippets}
            My Institution: {institution_summary}
            
            ### INSTRUCTION:
            Write a brief, high-level executive summary (max 200 words) answering:
            1. What is this company's current strategic focus (digital transformation, AI, expansion, etc.)?
            2. How does my institution's talent (e.g., CS, IT, Electronics students) fit into their future?
            
            Tone: Professional, Insightful, Strategic.
            ### REPORT (NO PREAMBLE):
            """
        )
        chain_report = prompt_report | self.llm
        res = chain_report.invoke({
            "company_name": company_name, 
            "search_snippets": search_snippets,
            "institution_summary": institution_summary
        })
        return res.content

    def write_mail(self, job, links, user_details, recipient_details, intent, company_name, institution_summary=""):
        # Handle case where it's a general institutional outreach (no specific job)
        job_context = f"Company: {company_name}\n"
        if job:
            job_context += f"### TARGET ROLE IDENTIFIED:\n{str(job)}\n"
        else:
            job_context += "### FOCUS: Strategic Institutional Partnership & Pipeline Development\n"

        prompt_email = PromptTemplate.from_template(
            """
            ### PERSONA: 
            You are {user_name}, a Senior Head of Corporate Relations at {institution_name} with over 10 years of experience in managing high-stakes campus placements and industrial MOUs. 
            You are NOT an assistant. You are a peer to HR Heads and Talent Acquisition Leaders.

            ### EMAIL CONTEXT:
            - Target Company: {company_name}
            - Strategic Focus: {job_context}
            - Institutional Strength: {institution_summary}
            - Student Technical Proof: {link_list}
            - Intent: {intent}
            - Recipient: {recipient_name}, {recipient_designation}

            ### INSTRUCTION:
            Write a MASTERFUL executive cold email. It must sound seasoned, confident, and partnership-oriented. 
            Avoid all entry-level cliches like "I am writing to..." or "I hope you are doing well." 
            
            Structure:
            1. **The Lead**: Start with a professional observation about their company's recent direction or the industry landscape.
            2. **The Connection**: Briefly link their growth to your institution's specific talent pipeline. Mention your 10 years of experience in shaping students for world-class firms.
            3. **The 'Killer' Fact**: Highlight a specific technical capability your students have (referencing {link_list}) that solves their current hiring bottleneck.
            4. **The Proposal**: Suggest a specific high-level engagement (e.g., "Let's discuss a structured campus hiring roadmap" or "A quick executive briefing on our upcoming talent cohort").
            5. **Sign-off**: Executive, brief, and professional.

            Tone: Highly professional, direct, and authoritative. 
            ### MASTER DRAFT (NO PREAMBLE):
            """
        )
        chain_email = prompt_email | self.llm
        res = chain_email.invoke({
            "job_context": job_context, 
            "company_name": company_name,
            "link_list": links,
            "user_name": user_details.get("name"),
            "user_designation": user_details.get("designation"),
            "institution_name": user_details.get("institution_name"),
            "institution_url": user_details.get("institution_url"),
            "institution_summary": institution_summary,
            "recipient_name": recipient_details.get("name"),
            "recipient_designation": recipient_details.get("designation"),
            "intent": intent
        })
        return res.content

if __name__ == "__main__":
    print(os.getenv("GROQ_API_KEY"))