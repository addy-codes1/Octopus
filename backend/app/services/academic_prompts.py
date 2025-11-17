"""Academic-specific prompt templates for research analysis."""

# Prompt for finding contradictions across papers
CONTRADICTION_PROMPT = """You are an academic research assistant analyzing multiple papers for contradictions and inconsistencies.

Examine the following excerpts from research papers and identify:
1. Direct contradictions in findings or conclusions
2. Conflicting methodological approaches
3. Disagreements in interpretations
4. Inconsistent definitions or terminology

For each contradiction found:
- State the specific contradiction clearly
- Cite which papers/sources conflict (using [1], [2], etc.)
- Explain the nature of the disagreement
- Note any potential reasons for the contradiction (different sample sizes, methodologies, contexts)

Context from papers:
{context}

User's question about contradictions:
{question}

Provide a structured analysis of contradictions found:"""


# Prompt for comparing methodologies
METHODOLOGY_COMPARISON_PROMPT = """You are an academic research assistant specializing in methodology analysis.

Compare and contrast the research methodologies used in the following paper excerpts:

For each paper, identify:
1. Research design (experimental, observational, qualitative, quantitative, mixed)
2. Sample size and selection criteria
3. Data collection methods
4. Analysis techniques
5. Limitations acknowledged

Then provide:
- A comparative table or summary
- Strengths and weaknesses of each approach
- Recommendations for which methodology might be most appropriate for different research questions

Context from papers:
{context}

User's question about methodologies:
{question}

Provide a detailed methodological comparison:"""


# Prompt for identifying research gaps
RESEARCH_GAPS_PROMPT = """You are an academic research assistant helping identify research gaps and future directions.

Analyze the following paper excerpts to identify:
1. Explicitly mentioned limitations or future research directions
2. Questions raised but not answered
3. Populations or contexts not studied
4. Methodological improvements suggested
5. Theoretical gaps or underexplored areas

For each gap identified:
- Describe the gap clearly
- Cite the relevant source(s)
- Explain why this gap is significant
- Suggest potential research questions to address it

Context from papers:
{context}

User's question about research gaps:
{question}

Provide a comprehensive analysis of research gaps:"""


# Prompt for synthesizing findings
SYNTHESIS_PROMPT = """You are an academic research assistant helping synthesize findings across multiple studies.

Analyze the following paper excerpts and provide:
1. Common themes and patterns
2. Areas of consensus
3. Unique or novel findings from each paper
4. Overall trends in the research

Structure your synthesis to:
- Group related findings together
- Highlight the strength of evidence (how many papers support each finding)
- Note any contextual factors that affect generalizability
- Provide a coherent narrative that integrates the findings

Context from papers:
{context}

User's question:
{question}

Provide a comprehensive synthesis:"""


# Prompt for explaining complex concepts
CONCEPT_EXPLANATION_PROMPT = """You are an academic research assistant helping explain complex research concepts.

Based on the following paper excerpts, provide a clear explanation that:
1. Defines key terms and concepts
2. Explains the theoretical framework
3. Shows how concepts relate to each other
4. Uses examples from the papers
5. Distinguishes between different uses or interpretations of terms

Make the explanation accessible while maintaining academic rigor.

Context from papers:
{context}

User's question:
{question}

Provide a clear, well-cited explanation:"""


# Prompt for statistical analysis comparison
STATISTICS_COMPARISON_PROMPT = """You are an academic research assistant specializing in statistical analysis.

Compare the statistical approaches and findings in the following paper excerpts:
1. Statistical tests used
2. Effect sizes reported
3. Significance levels
4. Confidence intervals
5. Sample sizes and power

Evaluate:
- Appropriateness of statistical methods
- Comparability of results across studies
- Potential issues with interpretation

Context from papers:
{context}

User's question about statistics:
{question}

Provide a detailed statistical comparison:"""


def get_academic_prompt(prompt_type: str, context: str, question: str) -> str:
    """Get a formatted academic prompt based on type."""
    prompts = {
        "contradiction": CONTRADICTION_PROMPT,
        "methodology": METHODOLOGY_COMPARISON_PROMPT,
        "gaps": RESEARCH_GAPS_PROMPT,
        "synthesis": SYNTHESIS_PROMPT,
        "concept": CONCEPT_EXPLANATION_PROMPT,
        "statistics": STATISTICS_COMPARISON_PROMPT,
    }

    template = prompts.get(prompt_type, SYNTHESIS_PROMPT)
    return template.format(context=context, question=question)


def detect_academic_intent(question: str) -> str:
    """Detect the type of academic analysis requested."""
    question_lower = question.lower()

    if any(word in question_lower for word in ["contradict", "conflict", "disagree", "inconsistent", "oppose"]):
        return "contradiction"

    if any(word in question_lower for word in ["method", "methodology", "approach", "design", "procedure"]):
        return "methodology"

    if any(word in question_lower for word in ["gap", "limitation", "future", "missing", "unexplored"]):
        return "gaps"

    if any(word in question_lower for word in ["statistic", "significance", "p-value", "effect size", "sample size"]):
        return "statistics"

    if any(word in question_lower for word in ["explain", "define", "what is", "meaning", "concept"]):
        return "concept"

    # Default to synthesis for general questions
    return "synthesis"
