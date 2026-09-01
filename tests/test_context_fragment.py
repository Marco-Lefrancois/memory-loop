import pytest
from src.engine.context.fragment import ContextFragment, ContextAssemblyEngine, MAX_FRAGMENT_TOKENS


def test_context_fragment_creation_and_hash():
    frag = ContextFragment(
        fragment_id="directives_ssot",
        fragment_type="directive",
        content="# AGENTS.md Constitution\nRule 1: Never modify client code."
    )
    assert frag.token_count > 0
    assert len(frag.sha256) == 64
    frag.validate()


def test_context_fragment_overflow_raises_error():
    giant_text = "word " * 15000  # ~15 000 tokens
    frag = ContextFragment(
        fragment_id="giant_overflow",
        fragment_type="knowledge",
        content=giant_text
    )
    with pytest.raises(ValueError, match="CONTEXT OVERFLOW"):
        frag.validate()


def test_context_assembly_engine_ordering():
    engine = ContextAssemblyEngine()
    
    frag_turn = ContextFragment("turn_1", "turn", "User said hello")
    frag_directive = ContextFragment("dir_1", "directive", "System prompt")
    frag_doc = ContextFragment("doc_1", "knowledge", "Architecture doc")
    
    # Ajouter dans un ordre désordonné
    engine.add_fragment(frag_turn)
    engine.add_fragment(frag_doc)
    engine.add_fragment(frag_directive)
    
    rendered = engine.render_prompt_context()
    
    # Vérifier que directive apparaît avant knowledge, qui apparaît avant turn
    pos_dir = rendered.find("TYPE: directive")
    pos_doc = rendered.find("TYPE: knowledge")
    pos_turn = rendered.find("TYPE: turn")
    
    assert pos_dir < pos_doc < pos_turn
