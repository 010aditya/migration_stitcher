# cli.py

import argparse
import os
from agents.mapping_loader import MappingLoader
from agents.context_stitcher import ContextStitcherAgent
from agents.fix_and_compile import FixAndCompileAgent
from agents.completion_agent import CompletionAgent
from agents.retry_agent import RetryAgent
from agents.build_validator import BuildValidatorAgent
from agents.package_structure_normalizer import PackageStructureNormalizerAgent
from agents.gradle_setup_agent import GradleSetupAgent
from agents.fix_history_logger import FixHistoryLogger

def main():
    parser = argparse.ArgumentParser(description="Run migration fix pipeline")
    parser.add_argument("--legacy", required=True, help="Path to legacy codebase")
    parser.add_argument("--migrated", required=True, help="Path to migrated Spring Boot codebase")
    parser.add_argument("--map", required=True, help="Path to mapping.json")
    parser.add_argument("--enterprise", default="", help="Path to enterprise framework codebase (optional)")

    args = parser.parse_args()

    # Load mapping
    print("📦 Loading mapping.json...")
    loader = MappingLoader(args.map)
    loader.load()

    # Gradle setup
    print("⚙️  Setting up Gradle...")
    gradle_setup = GradleSetupAgent(args.migrated)
    gradle_setup.setup()

    # Normalize packages
    print("📦 Normalizing package structure...")
    normalizer = PackageStructureNormalizerAgent(args.migrated)
    normalizer.normalize_all()

    # Init agents
    print("🤖 Initializing agents...")
    stitcher = ContextStitcherAgent(args.legacy, args.migrated, args.enterprise)
    fixer = FixAndCompileAgent(args.legacy, args.migrated, args.enterprise)
    completer = CompletionAgent(args.legacy, args.migrated, args.enterprise)
    validator = BuildValidatorAgent(args.migrated)
    retry = RetryAgent(args.legacy, args.migrated, args.enterprise)
    logger = FixHistoryLogger()

    # Process all mappings
    print("🚀 Running fix and complete pipeline...")
    for mapping in loader.get_all_mappings():
        for target in mapping["targetPaths"]:
            sources = mapping["sourcePaths"]

            print(f"\n🔧 Fixing: {target}")
            fix_result = fixer.fix_file(target, sources, [], stitcher)
            logger.log_fix(target, "FixAndCompileAgent", fix_result["fix_log"]["status"],
                           None, fix_result["fixed_code"], fix_result["fix_log"])

            if fix_result["fix_log"]["status"] != "success":
                print(f"🔍 Running completion for: {target}")
                complete_result = completer.complete_missing_logic(target, sources, [], stitcher)
                logger.log_fix(target, "CompletionAgent", complete_result["completion_log"]["status"],
                               None, complete_result["fixed_code"], complete_result["completion_log"])

    # Validate full build
    print("\n🧪 Validating Gradle build...")
    build_result = validator.validate_build()
    if build_result["build_success"]:
        print("✅ Gradle build successful!")
    else:
        print("❌ Build failed. Retrying problematic files...")
        retry.retry_fixes(loader)

if __name__ == "__main__":
    main()
