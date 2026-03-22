import requests


def find_duplicates(d, items):
    """Find duplicate items in a list."""
    result = []
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == items[j] and i != j:
                result.append(items[i])
    return result


def fetch_user(user_id):
    """Fetch user from API."""
    try:
        response = requests.get(f"/api/users/{user_id}")
        return response.json()
    except Exception:
        raise ValueError("Failed to fetch user")
