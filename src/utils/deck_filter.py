def filter_decks(decks, budget_query, tags_query, salt_query):
    """
    Filters a list of decks based on budget and tag criteria.

    Returns:
        The first matching deck dictionary, or None if no match is found.
    """
    for deck in decks:
        is_match = True

        # 1. Filter by budget (if provided)
        if budget_query:
            price = deck.get('price', float('inf'))
            budget_match = False
            if "-" in budget_query:
                min_b, max_b = map(float, budget_query.split('-'))
                if min_b <= price <= max_b: budget_match = True
            elif ">" in budget_query:
                min_b = float(budget_query.replace('>', ''))
                if price > min_b: budget_match = True
            elif "<" in budget_query:
                max_b = float(budget_query.replace('<', ''))
                if price <= max_b: budget_match = True
            else:  # A single number is treated as max budget
                max_b = float(budget_query)
                if price <= max_b: budget_match = True

            if not budget_match:
                is_match = False

        # 2. Filter by tags (if provided and still a match)
        if is_match and tags_query:
            search_tags = [t.strip() for t in tags_query.split(',') if t.strip()]
            deck_tags_lower = [t.lower() for t in deck.get("tags", [])]
            if not all(any(search_tag in deck_tag for deck_tag in deck_tags_lower) for search_tag in search_tags):
                is_match = False

        # 3. Filter by salt score
        if is_match and salt_query:
            salt_match = False
            salt = deck.get('salt', 30.00)
            if "-" in salt_query:
                min_s, max_s = map(float, salt_query.split('-'))
                if min_s <= salt <= max_s: salt_match = True
            elif ">" in salt_query:
                min_s = float(salt_query.replace('>', ''))
                if salt > min_s: salt_match = True
            elif "<" in salt_query:
                max_s = float(salt_query.replace('<', ''))
                if salt <= max_s: salt_match = True
            else:  # A single number is treated as max salt score
                max_s = float(salt_query)
                if salt <= max_s: salt_match = True

            if not salt_match:
                is_match = False


        # If all active filters passed, we found our deck
        if is_match:
            return deck

    return None # No deck found