import re
import os  # <--- NEW: Required for resolving symlinks and ".." tricks

class SemanticMapper:
    """
    M3.3 Component: Translates raw file paths into high-level Security Concepts.
    UPDATED: Uses Canonicalization (realpath) to defeat path evasion (Symlinks, Traversal).
    """
    def __init__(self):
        # The Knowledge Base: (Regex Pattern, Semantic Tag)
        self.rules = [
            # 1. User Protection (The Demo Case)
            (r".*protected.*", "SENSITIVE_USER_FILE"),

            # 2. Critical System Auth
            (r"^/etc/shadow.*", "CRITICAL_AUTH"),
            (r"^/etc/passwd.*", "CRITICAL_AUTH"),
            (r"^/etc/sudoers.*", "CRITICAL_AUTH"),
            (r"^/root/.*",      "ROOT_SENSITIVE"),

            # 3. SSH Keys (Catch them anywhere, not just in .ssh)
            (r".*id_rsa.*",     "SSH_PRIVATE_KEY"),
            (r".*id_dsa.*",     "SSH_PRIVATE_KEY"),
            (r".*id_ed25519.*", "SSH_PRIVATE_KEY"),
            (r"^/home/.*/\.ssh/.*", "SSH_CONFIG"),

            # 4. System Binaries
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

        # --- SECURITY FIX: CANONICALIZATION ---
        # 1. Resolve Symlinks (/tmp/shortcut -> /etc/shadow)
        # 2. Resolve Relative Paths (../../etc/shadow -> /etc/shadow)
        # 3. Resolve Redundant Slashes (/etc//shadow -> /etc/shadow)
        try:
            if os.path.exists(path):
                real_path = os.path.realpath(path)

                # If the path changed (it was an alias), update it
                if real_path != path:
                    # Optional: Log the evasion attempt
                    # print(f"[DEBUG] Path Unmasked: {path} -> {real_path}")
                    path = real_path
        except Exception:
            # If file doesn't exist yet or perm error, fall back to string check
            pass
        # --------------------------------------

        for pattern, tag in self.rules:
            if re.search(pattern, path):
                return tag

        return "UNCLASSIFIED_FILE"