/**
 * Tests for CLI commands (get --download, clone).
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdir, rm, writeFile, readdir, readFile, lstat, symlink } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { execSync } from "node:child_process";

describe("CLI Commands", () => {
  let testDir: string;
  let cliPath: string;

  beforeEach(async () => {
    testDir = join(tmpdir(), `cldpm-cli-test-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    await mkdir(testDir, { recursive: true });
    cliPath = join(__dirname, "..", "dist", "cli.js");
  });

  afterEach(async () => {
    await rm(testDir, { recursive: true, force: true });
  });

  /**
   * Setup a test mono repo with a project and shared skill
   */
  async function setupTestRepo(): Promise<string> {
    const repoPath = join(testDir, "test-repo");

    // Create cldpm.json
    await mkdir(repoPath, { recursive: true });
    await writeFile(
      join(repoPath, "cldpm.json"),
      JSON.stringify({
        name: "test-repo",
        version: "1.0.0",
        projectsDir: "projects",
        sharedDir: "shared",
      })
    );

    // Create shared directories
    for (const type of ["skills", "agents", "hooks", "rules"]) {
      await mkdir(join(repoPath, "shared", type), { recursive: true });
    }

    // Create a shared skill
    const skillPath = join(repoPath, "shared", "skills", "logging");
    await mkdir(skillPath, { recursive: true });
    await writeFile(join(skillPath, "SKILL.md"), "# Logging Skill\n\nA logging skill.");
    await writeFile(
      join(skillPath, "skill.json"),
      JSON.stringify({ name: "logging", description: "Logging skill" })
    );

    // Create a project
    const projectPath = join(repoPath, "projects", "my-app");
    await mkdir(projectPath, { recursive: true });
    await writeFile(
      join(projectPath, "project.json"),
      JSON.stringify({
        name: "my-app",
        description: "My application",
        dependencies: {
          skills: ["logging"],
          agents: [],
          hooks: [],
          rules: [],
        },
      })
    );
    await writeFile(join(projectPath, "CLAUDE.md"), "# My App\n\nProject instructions.");

    // Create .claude directory structure
    for (const type of ["skills", "agents", "hooks", "rules"]) {
      await mkdir(join(projectPath, ".claude", type), { recursive: true });
    }
    await writeFile(
      join(projectPath, ".claude", "settings.json"),
      JSON.stringify({ version: "1.0" })
    );

    // Create symlink to shared skill
    await symlink(
      join(repoPath, "shared", "skills", "logging"),
      join(projectPath, ".claude", "skills", "logging")
    );

    // Create a local skill (not a symlink)
    const localSkillPath = join(projectPath, ".claude", "skills", "local-utils");
    await mkdir(localSkillPath, { recursive: true });
    await writeFile(join(localSkillPath, "SKILL.md"), "# Local Utils\n\nLocal skill.");

    // Create outputs directory
    await mkdir(join(projectPath, "outputs"), { recursive: true });

    return repoPath;
  }

  /**
   * Run CLI command and return output
   */
  function runCli(args: string, cwd: string): string {
    try {
      return execSync(`node ${cliPath} ${args}`, {
        cwd,
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "pipe"],
      });
    } catch (error: unknown) {
      const execError = error as { stdout?: string; stderr?: string; message?: string };
      throw new Error(
        `CLI failed: ${execError.stderr || execError.stdout || execError.message}`
      );
    }
  }

  describe("cldpm get --download", () => {
    it("should download project with shared components", async () => {
      const repoPath = await setupTestRepo();
      const outputDir = join(testDir, "downloaded");

      runCli(`get my-app --download --output ${outputDir}`, repoPath);

      // Check that project was downloaded
      expect(await pathExists(outputDir)).toBe(true);
      expect(await pathExists(join(outputDir, "project.json"))).toBe(true);
      expect(await pathExists(join(outputDir, "CLAUDE.md"))).toBe(true);

      // Check that shared skill was copied (not symlinked)
      const skillPath = join(outputDir, ".claude", "skills", "logging");
      expect(await pathExists(skillPath)).toBe(true);
      const stats = await lstat(skillPath);
      expect(stats.isSymbolicLink()).toBe(false);
      expect(stats.isDirectory()).toBe(true);

      // Check skill contents
      expect(await pathExists(join(skillPath, "SKILL.md"))).toBe(true);
      const skillContent = await readFile(join(skillPath, "SKILL.md"), "utf-8");
      expect(skillContent).toContain("Logging Skill");
    });

    it("should copy local components", async () => {
      const repoPath = await setupTestRepo();
      const outputDir = join(testDir, "downloaded");

      runCli(`get my-app --download --output ${outputDir}`, repoPath);

      // Check that local skill was copied
      const localSkillPath = join(outputDir, ".claude", "skills", "local-utils");
      expect(await pathExists(localSkillPath)).toBe(true);
      const stats = await lstat(localSkillPath);
      expect(stats.isSymbolicLink()).toBe(false);
      expect(stats.isDirectory()).toBe(true);
    });

    it("should fail if output directory exists", async () => {
      const repoPath = await setupTestRepo();
      const outputDir = join(testDir, "existing");
      await mkdir(outputDir, { recursive: true });

      expect(() => {
        runCli(`get my-app --download --output ${outputDir}`, repoPath);
      }).toThrow();
    });

    it("should use project name as default output", async () => {
      const repoPath = await setupTestRepo();

      runCli(`get my-app --download`, repoPath);

      // Check that my-app directory was created
      const outputDir = join(repoPath, "my-app");
      expect(await pathExists(outputDir)).toBe(true);
      expect(await pathExists(join(outputDir, "project.json"))).toBe(true);
    });
  });

  describe("cldpm clone", () => {
    it("should clone project with shared components", async () => {
      const repoPath = await setupTestRepo();
      const cloneDir = join(testDir, "cloned");

      runCli(`clone my-app ${cloneDir}`, repoPath);

      // Check that project was cloned
      expect(await pathExists(cloneDir)).toBe(true);
      expect(await pathExists(join(cloneDir, "project.json"))).toBe(true);
      expect(await pathExists(join(cloneDir, "CLAUDE.md"))).toBe(true);

      // Check that shared skill was copied (not symlinked)
      const skillPath = join(cloneDir, ".claude", "skills", "logging");
      expect(await pathExists(skillPath)).toBe(true);
      const stats = await lstat(skillPath);
      expect(stats.isSymbolicLink()).toBe(false);
      expect(stats.isDirectory()).toBe(true);
    });

    it("should copy local components", async () => {
      const repoPath = await setupTestRepo();
      const cloneDir = join(testDir, "cloned");

      runCli(`clone my-app ${cloneDir}`, repoPath);

      // Check that local skill was copied
      const localSkillPath = join(cloneDir, ".claude", "skills", "local-utils");
      expect(await pathExists(localSkillPath)).toBe(true);
    });

    it("should include shared directory with --include-shared", async () => {
      const repoPath = await setupTestRepo();
      const cloneDir = join(testDir, "cloned");

      runCli(`clone my-app ${cloneDir} --include-shared`, repoPath);

      // Check that shared directory was copied
      expect(await pathExists(join(cloneDir, "shared"))).toBe(true);
      expect(await pathExists(join(cloneDir, "shared", "skills", "logging"))).toBe(true);

      // Check that cldpm.json was copied
      expect(await pathExists(join(cloneDir, "cldpm.json"))).toBe(true);
    });

    it("should preserve symlinks with --preserve-links", async () => {
      const repoPath = await setupTestRepo();
      const cloneDir = join(testDir, "cloned");

      runCli(`clone my-app ${cloneDir} --preserve-links`, repoPath);

      // Check that shared skill is a symlink
      const skillPath = join(cloneDir, ".claude", "skills", "logging");
      expect(await pathExists(skillPath)).toBe(true);
      const stats = await lstat(skillPath);
      expect(stats.isSymbolicLink()).toBe(true);
    });

    it("should fail if target directory exists", async () => {
      const repoPath = await setupTestRepo();
      const cloneDir = join(testDir, "existing");
      await mkdir(cloneDir, { recursive: true });

      expect(() => {
        runCli(`clone my-app ${cloneDir}`, repoPath);
      }).toThrow();
    });

    it("should copy settings.json", async () => {
      const repoPath = await setupTestRepo();
      const cloneDir = join(testDir, "cloned");

      runCli(`clone my-app ${cloneDir}`, repoPath);

      const settingsPath = join(cloneDir, ".claude", "settings.json");
      expect(await pathExists(settingsPath)).toBe(true);
      const content = await readFile(settingsPath, "utf-8");
      const settings = JSON.parse(content);
      expect(settings.version).toBe("1.0");
    });

    it("should copy outputs directory", async () => {
      const repoPath = await setupTestRepo();

      // Add a file to outputs
      await writeFile(
        join(repoPath, "projects", "my-app", "outputs", "result.txt"),
        "test output"
      );

      const cloneDir = join(testDir, "cloned");
      runCli(`clone my-app ${cloneDir}`, repoPath);

      expect(await pathExists(join(cloneDir, "outputs"))).toBe(true);
      expect(await pathExists(join(cloneDir, "outputs", "result.txt"))).toBe(true);
    });
  });

  describe("cldpm get (basic)", () => {
    it("should display project tree", async () => {
      const repoPath = await setupTestRepo();

      const output = runCli(`get my-app`, repoPath);

      expect(output).toContain("my-app");
      expect(output).toContain("Shared");
      expect(output).toContain("logging");
    });

    it("should output JSON with --format json", async () => {
      const repoPath = await setupTestRepo();

      const output = runCli(`get my-app --format json`, repoPath);

      const parsed = JSON.parse(output);
      expect(parsed.name).toBe("my-app");
      expect(parsed.shared.skills).toBeDefined();
      expect(parsed.shared.skills.length).toBeGreaterThan(0);
      expect(parsed.shared.skills[0].name).toBe("logging");
    });
  });
});

/**
 * Helper to check if path exists
 */
async function pathExists(path: string): Promise<boolean> {
  try {
    await lstat(path);
    return true;
  } catch {
    return false;
  }
}
