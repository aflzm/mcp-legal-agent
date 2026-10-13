"""Offline demo that requires no third-party dependencies."""

import json

from agent.harness import AgentHarness

if __name__ == "__main__":
    print(
        json.dumps(
            AgentHarness().run(
                "Zhang secretly stole another person's property in a relatively large amount."
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
