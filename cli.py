# cli.py

import argparse
import os
from agents.gradle_setup_agent import GradleSetupAgent
from agents.retry_agent import RetryAgent
from agents.mapping_loader import MappingLoader

def main():
    parser = argparse.ArgumentParser(description="Run migration refinement tool")
    parser.add_argument("--legacy", required=True, help="Path to legacy codebase")
    parser.add_argument("--migrated", required=True, help="Path to migrated codebase")
    parser.add_argument("--map", required=True, help="Path to mapping.json file")
    parser.add_argument("--reference", help="Path to reference applications (legacy + migrated)", default="")
    parser.add_argument("--enterprise", help="Path to shared enterprise framework", default="")

    args = parser.parse_args()

    print("🚀 Starting Migration Assist Refinement Pipeline")
    print(f"📁 Legacy dir:     {args.legacy}")
    print(f"📁 Migrated dir:   {args.migrated}")
    print(f"📄 Mapping file:   {args.map}")
    print(f"📂 Reference dir:  {args.reference or 'None'}")
    print(f"📂 Enterprise dir: {args.enterprise or 'None'}")
    print("─────────────────────────────────────────────")

    # Load mapping.json
    mapping = MappingLoader(args.map)

    # Step 1: Setup Gradle files
    gradle_setup = GradleSetupAgent(
        migrated_dir=args.migrated,
        legacy_dir=args.legacy,
        reference_dir=args.reference
    )
    gradle_setup.setup()

    # Step 2: Retry fixes and complete migration
    retry_agent = RetryAgent(
        legacy_dir=args.legacy,
        migrated_dir=args.migrated,
        enterprise_dir=args.enterprise,
        reference_dir=args.reference
    )
    result = retry_agent.retry_fixes(mapping=mapping)

    print("✅ Migration Assist post-processing complete.")
    print(f"🔧 Final Status: {result['status']}")
    print(f"🔁 Retry Attempts: {result.get('retry_attempts', 0)}")

if __name__ == "__main__":
    main()
