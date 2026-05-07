import base64


def encode_id(id: int) -> str:
    """Encode a numeric ID to a Base64 URL-safe string."""
    raw = f"CVOTE:{id}:GH"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip('=')


def decode_id(encoded: str) -> int:
    """Decode a Base64 string back to a numeric ID."""
    padding = 4 - len(encoded) % 4
    if padding != 4:
        encoded += '=' * padding
    raw = base64.urlsafe_b64decode(encoded.encode()).decode()
    parts = raw.split(':')
    if len(parts) != 3 or parts[0] != 'CVOTE' or parts[2] != 'GH':
        raise ValueError('Invalid encoded ID')
    return int(parts[1])