import os


class RulesLoader:
    @staticmethod
    def load(rules_dir: str) -> str:
        if not os.path.isdir(rules_dir):
            return ""
        files = sorted(
            f for f in os.listdir(rules_dir) if f.endswith(".md")
        )
        parts = []
        for filename in files:
            path = os.path.join(rules_dir, filename)
            with open(path, encoding="utf-8") as fh:
                parts.append(fh.read())
        return "\n\n".join(parts)
