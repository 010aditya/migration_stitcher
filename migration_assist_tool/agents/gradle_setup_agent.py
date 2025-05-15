# agents/gradle_setup_agent.py

import os
import shutil
from maven_tools import MavenProject


class GradleSetupAgent:
    def __init__(self, migrated_dir: str, legacy_dir: str, template_dir: str = "config/templates"):
        self.migrated_dir = migrated_dir
        self.legacy_dir = legacy_dir
        self.template_dir = template_dir

    def setup(self):
        build_gradle = os.path.join(self.migrated_dir, "build.gradle")
        settings_gradle = os.path.join(self.migrated_dir, "settings.gradle")

        if not os.path.exists(build_gradle):
            print("🛠 Generating build.gradle from pom.xml...")
            pom_path = self._find_pom()
            if pom_path:
                self._generate_build_gradle_from_pom(pom_path)
            else:
                self._write_file(build_gradle, self._fallback_build_gradle())

        if not os.path.exists(settings_gradle):
            self._generate_settings_gradle_from_pom()

        self._ensure_gradle_wrapper()
        return {"status": "complete"}

    def _find_pom(self):
        for root, _, files in os.walk(self.legacy_dir):
            if "pom.xml" in files:
                return os.path.join(root, "pom.xml")
        return None

    def _generate_build_gradle_from_pom(self, pom_path):
        project = MavenProject(pom_path)
        deps = project.get_dependencies()
        group_id = project.get_group_id()
        artifact_id = project.get_artifact_id()
        version = project.get_version()

        lines = [
            "plugins {",
            "    id 'java'",
            "    id 'org.springframework.boot' version '3.2.0'",
            "    id 'io.spring.dependency-management' version '1.1.0'",
            "}",
            "",
            f"group = '{group_id}'",
            f"version = '{version or '1.0.0'}'",
            "sourceCompatibility = '21'",
            "",
            "repositories {",
            "    mavenCentral()",
            "}",
            "",
            "dependencies {"
        ]

        for d in deps:
            scope = d.get("scope", "compile")
            if scope in ("compile", "runtime", "provided", "system"):
                lines.append(f"    implementation '{d['groupId']}:{d['artifactId']}:{d['version']}'")
            elif scope == "test":
                lines.append(f"    testImplementation '{d['groupId']}:{d['artifactId']}:{d['version']}'")

        lines.append("}")
        lines.append("test { useJUnitPlatform() }")

        build_gradle_path = os.path.join(self.migrated_dir, "build.gradle")
        self._write_file(build_gradle_path, "\n".join(lines))

    def _generate_settings_gradle_from_pom(self):
        pom_path = self._find_pom()
        artifact_id = "migrated-project"
        if pom_path:
            project = MavenProject(pom_path)
            artifact_id = project.get_artifact_id() or "migrated-project"
        self._write_file(
            os.path.join(self.migrated_dir, "settings.gradle"),
            f"rootProject.name = '{artifact_id}'\n"
        )

    def _write_file(self, path: str, content: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _ensure_gradle_wrapper(self):
        gradlew = os.path.join(self.migrated_dir, "gradlew")
        gradlew_bat = os.path.join(self.migrated_dir, "gradlew.bat")
        wrapper_dir = os.path.join(self.migrated_dir, "gradle/wrapper")
        wrapper_props = os.path.join(wrapper_dir, "gradle-wrapper.properties")

        os.makedirs(wrapper_dir, exist_ok=True)

        if not os.path.exists(gradlew):
            self._write_file(gradlew, "#!/bin/bash\n# Gradle wrapper placeholder\n")
            os.chmod(gradlew, 0o755)
        if not os.path.exists(gradlew_bat):
            self._write_file(gradlew_bat, "@echo off\nREM Gradle wrapper placeholder\n")
        if not os.path.exists(wrapper_props):
            self._write_file(wrapper_props, """\
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.5-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")

    def _fallback_build_gradle(self):
        return """\
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.0'
}

group = 'com.migrated'
version = '1.0.0'
sourceCompatibility = '21'

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}

test {
    useJUnitPlatform()
}
"""