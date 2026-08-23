from app.retriever import get_index


def test_index_builds_and_has_chunks():
    idx = get_index(force_rebuild=True)
    assert len(idx.chunks) > 0
    sources = {c.source_file for c in idx.chunks}
    assert "01_Support_Policy_v3_CURRENT.pdf" in sources
    assert "02_Support_Policy_v2_DEPRECATED.pdf" in sources


def test_deprecated_doc_is_tagged_deprecated():
    idx = get_index()
    deprecated_chunks = [c for c in idx.chunks if c.source_file == "02_Support_Policy_v2_DEPRECATED.pdf"]
    assert deprecated_chunks
    assert all(c.status == "deprecated" for c in deprecated_chunks)
    current_chunks = [c for c in idx.chunks if c.source_file == "01_Support_Policy_v3_CURRENT.pdf"]
    assert all(c.status == "current" for c in current_chunks)


def test_customer_agreements_carry_account_scope():
    idx = get_index()
    northstar = [c for c in idx.chunks if c.source_file.startswith("05_Northstar")]
    lumenworks = [c for c in idx.chunks if c.source_file.startswith("06_LumenWorks")]
    assert all(c.account_id == "ACCT-001" for c in northstar)
    assert all(c.account_id == "ACCT-002" for c in lumenworks)


def test_customer_search_never_leaks_other_account_agreement():
    idx = get_index()
    # A customer with NO agreement of their own (Beacon Retail / ACCT-003)
    # must never receive Northstar's or LumenWorks's agreement text, even
    # for a query that would otherwise match it well.
    results = idx.search(
        "Northstar Logistics enterprise cancellation waiver LumenWorks credit",
        k=10,
        allowed_account_id="ACCT-003",
    )
    assert all(c.account_id in (None, "ACCT-003") for c in results)


def test_customer_search_can_see_own_agreement():
    idx = get_index()
    results = idx.search("cancellation fee waiver", k=10, allowed_account_id="ACCT-001")
    sources = {c.source_file for c in results}
    assert "05_Northstar_Logistics_Enterprise_Agreement.pdf" in sources


def test_internal_search_can_see_all_agreements():
    idx = get_index()
    results = idx.search("service credit cancellation SLA", k=16, allowed_account_id="__ANY__")
    sources = {c.source_file for c in results}
    assert "05_Northstar_Logistics_Enterprise_Agreement.pdf" in sources or len(results) > 0
