import re

class SemanticMapper:
    """
    M3.0 Component: Translates raw file paths into high-level Security Concepts.
    """
    def __init__(self):
        # The Knowledge Base: (Regex Pattern, Semantic Tag)
        # Order matters: Specific rules first, generic last.
        self.rules = [
            # 1. User Protection (The M2.1 Demo Case)
            (r".*protected.*", "SENSITIVE_USER_FILE"),

            # 2. Critical System Auth
            (r"^/etc/shadow.*", "CRITICAL_AUTH"),
            (r"^/etc/passwd.*", "CRITICAL_AUTH"),
            (r"^/etc/sudoers.*", "CRITICAL_AUTH"),
            (r"^/root/.*",      "ROOT_SENSITIVE"),

            # 3. SSH Keys (High Value Targets)
            (r"^/home/.*/\.ssh/id_.*", "SSH_PRIVATE_KEY"),
            (r"^/home/.*/\.ssh/.*",    "SSH_CONFIG"),

            # 4. System Binaries (Integrity)
            (r"^/bin/.*",     "SYSTEM_BINARY"),
            (r"^/usr/bin/.*", "SYSTEM_BINARY"),
            (r"^/sbin/.*",    "SYSTEM_ADMIN_BINARY"),

            # 5. Libraries
            (r"^/lib.*/.*\.so.*", "SHARED_LIBRARY"),

            # 6. Noise (Low Risk)
            (r"^/dev/null", "DEVICE_NULL"),
            (r"^/dev/tty",  "DEVICE_TTY"),
            (r"^/proc/.*",  "PROC_FS"),
            (r"^/tmp/.*",   "TEMP_FILE"),
        ]

    def classify(self, path):
        """Returns the Semantic Tag for a given path."""
        if not path:
            return "UNKNOWN"

        for pattern, tag in self.rules:
            # Use regex search to find matches
            if re.search(pattern, path):
                return tag

        return "UNCLASSIFIED_FILE"