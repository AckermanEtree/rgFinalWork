def check_sensitive(text):
    """Basic sensitive word checker stub."""
    bad_words = []
    for word in bad_words:
        if word in text:
            return False, f"contains sensitive word: {word}"
    return True, "ok"
