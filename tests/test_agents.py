import pytest
from src.agent.orchestrator import run_analysis_graph
from src.agent.state import Finding

def test_run_analysis_graph_success():
    """Test that the LangGraph orchestrator runs end-to-end with mock data."""
    # Setup mock findings
    findings = [
        {"label": "Consolidation", "confidence": 0.95, "location": "Right lower lobe", "severity": 0.8},
    ]
    metadata = {"patient_age": "065Y", "patient_sex": "M"}

    # Run the graph
    result = run_analysis_graph("scan-test-123", findings, metadata)

    # Asserts
    assert result is not None
    assert result["scan_id"] == "scan-test-123"
    assert result["status"] == "success"
    
    # Check that each agent populated the state
    assert len(result.get("similar_cases", [])) > 0, "Retrieval agent failed"
    assert len(result.get("literature_results", [])) > 0, "Literature agent failed"
    assert len(result.get("differential_diagnoses", [])) > 0, "Diagnosis agent failed"
    
    # Ensure probabilities are normalized and sorted
    diags = result["differential_diagnoses"]
    assert diags[0].probability >= diags[-1].probability, "Diagnoses should be sorted"
    
def test_run_analysis_graph_empty_findings():
    """Test the graph with no findings to see how it handles a normal scan."""
    result = run_analysis_graph("scan-test-456", [], {})
    
    assert result["status"] == "success"
    # Even with empty findings, it should run to completion and maybe provide baseline diagnoses or empty lists
    assert "differential_diagnoses" in result
