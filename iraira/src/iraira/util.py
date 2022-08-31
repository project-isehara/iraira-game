from pathlib import Path


class RepoPath:
    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.assert_dir = self.repo_root / "assert"
        self.db_dir = self.repo_root / "db"
