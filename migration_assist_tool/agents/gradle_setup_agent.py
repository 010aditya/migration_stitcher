# agents/gradle_setup_agent.py

import os
import shutil
import xml.etree.ElementTree as ET


class GradleSetupAgent:
    def __init__(self, migrated_dir: str, legacy_dir: str, template_dir: str = "config/templates"):
        self.migrated_dir = migrated_dir
        self.legacy_dir = legacy_dir
        self.template_dir = template_dir

    def setup(self):
        build_gradle = os.path.join(self.migrated_dir, "build.gradle")
        settings_gradle = os.path.join(self.migrated_dir, "settings.gradle")

        pom_path = self._find_pom()

        if not os.path.exists(build_gradle):
            if pom_path:
                print("🛠 Generating build.gradle from pom.xml...")
                self._generate_build_gradle_from_pom(pom_path)
            else:
                self._write_file(build_gradle, self._fallback_build_gradle())

        if not os.path.exists(settings_gradle):
            artifact_id = self._get_artifact_id_from_pom(pom_path) if pom_path else "migrated-project"
            self._write_file(settings_gradle, f"rootProject.name = '{artifact_id}'\n")

        self._ensure_gradle_wrapper()
        return {"status": "complete"}

    def _find_pom(self):
        for root, _, files in os.walk(self.legacy_dir):
            if "pom.xml" in files:
                return os.path.join(root, "pom.xml")
        return None

    def _get_artifact_id_from_pom(self, pom_path):
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()
            ns = {'m': root.tag.split('}')[0].strip('{')}
            artifact_id = root.find("m:artifactId", ns)
            return artifact_id.text if artifact_id is not None else "migrated-project"
        except Exception:
            return "migrated-project"

    def _generate_build_gradle_from_pom(self, pom_path):
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()
            ns = {'m': root.tag.split('}')[0].strip('{')}

            group_id = root.find("m:groupId", ns)
            artifact_id = root.find("m:artifactId", ns)
            version = root.find("m:version", ns)

            group = group_id.text if group_id is not None else "com.migrated"
            artifact = artifact_id.text if artifact_id is not None else "migrated-project"
            ver = version.text if version is not None else "1.0.0"

            dependencies = []
            deps = root.find("m:dependencies", ns)
            if deps is not None:
                for dep in deps.findall("m:dependency", ns):
                    g = dep.find("m:groupId", ns)
                    a = dep.find("m:artifactId", ns)
                    v = dep.find("m:version", ns)
                    scope = dep.find("m:scope", ns)
                    if g is not None and a is not None and v is not None:
                        line = f"    {'testImplementation' if (scope is not None and scope.text == 'test') else 'implementation'} '{g.text}:{a.text}:{v.text}'"
                        dependencies.append(line)

            gradle_lines = [
                "plugins {",
                "    id 'java'",
                "    id 'org.springframework.boot' version '3.2.0'",
                "    id 'io.spring.dependency-management' version '1.1.0'",
                "}",
                "",
                f"group = '{group}'",
                f"version = '{ver}'",
                "sourceCompatibility = '21'",
                "",
                "repositories {",
                "    mavenCentral()",
                "}",
                "",
                "dependencies {"
            ]
            gradle_lines.extend(dependencies)
            gradle_lines.append("}")
            gradle_lines.append("test { useJUnitPlatform() }")

            self._write_file(os.path.join(self.migrated_dir, "build.gradle"), "\n".join(gradle_lines))

        except Exception as e:
            print(f"⚠️ Failed to parse pom.xml: {e}")
            self._write_file(os.path.join(self.migrated_dir, "build.gradle"), self._fallback_build_gradle())

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
