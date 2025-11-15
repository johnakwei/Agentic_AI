"""
Test and Evaluation Suite for ArXiv Quantum Physics Agent
==========================================================

This script validates all components and generates evaluation metrics.
Run this before submitting to ensure everything works correctly.
"""

import asyncio
import logging
from typing import List, Dict, Any
from arxiv_quantum_agent import (
    fetch_arxiv_papers,
    extract_latex_equations,
    calculate_relevance_score,
    QuantumPhysicsAgentSystem,
    AgentEvaluator
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TestSuite:
    """Comprehensive test suite for the agent system"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, condition: bool, message: str = ""):
        """Record test result"""
        if condition:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
        
        result = f"{status} - {name}"
        if message:
            result += f": {message}"
        
        self.results.append(result)
        print(result)
        return condition
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        total = self.passed + self.failed
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%")
        print("=" * 80)


async def test_custom_tools():
    """Test all custom tools"""
    print("\n" + "=" * 80)
    print("TESTING CUSTOM TOOLS")
    print("=" * 80)
    
    suite = TestSuite()
    
    # Test 1: ArXiv paper fetching
    print("\n📡 Testing ArXiv API integration...")
    papers = fetch_arxiv_papers(query="quantum computing", max_results=5, days_back=30)
    suite.test(
        "fetch_arxiv_papers - returns data",
        len(papers) > 0,
        f"Retrieved {len(papers)} papers"
    )
    
    if papers:
        paper = papers[0]
        suite.test(
            "fetch_arxiv_papers - has title",
            'title' in paper and len(paper['title']) > 0
        )
        suite.test(
            "fetch_arxiv_papers - has authors",
            'authors' in paper and len(paper['authors']) > 0
        )
        suite.test(
            "fetch_arxiv_papers - has abstract",
            'abstract' in paper and len(paper['abstract']) > 0
        )
        suite.test(
            "fetch_arxiv_papers - has arxiv_url",
            'arxiv_url' in paper and 'arxiv.org' in paper['arxiv_url']
        )
    
    # Test 2: LaTeX equation extraction
    print("\n🔢 Testing LaTeX equation extraction...")
    test_text = """
    The Hamiltonian is given by $H = \\sum_i E_i |i\\rangle\\langle i|$.
    The wave function satisfies $$\\Psi(x,t) = \\sum_n c_n \\phi_n(x) e^{-iE_nt/\\hbar}$$.
    """
    equations = extract_latex_equations(test_text)
    suite.test(
        "extract_latex_equations - finds equations",
        len(equations) > 0,
        f"Found {len(equations)} equations"
    )
    suite.test(
        "extract_latex_equations - finds Hamiltonian",
        any("H =" in eq for eq in equations)
    )
    
    # Test 3: Relevance scoring
    print("\n⭐ Testing relevance scoring...")
    test_paper = {
        'title': 'Quantum Entanglement in Superconducting Qubits',
        'abstract': 'We study entanglement generation in quantum computing systems.'
    }
    score = calculate_relevance_score(test_paper, ['entanglement', 'quantum'])
    suite.test(
        "calculate_relevance_score - returns valid score",
        0 <= score <= 100,
        f"Score: {score}"
    )
    suite.test(
        "calculate_relevance_score - recognizes relevant keywords",
        score > 30,
        f"Score {score} indicates keyword matches"
    )
    
    suite.print_summary()
    return suite.passed, suite.failed


async def test_agent_system(api_key: str):
    """Test the complete multi-agent system"""
    print("\n" + "=" * 80)
    print("TESTING MULTI-AGENT SYSTEM")
    print("=" * 80)
    
    suite = TestSuite()
    
    # Initialize system
    print("\n🤖 Initializing agent system...")
    try:
        system = QuantumPhysicsAgentSystem(api_key)
        suite.test("System initialization", True, "System created successfully")
    except Exception as e:
        suite.test("System initialization", False, f"Error: {str(e)}")
        suite.print_summary()
        return suite.passed, suite.failed
    
    # Test memory/preferences
    print("\n🧠 Testing memory and preferences...")
    original_interests = system.user_preferences['research_interests'].copy()
    new_interests = ['quantum machine learning', 'NISQ algorithms']
    system.update_user_preferences(new_interests)
    suite.test(
        "update_user_preferences",
        system.user_preferences['research_interests'] == new_interests,
        "Preferences updated successfully"
    )
    
    # Test query processing
    print("\n🔍 Testing query processing...")
    print("   This may take 15-30 seconds as the agent pipeline runs...")
    query = "quantum error correction"
    
    try:
        result = await system.process_research_query(query)
        
        suite.test(
            "process_research_query - returns result",
            result is not None
        )
        suite.test(
            "process_research_query - has summary",
            'summary' in result and len(result['summary']) > 0,
            f"Summary length: {len(result.get('summary', ''))}"
        )
        suite.test(
            "process_research_query - has session_id",
            'session_id' in result
        )
        suite.test(
            "process_research_query - has metrics",
            'metrics' in result
        )
        
        # Check metrics
        if 'metrics' in result:
            metrics = result['metrics']
            suite.test(
                "Metrics - tracks agent calls",
                metrics.get('total_agent_calls', 0) > 0,
                f"Agent calls: {metrics.get('total_agent_calls', 0)}"
            )
            suite.test(
                "Metrics - tracks processing time",
                metrics.get('total_processing_time_seconds', 0) > 0,
                f"Time: {metrics.get('total_processing_time_seconds', 0)}s"
            )
            suite.test(
                "Metrics - has success rate",
                'success_rate_percent' in metrics,
                f"Success rate: {metrics.get('success_rate_percent', 0)}%"
            )
    
    except Exception as e:
        suite.test("process_research_query", False, f"Error: {str(e)}")
    
    suite.print_summary()
    return suite.passed, suite.failed


async def test_evaluation_framework():
    """Test the agent evaluation framework"""
    print("\n" + "=" * 80)
    print("TESTING EVALUATION FRAMEWORK")
    print("=" * 80)
    
    suite = TestSuite()
    evaluator = AgentEvaluator()
    
    # Test retrieval quality evaluation
    print("\n📊 Testing retrieval quality evaluation...")
    test_papers = [
        {'title': 'Quantum Computing', 'abstract': 'Study of quantum computers'},
        {'title': 'Classical Computing', 'abstract': 'Study of classical computers'},
        {'title': 'Quantum Algorithms', 'abstract': 'New quantum algorithms'}
    ]
    keywords = ['quantum', 'qubit']
    quality = evaluator.evaluate_retrieval_quality(test_papers, keywords)
    suite.test(
        "evaluate_retrieval_quality - returns score",
        0 <= quality <= 100,
        f"Quality score: {quality}%"
    )
    suite.test(
        "evaluate_retrieval_quality - detects relevant papers",
        quality > 50,
        "Correctly identifies relevant papers"
    )
    
    # Test summary completeness evaluation
    print("\n📝 Testing summary completeness evaluation...")
    test_summary = """
    Executive Summary: This analysis covers quantum error correction.
    
    Top Papers:
    1. Paper on surface codes
    2. Paper on topological codes
    
    Trends: Increasing focus on fault-tolerant architectures
    
    Recommendations: Read papers on stabilizer codes
    """
    completeness = evaluator.evaluate_summary_completeness(test_summary)
    suite.test(
        "evaluate_summary_completeness - checks structure",
        isinstance(completeness, dict),
        f"Found {sum(completeness.values())} required sections"
    )
    suite.test(
        "evaluate_summary_completeness - finds executive summary",
        completeness.get('executive_summary', False)
    )
    suite.test(
        "evaluate_summary_completeness - finds top papers",
        completeness.get('top_papers', False)
    )
    
    # Test performance evaluation
    print("\n⚡ Testing performance evaluation...")
    test_metrics = {
        'average_processing_time_seconds': 10.5,
        'success_rate_percent': 95.0
    }
    performance = evaluator.evaluate_performance(test_metrics)
    suite.test(
        "evaluate_performance - returns ratings",
        isinstance(performance, dict) and len(performance) > 0
    )
    suite.test(
        "evaluate_performance - rates speed",
        'speed' in performance
    )
    suite.test(
        "evaluate_performance - rates reliability",
        'reliability' in performance
    )
    
    suite.print_summary()
    return suite.passed, suite.failed


async def run_all_tests():
    """Run complete test suite"""
    print("\n" + "=" * 80)
    print("ARXIV QUANTUM PHYSICS AGENT - COMPLETE TEST SUITE")
    print("=" * 80)
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Custom Tools
    passed, failed = await test_custom_tools()
    total_passed += passed
    total_failed += failed
    
    # Test 2: Agent System (requires API key)
    import os
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        passed, failed = await test_agent_system(api_key)
        total_passed += passed
        total_failed += failed
    else:
        print("\n⚠️  Skipping agent system tests - GEMINI_API_KEY not set")
        print("   Set your API key to run full tests:")
        print("   export GEMINI_API_KEY='your-key-here'")
    
    # Test 3: Evaluation Framework
    passed, failed = await test_evaluation_framework()
    total_passed += passed
    total_failed += failed
    
    # Final Summary
    print("\n" + "=" * 80)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 80)
    total = total_passed + total_failed
    print(f"Total Tests Run: {total}")
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"Overall Success Rate: {(total_passed/total*100):.1f}%")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! Agent is ready for submission!")
    elif total_failed <= 2:
        print("\n✅ Most tests passed. Minor issues detected.")
    else:
        print("\n⚠️  Multiple test failures detected. Please review errors.")
    
    print("=" * 80)
    
    return total_passed, total_failed


async def generate_evaluation_report():
    """Generate a comprehensive evaluation report"""
    print("\n" + "=" * 80)
    print("GENERATING EVALUATION REPORT")
    print("=" * 80)
    
    import os
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠️  Cannot generate full report without API key")
        print("   Set GEMINI_API_KEY environment variable")
        return
    
    print("\n📊 Running complete agent workflow for evaluation...")
    system = QuantumPhysicsAgentSystem(api_key)
    
    # Test queries
    test_queries = [
        "quantum error correction",
        "topological quantum computing",
        "superconducting qubits"
    ]
    
    results = []
    for query in test_queries:
        print(f"\n🔍 Processing: '{query}'")
        try:
            result = await system.process_research_query(query)
            results.append({
                'query': query,
                'success': True,
                'metrics': result['metrics']
            })
        except Exception as e:
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })
    
    # Generate report
    print("\n" + "=" * 80)
    print("📋 EVALUATION REPORT")
    print("=" * 80)
    
    successful = sum(1 for r in results if r['success'])
    print(f"\n✅ Successful Queries: {successful}/{len(test_queries)}")
    
    if successful > 0:
        # Calculate average metrics
        avg_time = sum(
            r['metrics']['average_processing_time_seconds']
            for r in results if r['success']
        ) / successful
        
        avg_success_rate = sum(
            r['metrics']['success_rate_percent']
            for r in results if r['success']
        ) / successful
        
        print(f"\n⏱️  Average Processing Time: {avg_time:.2f} seconds")
        print(f"📈 Average Success Rate: {avg_success_rate:.1f}%")
        
        # Evaluate performance
        evaluator = AgentEvaluator()
        performance = evaluator.evaluate_performance({
            'average_processing_time_seconds': avg_time,
            'success_rate_percent': avg_success_rate
        })
        
        print(f"\n🏆 Performance Ratings:")
        for metric, rating in performance.items():
            print(f"   {metric.capitalize()}: {rating}")
    
    print("\n" + "=" * 80)
    print("Report generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║           ArXiv Quantum Physics Agent - Test & Evaluation Suite          ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run tests
    asyncio.run(run_all_tests())
    
    # Generate evaluation report
    print("\n" + "=" * 80)
    response = input("\nGenerate detailed evaluation report? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(generate_evaluation_report())
    
    print("\n✅ Testing complete!")
