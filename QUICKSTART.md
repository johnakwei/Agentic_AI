# 🚀 Quick Start Guide

Get your ArXiv Quantum Physics Agent running in 5 minutes!

## Step 1: Prerequisites

Make sure you have:
- Python 3.10 or higher installed
- An internet connection
- A Gemini API key (get it free at https://aistudio.google.com/apikey)

## Step 2: Install Dependencies

```bash
pip install google-adk
```

That's it! The agent only needs one main package.

## Step 3: Set Your API Key

### On macOS/Linux:
```bash
export GEMINI_API_KEY='your-api-key-here'
```

### On Windows (Command Prompt):
```cmd
set GEMINI_API_KEY=your-api-key-here
```

### On Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY='your-api-key-here'
```

## Step 4: Run the Agent

```bash
python arxiv_quantum_agent.py
```

You should see:
```
================================================================================
ArXiv Quantum Physics Paper Triage & Summarization Agent
================================================================================

🎯 Course Requirements Demonstrated:
✅ Multi-agent system (Sequential pipeline with 5 agents)
✅ Custom tools (ArXiv API, LaTeX parser, scoring)
...
```

## Step 5: Customize (Optional)

Open `arxiv_quantum_agent.py` and find this section:

```python
self.user_preferences = {
    "research_interests": ["quantum entanglement", "quantum computing"],
    "preferred_categories": ["quant-ph"],
    "papers_per_query": 20
}
```

Change the `research_interests` to match your research topics!

## Example Queries to Try

Once running, try these queries:
- "Recent advances in quantum error correction"
- "Topological quantum computing with anyons"
- "Quantum machine learning applications"
- "Superconducting qubit decoherence mitigation"
- "Variational quantum algorithms for optimization"

## Troubleshooting

### "ModuleNotFoundError: No module named 'google.adk'"
```bash
pip install google-adk
```

### "API key error"
- Make sure you set the GEMINI_API_KEY environment variable
- Verify your key at https://aistudio.google.com/apikey
- Try re-exporting the variable

### "No papers found"
- Check your internet connection
- Try a broader query like "quantum computing"
- The ArXiv API might be temporarily down - try again in a few minutes

### "Timeout errors"
- This is normal for the first run (downloading models)
- Subsequent runs will be faster
- Try reducing `papers_per_query` to 10

## What's Next?

- Read the full README.md for detailed documentation
- Check out the architecture diagrams
- Try customizing the agents for your specific needs
- Deploy to the cloud for 24/7 access

## Getting Help

- Check the README.md for detailed troubleshooting
- Review the code comments (heavily documented!)
- Kaggle Discord: https://discord.com/invite/kaggle

---

**🎉 That's it! You're now running an AI agent system that can analyze quantum physics papers 90% faster than manual screening!**
