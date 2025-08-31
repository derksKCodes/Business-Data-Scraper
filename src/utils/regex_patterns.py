# Regex patterns for contact information extraction

# Email patterns
EMAIL_PATTERNS = [
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    r'[a-zA-Z0-9._%+-]+\[at\][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    r'[a-zA-Z0-9._%+-]+\(at\)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
]

# Phone number patterns (international formats)
PHONE_PATTERNS = [
    r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    r'(\+?\d{1,3}[-.\s]?)?\(?\d{2}\)?[-.\s]?\d{4}[-.\s]?\d{4}',
    r'(\+?\d{1,3}[-.\s]?)?\(?\d{4}\)?[-.\s]?\d{3}[-.\s]?\d{3}',
    r'(\+?\d{1,3}[-.\s]?)?\(?\d{5}\)?[-.\s]?\d{3}[-.\s]?\d{2}',
    r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
    r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',
    r'\(\d{2}\)\s*\d{4}[-.\s]?\d{4}',
]

# Social media platform patterns
SOCIAL_MEDIA_PATTERNS = {
    'facebook': [
        r'facebook\.com/',
        r'fb\.com/',
        r'fb\.me/',
        r'facebook',
    ],
    'twitter': [
        r'twitter\.com/',
        r't\.co/',
        r'twitter',
        r'x\.com/',
    ],
    'linkedin': [
        r'linkedin\.com/',
        r'linkedin',
        r'lnkd\.in/',
    ],
    'instagram': [
        r'instagram\.com/',
        r'instagr\.am/',
        r'instagram',
    ],
    'youtube': [
        r'youtube\.com/',
        r'youtu\.be/',
        r'youtube',
    ],
    'pinterest': [
        r'pinterest\.com/',
        r'pin\.it/',
        r'pinterest',
    ],
    'tiktok': [
        r'tiktok\.com/',
        r'tiktok',
    ],
}