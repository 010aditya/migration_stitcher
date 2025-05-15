import os
import subprocess
from agents.fix_and_compile import FixAndCompileAgent
from agents.build_fixer_agent import BuildFixerAgent
from agents.context_stitcher import ContextStitcherAgent

class RetryAgent:
    def __init__(self, migrated_dir, legacy_dir, enterprise_dir, reference_dir, max_retries=3):
        self.migrated_dir = migrated_dir
        self.legacy_dir = legacy_dir
        self.enterprise_dir = enterprise_dir
        self.reference_dir = reference_dir
        self.max_retries = max_retries

        self.fixer = FixAndCompileAgent(
            legacy_dir=legacy_dir,
            migrated_dir=migrated_dir,
            enterprise_dir=enterprise_dir,
            reference_dir=reference_dir
        )
        self.context_builder = ContextStitcherAgent(
            legacy_dir=legacy_dir,
            migrated_dir=migrated_dir,
            enterprise_dir=enterprise_dir,
            reference_dir=reference_dir
        )
        self.build_fixer = BuildFixerAgent(migrated_dir)

    def check_single_file_compiles(self, java_path: str) -> bool:
        try:
            output_dir = ".buildcheck/bin"
            os.makedirs(output_dir, exist_ok=True)
            cmd = ["javac", "-d", output_dir, java_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️ Compile check failed: {e}")
            return False

    def retry_fix_and_build(self, migration_map):
        for file_entry in migration_map:
            source_paths = file_entry.get("source", [])
            target_paths = file_entry.get("target", [])
            for target_path in target_paths:
                target_file_path = os.path.join(self.migrated_dir, target_path)

                # Skip if file already compiles
                if self.check_single_file_compiles(target_file_path):
                    print(f"✅ {target_path} compiles. Skipping fix.")
                    continue

                success = False
                for attempt in range(self.max_retries):
                    print(f"🔁 Attempt {attempt+1} to fix and compile {target_path}")
                    fix_result = self.fixer.fix_file(
                        target_path=target_path,
                        source_paths=source_paths,
                        enterprise_refs=[],
                        stitcher=self.context_builder
                    )

                    # Check again if file compiles after fix
                    if self.check_single_file_compiles(target_file_path):
                        print(f"✅ {target_path} compiles after fix.")
                        success = True
                        break
                    else:
                        print(f"❌ {target_path} still fails to compile.")

                if not success:
                    print(f"🚨 {target_path} could not be compiled after {self.max_retries} attempts.")

        # After all files compile, try Gradle build
        print("🚀 All file fixes attempted. Triggering Gradle build...")
        # Add your actual Gradle build trigger logic here
