import re

# The regex pattern
ipc_regex = re.compile(r"^(I.P.C|IPC|Indian Penal Code)\b.*$", re.IGNORECASE)

# Example text containing different formats
test_strings = [
    "I.P.C.",
    "IPC",
    "Indian Penal Code",
    "I.P.C (Police), 1098",
    "Something else",
    "I.P.C. 1234",
    "ipc",
    "I.P.C. and other details",
]

# Check each string against the regex
for text in test_strings:
    if ipc_regex.match(text):
        print(f"Matched: {text}")
    else:
        print(f"Did not match: {text}")
