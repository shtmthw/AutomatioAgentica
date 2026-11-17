"""Launch the AutomatioAgentica MCP server from any working directory.

MCP clients start servers from their own directory, so `python -m automatio.mcp_server`
only works when the client runs it inside the repository. This launcher puts the
repository on sys.path first, so an absolute path is all a client config needs:

    /path/to/AutomatioAgentica/.venv/bin/python /path/to/AutomatioAgentica/scripts/mcp_server.py

`python -m automatio mcp-config` prints that config, filled in for this checkout.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automatio.mcp_server import main  # noqa: E402

if __name__ == "__main__":
    main()
