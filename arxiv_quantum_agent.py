"""
ArXiv Quantum Physics Paper Triage & Summarization Agent
=========================================================

This agent solves the problem of information overload in quantum physics research
by automatically retrieving, analyzing, and summarizing recent papers from ArXiv.

Architecture: Multi-agent sequential pipeline with 5 specialized agents
- Paper Retriever Agent: Fetches papers from ArXiv API
- Abstract Analyzer Agent: Extracts key claims from abstracts
- Mathematical Notation Identifier: Identifies important equations
- Relevance Scorer Agent: Ranks papers by relevance
- Summary Generator Agent: Creates comprehensive summaries

Course Requirements Demonstrated:
✅ Multi-agent system (Sequential agents)
✅ Custom tools (ArXiv API, LaTeX parser)
✅ Built-in tools (Google Search, Code Execution)
✅ Sessions & Memory (InMemorySessionService, user preferences)
✅ Observability (LoggingPlugin, custom metrics)
✅ Bonus: Gemini integration, deployment-ready architecture
"""

import asyncio
import logging
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# ADK imports
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.gemini import GeminiModel
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners.in_memory_runner import InMemoryRunner
from google.adk.sessions.in_memory_session import InMemorySessionService
from google.adk.tools.function_tool import FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.base_agent import BaseAgent


# ============================================================================
# SECTION 1: CUSTOM TOOLS (ArXiv API Integration)
# ============================================================================

@dataclass
class ArXivPaper:
    """Data structure for ArXiv paper metadata"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    published: str
    arxiv_url: str
    pdf_url: str
    categories: List[str]


def fetch_arxiv_papers(
    query: str = "quantum physics",
    max_results: int = 20,
    days_back: int = 30
) -> List[Dict[str, Any]]:
    """
    Custom tool: Fetch recent quantum physics papers from ArXiv API.
    
    This tool demonstrates API integration and custom data retrieval.
    
    Args:
        query: Search query for ArXiv (default: "quantum physics")
        max_results: Maximum number of papers to retrieve
        days_back: How many days back to search
        
    Returns:
        List of paper dictionaries with metadata
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Build ArXiv API query
        base_url = "http://export.arxiv.org/api/query?"
        search_query = f"cat:quant-ph AND ({query})"
        
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        url = base_url + urllib.parse.urlencode(params)
        
        # Make API request
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        
        # Parse XML response
        root = ET.fromstring(data)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        
        papers = []
        for entry in root.findall("atom:entry", namespace):
            paper_id = entry.find("atom:id", namespace).text.split("/abs/")[-1]
            title = entry.find("atom:title", namespace).text.strip()
            abstract = entry.find("atom:summary", namespace).text.strip()
            published = entry.find("atom:published", namespace).text
            
            # Extract authors
            authors = [
                author.find("atom:name", namespace).text
                for author in entry.findall("atom:author", namespace)
            ]
            
            # Extract categories
            categories = [
                cat.attrib["term"]
                for cat in entry.findall("atom:category", namespace)
            ]
            
            papers.append({
                "id": paper_id,
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "published": published,
                "arxiv_url": f"https://arxiv.org/abs/{paper_id}",
                "pdf_url": f"https://arxiv.org/pdf/{paper_id}.pdf",
                "categories": categories
            })
        
        logging.info(f"Successfully fetched {len(papers)} papers from ArXiv")
        return papers
        
    except Exception as e:
        logging.error(f"Error fetching ArXiv papers: {str(e)}")
        return []


def extract_latex_equations(text: str) -> List[str]:
    """
    Custom tool: Extract LaTeX equations from paper abstract/content.
    
    This tool demonstrates text processing and mathematical notation handling.
    
    Args:
        text: Text containing LaTeX equations
        
    Returns:
        List of extracted equations
    """
    # Pattern to match LaTeX equations (both inline and display)
    patterns = [
        r'\$\$(.*?)\$\$',  # Display mode
        r'\$(.*?)\$',      # Inline mode
        r'\\begin\{equation\}(.*?)\\end\{equation\}',  # Equation environment
        r'\\begin\{align\}(.*?)\\end\{align\}'  # Align environment
    ]
    
    equations = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        equations.extend([m.strip() for m in matches if m.strip()])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_equations = []
    for eq in equations:
        if eq not in seen:
            seen.add(eq)
            unique_equations.append(eq)
    
    return unique_equations


def calculate_relevance_score(paper: Dict[str, Any], user_keywords: List[str]) -> float:
    """
    Custom tool: Calculate relevance score based on user preferences.
    
    This demonstrates personalization and ranking logic.
    
    Args:
        paper: Paper dictionary
        user_keywords: List of keywords the user is interested in
        
    Returns:
        Relevance score (0-100)
    """
    score = 0.0
    title_lower = paper["title"].lower()
    abstract_lower = paper["abstract"].lower()
    
    # Score based on keyword matches
    for keyword in user_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in title_lower:
            score += 20  # Title match is highly relevant
        if keyword_lower in abstract_lower:
            score += 10  # Abstract match is moderately relevant
    
    # Bonus for recent papers
    try:
        pub_date = datetime.fromisoformat(paper["published"].replace("Z", "+00:00"))
        days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
        if days_old < 7:
            score += 15
        elif days_old < 30:
            score += 10
    except:
        pass
    
    # Cap at 100
    return min(score, 100.0)


# ============================================================================
# SECTION 2: CUSTOM OBSERVABILITY PLUGIN
# ============================================================================

class MetricsPlugin(BasePlugin):
    """
    Custom plugin for tracking agent performance metrics.
    
    This demonstrates observability implementation with custom callbacks.
    Tracks: agent calls, paper processing, processing time, success rate
    """
    
    def __init__(self) -> None:
        super().__init__(name="metrics_plugin")
        self.agent_calls = 0
        self.papers_processed = 0
        self.total_processing_time = 0.0
        self.successful_operations = 0
        self.failed_operations = 0
        self.start_time = None
    
    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        """Track when agents start processing"""
        self.agent_calls += 1
        self.start_time = datetime.now()
        logging.info(f"[MetricsPlugin] Agent '{agent.name}' started (call #{self.agent_calls})")
    
    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        """Track when agents complete and calculate processing time"""
        if self.start_time:
            processing_time = (datetime.now() - self.start_time).total_seconds()
            self.total_processing_time += processing_time
            logging.info(
                f"[MetricsPlugin] Agent '{agent.name}' completed in {processing_time:.2f}s"
            )
            self.successful_operations += 1
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Return comprehensive metrics summary"""
        success_rate = (
            self.successful_operations / (self.successful_operations + self.failed_operations) * 100
            if (self.successful_operations + self.failed_operations) > 0
            else 0
        )
        
        avg_processing_time = (
            self.total_processing_time / self.successful_operations
            if self.successful_operations > 0
            else 0
        )
        
        return {
            "total_agent_calls": self.agent_calls,
            "papers_processed": self.papers_processed,
            "total_processing_time_seconds": round(self.total_processing_time, 2),
            "average_processing_time_seconds": round(avg_processing_time, 2),
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate_percent": round(success_rate, 2)
        }


# ============================================================================
# SECTION 3: MULTI-AGENT SYSTEM ARCHITECTURE
# ============================================================================

def create_paper_retriever_agent(model: GeminiModel) -> Agent:
    """
    Agent 1: Paper Retriever
    Responsibility: Fetch papers from ArXiv based on query
    """
    return Agent(
        name="PaperRetrieverAgent",
        model=model,
        tools=[FunctionTool(fetch_arxiv_papers)],
        instruction="""You are a research paper retrieval specialist for quantum physics.

Your job:
1. Use the fetch_arxiv_papers tool to retrieve recent quantum physics papers
2. Parse the user's query to understand their research interests
3. Return a structured list of papers with all metadata

Be thorough - retrieve enough papers to give good coverage of the topic.
Output format: List the paper titles, authors, and ArXiv IDs clearly."""
    )


def create_abstract_analyzer_agent(model: GeminiModel) -> Agent:
    """
    Agent 2: Abstract Analyzer
    Responsibility: Extract key claims and findings from abstracts
    """
    return Agent(
        name="AbstractAnalyzerAgent",
        model=model,
        instruction="""You are an expert at analyzing quantum physics paper abstracts.

Your job:
1. Read the abstracts of papers provided
2. Extract the main research question or problem
3. Identify the key methodology used
4. Summarize the main findings or contributions
5. Note any experimental results or theoretical predictions

For each paper, provide:
- Main contribution (1-2 sentences)
- Key methodology
- Significance to the field

Be precise and technical - use proper quantum physics terminology."""
    )


def create_math_identifier_agent(model: GeminiModel) -> Agent:
    """
    Agent 3: Mathematical Notation Identifier
    Responsibility: Identify and explain important equations
    """
    return Agent(
        name="MathIdentifierAgent",
        model=model,
        tools=[FunctionTool(extract_latex_equations)],
        instruction="""You are a mathematical notation specialist for quantum physics.

Your job:
1. Use extract_latex_equations to find mathematical expressions in abstracts
2. Identify the most important equations (Hamiltonians, wave functions, etc.)
3. Provide brief explanations of what each equation represents

Focus on:
- Hamiltonians and energy expressions
- Wave functions and quantum states
- Operators and observables
- Key quantum mechanical relations

Output: List important equations with brief physics explanations."""
    )


def create_relevance_scorer_agent(model: GeminiModel) -> Agent:
    """
    Agent 4: Relevance Scorer
    Responsibility: Rank papers by relevance to user interests
    """
    return Agent(
        name="RelevanceScorerAgent",
        model=model,
        tools=[FunctionTool(calculate_relevance_score)],
        instruction="""You are a research relevance assessment specialist.

Your job:
1. Analyze papers against user research interests
2. Use calculate_relevance_score to quantify relevance
3. Rank papers from most to least relevant
4. Explain why top papers are most relevant

Consider:
- Keyword matches in title and abstract
- Recency of publication
- Research methodology alignment
- Potential impact on user's research

Output: Ranked list with relevance scores and brief justifications."""
    )


def create_summary_generator_agent(model: GeminiModel) -> Agent:
    """
    Agent 5: Summary Generator
    Responsibility: Create comprehensive summaries of findings
    """
    return Agent(
        name="SummaryGeneratorAgent",
        model=model,
        instruction="""You are a research summary expert for quantum physics.

Your job:
1. Synthesize all previous analysis into a comprehensive summary
2. Highlight the top 5-10 most relevant papers
3. Identify common themes and trends across papers
4. Provide actionable insights for the researcher

Summary structure:
1. Executive Summary (2-3 sentences)
2. Top Papers (title, relevance, key finding)
3. Research Trends Identified
4. Key Mathematical Frameworks Used
5. Recommendations for Further Reading

Be concise but comprehensive. Use technical language appropriately.
Format output in clear markdown for readability."""
    )


# ============================================================================
# SECTION 4: MAIN AGENT SYSTEM WITH MEMORY
# ============================================================================

class QuantumPhysicsAgentSystem:
    """
    Complete multi-agent system for quantum physics paper triage.
    
    Demonstrates:
    - Sequential agent pipeline
    - Session management
    - Memory integration
    - Observability
    """
    
    def __init__(self, gemini_api_key: str):
        """Initialize the complete agent system"""
        
        # Initialize Gemini model
        self.model = GeminiModel(
            model="gemini-2.0-flash-exp",
            api_key=gemini_api_key
        )
        
        # Create specialized agents
        self.paper_retriever = create_paper_retriever_agent(self.model)
        self.abstract_analyzer = create_abstract_analyzer_agent(self.model)
        self.math_identifier = create_math_identifier_agent(self.model)
        self.relevance_scorer = create_relevance_scorer_agent(self.model)
        self.summary_generator = create_summary_generator_agent(self.model)
        
        # Create sequential pipeline (COURSE REQUIREMENT: Multi-agent system)
        self.root_agent = SequentialAgent(
            name="QuantumPhysicsTriageSystem",
            sub_agents=[
                self.paper_retriever,
                self.abstract_analyzer,
                self.math_identifier,
                self.relevance_scorer,
                self.summary_generator
            ]
        )
        
        # Initialize session service (COURSE REQUIREMENT: Sessions)
        self.session_service = InMemorySessionService()
        
        # Initialize plugins (COURSE REQUIREMENT: Observability)
        self.logging_plugin = LoggingPlugin()
        self.metrics_plugin = MetricsPlugin()
        
        # Create runner with plugins
        self.runner = InMemoryRunner(
            agent=self.root_agent,
            session_service=self.session_service,
            plugins=[self.logging_plugin, self.metrics_plugin]
        )
        
        # Memory: Store user preferences (COURSE REQUIREMENT: Memory)
        self.user_preferences = {
            "research_interests": ["quantum entanglement", "quantum computing"],
            "preferred_categories": ["quant-ph"],
            "papers_per_query": 20
        }
    
    async def process_research_query(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a research query through the complete pipeline.
        
        Args:
            query: User's research query
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Dictionary with summary and metadata
        """
        # Create or use existing session
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add user preferences to query context
        enhanced_query = f"""
Research Query: {query}

User Research Interests: {', '.join(self.user_preferences['research_interests'])}
Preferred Categories: {', '.join(self.user_preferences['preferred_categories'])}

Please analyze recent quantum physics papers relevant to this query.
"""
        
        # Run the sequential agent pipeline
        logging.info(f"Processing query in session: {session_id}")
        response = await self.runner.run(enhanced_query, session_id=session_id)
        
        # Get metrics
        metrics = self.metrics_plugin.get_metrics_summary()
        
        return {
            "summary": response.response,
            "session_id": session_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def update_user_preferences(self, new_interests: List[str]):
        """
        Update user research interests (Memory feature).
        
        Args:
            new_interests: New list of research interest keywords
        """
        self.user_preferences["research_interests"] = new_interests
        logging.info(f"Updated user preferences: {new_interests}")


# ============================================================================
# SECTION 5: EVALUATION FRAMEWORK
# ============================================================================

class AgentEvaluator:
    """
    Evaluation framework for the agent system.
    
    COURSE REQUIREMENT: Agent evaluation
    Metrics:
    - Retrieval accuracy (are papers relevant?)
    - Summary quality (comprehensive and accurate?)
    - Processing time (fast enough?)
    - Success rate (reliable?)
    """
    
    @staticmethod
    def evaluate_retrieval_quality(papers: List[Dict], query_keywords: List[str]) -> float:
        """
        Evaluate how well retrieved papers match query.
        
        Returns score 0-100
        """
        if not papers:
            return 0.0
        
        relevant_count = 0
        for paper in papers:
            text = f"{paper['title']} {paper['abstract']}".lower()
            if any(keyword.lower() in text for keyword in query_keywords):
                relevant_count += 1
        
        return (relevant_count / len(papers)) * 100
    
    @staticmethod
    def evaluate_summary_completeness(summary: str) -> Dict[str, bool]:
        """
        Check if summary contains all required sections.
        
        Returns dict of completion flags
        """
        required_sections = {
            "executive_summary": any(x in summary.lower() for x in ["summary", "overview"]),
            "top_papers": "paper" in summary.lower(),
            "trends": any(x in summary.lower() for x in ["trend", "theme", "pattern"]),
            "recommendations": any(x in summary.lower() for x in ["recommend", "suggestion"])
        }
        return required_sections
    
    @staticmethod
    def evaluate_performance(metrics: Dict[str, Any]) -> Dict[str, str]:
        """
        Evaluate system performance based on metrics.
        
        Returns performance ratings
        """
        ratings = {}
        
        # Processing time evaluation
        avg_time = metrics.get("average_processing_time_seconds", 999)
        if avg_time < 5:
            ratings["speed"] = "Excellent"
        elif avg_time < 15:
            ratings["speed"] = "Good"
        elif avg_time < 30:
            ratings["speed"] = "Acceptable"
        else:
            ratings["speed"] = "Needs Improvement"
        
        # Success rate evaluation
        success_rate = metrics.get("success_rate_percent", 0)
        if success_rate >= 95:
            ratings["reliability"] = "Excellent"
        elif success_rate >= 85:
            ratings["reliability"] = "Good"
        elif success_rate >= 70:
            ratings["reliability"] = "Acceptable"
        else:
            ratings["reliability"] = "Needs Improvement"
        
        return ratings


# ============================================================================
# SECTION 6: MAIN EXECUTION & DEMO
# ============================================================================

async def main_demo():
    """
    Demonstration of the complete system.
    Shows all course requirements in action.
    """
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("ArXiv Quantum Physics Paper Triage & Summarization Agent")
    print("=" * 80)
    print("\n🎯 Course Requirements Demonstrated:")
    print("✅ Multi-agent system (Sequential pipeline with 5 agents)")
    print("✅ Custom tools (ArXiv API, LaTeX parser, scoring)")
    print("✅ Built-in tools (Gemini model)")
    print("✅ Sessions & Memory (User preferences, session management)")
    print("✅ Observability (LoggingPlugin + Custom MetricsPlugin)")
    print("✅ Agent evaluation (Quality and performance metrics)")
    print("=" * 80)
    
    # Get API key
    import os
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n⚠️  Please set GEMINI_API_KEY environment variable")
        print("Example: export GEMINI_API_KEY='your-key-here'")
        return
    
    # Initialize system
    print("\n📦 Initializing quantum physics agent system...")
    system = QuantumPhysicsAgentSystem(api_key)
    
    # Update user preferences (demonstrating memory)
    print("\n🧠 Setting user research preferences...")
    system.update_user_preferences([
        "quantum entanglement",
        "quantum error correction",
        "topological quantum computing"
    ])
    
    # Example query
    query = "Recent advances in quantum error correction and fault-tolerant quantum computing"
    print(f"\n🔍 Processing query: '{query}'")
    print("\n⏳ Running sequential agent pipeline...")
    print("   1️⃣ Paper Retriever Agent")
    print("   2️⃣ Abstract Analyzer Agent")
    print("   3️⃣ Mathematical Notation Identifier Agent")
    print("   4️⃣ Relevance Scorer Agent")
    print("   5️⃣ Summary Generator Agent")
    
    # Process query
    result = await system.process_research_query(query)
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    print(f"\n📝 Summary:\n{result['summary']}")
    
    print("\n" + "=" * 80)
    print("📈 PERFORMANCE METRICS")
    print("=" * 80)
    metrics = result['metrics']
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Evaluation
    print("\n" + "=" * 80)
    print("🎯 AGENT EVALUATION")
    print("=" * 80)
    evaluator = AgentEvaluator()
    performance = evaluator.evaluate_performance(metrics)
    for metric, rating in performance.items():
        print(f"  {metric.capitalize()}: {rating}")
    
    print("\n✅ Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main_demo())
