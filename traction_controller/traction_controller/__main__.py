import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))


if __name__ == "__main__":
    from traction_controller.main import main

    main()
