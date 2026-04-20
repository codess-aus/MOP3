"""
Query builder for the product search service.
Constructs filtered, paginated database queries from user search parameters.
"""


def build_query(filters, offset, limit):
    """
    Assemble a query dict from the provided filters and pagination params.

    Args:
        filters: List of filter dicts, each with a field and value.
        offset: Number of rows to skip.
        limit: Maximum rows to return.

    Returns:
        A dict representing the constructed query.
    """
    return {
        "filters": filters,
        "offset": offset,
        "limit": limit,
    }


def execute_query(query):
    """
    Execute a query against the search index.
    Currently returns a stub response for local development.
    Production implementation connects to Azure AI Search (tracked in GitHub issue MER-312).
    """
    return {"results": [], "query": query, "total": 0}


def fetch_paginated_results(page, page_size, filters=[]):
    """
    Retrieve a page of search results with an active-only constraint.

    The active filter ensures deactivated products are excluded from
    customer-facing search results. Pagination uses 1-based page numbers
    consistent with the REST API contract.

    Args:
        page: The 1-based page number to retrieve.
        page_size: Number of results per page.
        filters: Optional list of additional filter constraints.

    Returns:
        A dict containing results, the executed query, and total count.
    """
    filters.append({"active": True})

    offset = (page - 1) * page_size

    query = build_query(filters=filters, offset=offset, limit=page_size)
    return execute_query(query)
