# agents/gradle_setup_agent.py

import os
import shutil

class GradleSetupAgent:
    def __init__(self, migrated_dir: str, template_dir: str = "config/templates"):
        self.migrated_dir = migrated_dir
        self.template_dir = template_dir

    def setup(self):
        gradle_files = ["build.gradle", "settings.gradle", "gradlew", "gradlew.bat"]
        gradle_wrapper_dir = os.path.join(self.migrated_dir, "gradle/wrapper")
        gradle_wrapper_files = ["gradle-wrapper.properties", "gradle-wrapper.jar"]

        generated = []

        # build.gradle
        build_path = os.path.join(self.migrated_dir, "build.gradle")
        if not os.path.exists(build_path):
            template = os.path.join(self.template_dir, "build.gradle.template")
            self._copy_or_create(template, build_path, self._default_build_gradle())
            generated.append("build.gradle")

        # settings.gradle
        settings_path = os.path.join(self.migrated_dir, "settings.gradle")
        if not os.path.exists(settings_path):
            template = os.path.join(self.template_dir, "settings.gradle.template")
            self._copy_or_create(template, settings_path, f"rootProject.name = 'migrated-project'\n")
            generated.append("settings.gradle")

        # gradlew scripts
        for wrapper_file in ["gradlew", "gradlew.bat"]:
            wrapper_path = os.path.join(self.migrated_dir, wrapper_file)
            if not os.path.exists(wrapper_path):
                self._write_file(wrapper_path, self._default_gradlew(wrapper_file))
                os.chmod(wrapper_path, 0o755)
                generated.append(wrapper_file)

        # gradle/wrapper/ files
        os.makedirs(gradle_wrapper_dir, exist_ok=True)
        for wrapper_file in gradle_wrapper_files:
            wrapper_path = os.path.join(gradle_wrapper_dir, wrapper_file)
            if not os.path.exists(wrapper_path):
                self._write_file(wrapper_path, self._default_wrapper_file(wrapper_file))
                generated.append(f"gradle/wrapper/{wrapper_file}")

        return {"status": "complete", "generated_files": generated}

    def _copy_or_create(self, template_path: str, dest_path: str, fallback_content: str):
        if os.path.exists(template_path):
            shutil.copy(template_path, dest_path)
        else:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(fallback_content)

    def _write_file(self, path: str, content: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _default_build_gradle(self) -> str:
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
    implementation 'com.fasterxml.jackson.core:jackson-databind'
    implementation 'org.projectlombok:lombok'
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}

test {
    useJUnitPlatform()
}
"""

    def _default_gradlew(self, filename: str) -> str:
        return f"# {filename} placeholder script — Replace with real wrapper for production.\n"

    def _default_wrapper_file(self, filename: str) -> str:
        if filename.endswith(".properties"):
            return """\
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.5-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""
        else:
            return "// Binary .jar placeholder — must be replaced with real Gradle wrapper JAR.\n"
