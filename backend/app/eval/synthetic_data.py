"""
Synthetic hand-labeled transcript for evaluation.

Contains:
- Clear requirements with grounding
- Deliberately contradictory statements
- Deliberately vague/ungroundable statements
- Filler content
"""

SYNTHETIC_TRANSCRIPT = """Interviewer (00:00:05): Hello, thank you for meeting today. How are you?

Stakeholder (00:00:10): I'm doing well, thanks for asking.

Interviewer (00:00:15): Let's discuss the authentication requirements for the new system.

Stakeholder (00:00:20): We need a login system that supports multi-factor authentication. Users should be able to choose between SMS codes or authenticator apps like Google Authenticator.

Interviewer (00:00:45): What about password requirements?

Stakeholder (00:00:50): Passwords must be at least 12 characters long with uppercase, lowercase, numbers, and special characters. Also, passwords should expire every 90 days for compliance.

Interviewer (00:01:20): Got it. What about session management?

Stakeholder (00:01:25): Sessions should timeout after 30 minutes of inactivity. But if users enable "remember me" on trusted devices, sessions can last up to 30 days.

Interviewer (00:02:00): Earlier you mentioned 30 minutes for session timeout. Is that firm?

Stakeholder (00:02:05): Actually, for security reasons, I think sessions should timeout after 15 minutes of inactivity.

Interviewer (00:02:30): So 15 minutes or 30 minutes?

Stakeholder (00:02:35): Let's go with 15 minutes for now.

Interviewer (00:03:00): What about data encryption?

Stakeholder (00:03:05): All user data must be encrypted. Use industry-standard encryption.

Interviewer (00:03:20): Can you be more specific about the encryption requirements?

Stakeholder (00:03:25): Just make it secure. You know, encrypted and safe.

Interviewer (00:03:40): Understood. Anything else on authentication?

Stakeholder (00:03:45): The system should be really user-friendly and intuitive.

Interviewer (00:04:00): Great, I think we covered everything. Thanks again!

Stakeholder (00:04:05): No problem, have a good day!"""


# Gold standard: Hand-labeled requirements
GOLD_REQUIREMENTS = [
    {
        "id": "gold_req_1",
        "statement": "System must support multi-factor authentication with SMS codes or authenticator apps",
        "grounded": True,
        "segment_indices": [3],  # Stakeholder at 00:00:20
        "quotes": ["multi-factor authentication", "SMS codes or authenticator apps"]
    },
    {
        "id": "gold_req_2",
        "statement": "Passwords must be at least 12 characters with uppercase, lowercase, numbers, and special characters",
        "grounded": True,
        "segment_indices": [5],  # Stakeholder at 00:00:50
        "quotes": ["at least 12 characters long with uppercase, lowercase, numbers, and special characters"]
    },
    {
        "id": "gold_req_3",
        "statement": "Passwords must expire every 90 days",
        "grounded": True,
        "segment_indices": [5],
        "quotes": ["passwords should expire every 90 days"]
    },
    {
        "id": "gold_req_4",
        "statement": "Sessions should timeout after 15 minutes of inactivity",
        "grounded": True,
        "segment_indices": [9],  # Final answer at 00:02:05
        "quotes": ["sessions should timeout after 15 minutes of inactivity"]
    },
    {
        "id": "gold_req_5",
        "statement": "Remember me feature allows sessions to last 30 days on trusted devices",
        "grounded": True,
        "segment_indices": [7],
        "quotes": ["remember me", "sessions can last up to 30 days"]
    },
    {
        "id": "gold_req_6",
        "statement": "All user data must be encrypted",
        "grounded": True,
        "segment_indices": [13],
        "quotes": ["All user data must be encrypted"]
    },
]

# Known contradictions
GOLD_CONTRADICTIONS = [
    {
        "requirement_1": "Sessions timeout after 30 minutes",
        "requirement_2": "Sessions timeout after 15 minutes",
        "segment_1_index": 7,  # 00:01:25
        "segment_2_index": 9,  # 00:02:05
    }
]

# Known ungroundable statements (too vague)
GOLD_UNGROUNDABLE = [
    {
        "statement": "Use industry-standard encryption",
        "reason": "Too vague, no specific algorithm or standard mentioned",
        "segment_index": 13
    },
    {
        "statement": "System should be user-friendly and intuitive",
        "reason": "Subjective, no measurable criteria",
        "segment_index": 17
    }
]

# Filler segments (should be classified as filler)
GOLD_FILLER_INDICES = [
    0,   # Hello greeting
    1,   # I'm doing well
    20,  # Thanks again
    21   # Have a good day
]
