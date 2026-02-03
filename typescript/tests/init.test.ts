/**
 * Tests for cldpm init command.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdir, rm, writeFile, readFile, lstat } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { execSync } from "node:child_process";

describe("cldpm init", () => {
  let testDir: string;
  let cliPath: string;

  beforeEach(async () => {
    testDir = join(tmpdir(), `cldpm-init-test-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    await mkdir(testDir, { recursive: true });
    cliPath = join(__dirname, "..", "dist", "cli.js");
  });

  afterEach(async () => {
    await rm(testDir, { recursive: true, force: true });
  });

  /**
   * Run CLI command and return output
   */
  function runCli(args: string, cwd: string): { stdout: string; stderr: string; exitCode: number } {
    try {
      const stdout = execSync(`node ${cliPath} ${args}`, {
        cwd,
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "pipe"],
      });
      return { stdout, stderr: "", exitCode: 0 };
    } catch (error: unknown) {
      const execError = error as { stdout?: string; stderr?: string; status?: number; code?: number };
      return {
        stdout: execError.stdout || "",
        stderr: execError.stderr || "",
        exitCode: execError.status ?? execError.code ?? 1,
      };
    }
  }

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

  describe("basic init", () => {
    it("should initialize in current directory", async () => {
      const repoPath = join(testDir, "new-repo");
      await mkdir(repoPath, { recursive: true });

      const result = runCli("init", repoPath);

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toContain("Initialized CLDPM mono repo");

      // Check cldpm.json exists
      expect(await pathExists(join(repoPath, "cldpm.json"))).toBe(true);
      const configContent = await readFile(join(repoPath, "cldpm.json"), "utf-8");
      const config = JSON.parse(configContent);
      expect(config.name).toBeDefined();
      expect(config.projectsDir).toBe("projects");
      expect(config.sharedDir).toBe("shared");

      // Check directories exist
      expect(await pathExists(join(repoPath, "projects"))).toBe(true);
      expect(await pathExists(join(repoPath, "shared", "skills"))).toBe(true);
      expect(await pathExists(join(repoPath, "shared", "agents"))).toBe(true);
      expect(await pathExists(join(repoPath, "shared", "hooks"))).toBe(true);
      expect(await pathExists(join(repoPath, "shared", "rules"))).toBe(true);
      expect(await pathExists(join(repoPath, ".cldpm", "templates"))).toBe(true);

      // Check files exist
      expect(await pathExists(join(repoPath, "CLAUDE.md"))).toBe(true);
      expect(await pathExists(join(repoPath, ".gitignore"))).toBe(true);
    });

    it("should initialize in new directory", async () => {
      const result = runCli("init my-monorepo", testDir);

      expect(result.exitCode).toBe(0);
      expect(await pathExists(join(testDir, "my-monorepo", "cldpm.json"))).toBe(true);
      expect(await pathExists(join(testDir, "my-monorepo", "projects"))).toBe(true);
      expect(await pathExists(join(testDir, "my-monorepo", "shared"))).toBe(true);
    });

    it("should initialize with custom name", async () => {
      const repoPath = join(testDir, "custom-repo");
      await mkdir(repoPath, { recursive: true });

      const result = runCli("init --name 'My Custom Repo'", repoPath);

      expect(result.exitCode).toBe(0);
      const configContent = await readFile(join(repoPath, "cldpm.json"), "utf-8");
      const config = JSON.parse(configContent);
      expect(config.name).toBe("My Custom Repo");
    });

    it("should fail if already initialized", async () => {
      const repoPath = join(testDir, "existing-repo");
      await mkdir(repoPath, { recursive: true });

      // First init
      runCli("init", repoPath);

      // Second init should fail
      const result = runCli("init", repoPath);

      expect(result.exitCode).toBe(1);
      expect(result.stdout + result.stderr).toContain("Already initialized");
    });
  });

  describe("init with --existing flag", () => {
    it("should fail on non-empty directory without --existing flag", async () => {
      const repoPath = join(testDir, "non-empty");
      await mkdir(repoPath, { recursive: true });

      // Create some existing content
      await writeFile(join(repoPath, "existing-file.txt"), "content");

      const result = runCli("init", repoPath);

      expect(result.exitCode).toBe(1);
      const output = result.stdout + result.stderr;
      expect(output).toContain("not empty");
      expect(output).toContain("--existing");
    });

    it("should succeed on non-empty directory with --existing flag", async () => {
      const repoPath = join(testDir, "non-empty-existing");
      await mkdir(repoPath, { recursive: true });

      // Create some existing content
      await writeFile(join(repoPath, "existing-file.txt"), "content");
      await mkdir(join(repoPath, "src"), { recursive: true });
      await writeFile(join(repoPath, "src", "main.ts"), "console.log('hello');");

      const result = runCli("init --existing", repoPath);

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toContain("Initialized CLDPM mono repo");

      // Check CLDPM structure was created
      expect(await pathExists(join(repoPath, "cldpm.json"))).toBe(true);
      expect(await pathExists(join(repoPath, "projects"))).toBe(true);
      expect(await pathExists(join(repoPath, "shared", "skills"))).toBe(true);

      // Check existing content is preserved
      expect(await pathExists(join(repoPath, "existing-file.txt"))).toBe(true);
      const existingContent = await readFile(join(repoPath, "existing-file.txt"), "utf-8");
      expect(existingContent).toBe("content");
      expect(await pathExists(join(repoPath, "src", "main.ts"))).toBe(true);
    });

    it("should warn but succeed on already initialized repo with --existing", async () => {
      const repoPath = join(testDir, "already-init");
      await mkdir(repoPath, { recursive: true });

      // First init
      runCli("init", repoPath);

      // Second init with --existing should warn but succeed
      const result = runCli("init --existing", repoPath);

      expect(result.exitCode).toBe(0);
      const output = result.stdout + result.stderr;
      expect(output).toContain("already exists");
      expect(output).toContain("updating");
    });

    it("should preserve existing CLAUDE.md with --existing", async () => {
      const repoPath = join(testDir, "preserve-claude");
      await mkdir(repoPath, { recursive: true });

      // Create existing CLAUDE.md
      const existingClaudeContent = "# My Existing Project\n\nThis is my existing project.";
      await writeFile(join(repoPath, "CLAUDE.md"), existingClaudeContent);

      const result = runCli("init --existing", repoPath);

      expect(result.exitCode).toBe(0);

      // Check CLAUDE.md was preserved
      const claudeContent = await readFile(join(repoPath, "CLAUDE.md"), "utf-8");
      expect(claudeContent).toContain("My Existing Project");
      expect(claudeContent).toContain("This is my existing project");

      // Check that CLDPM section was appended
      expect(claudeContent).toContain("CLDPM-SECTION-START");
    });

    it("should append to existing .gitignore with --existing", async () => {
      const repoPath = join(testDir, "preserve-gitignore");
      await mkdir(repoPath, { recursive: true });

      // Create existing .gitignore
      const existingGitignore = "node_modules/\n.env\n";
      await writeFile(join(repoPath, ".gitignore"), existingGitignore);

      const result = runCli("init --existing", repoPath);

      expect(result.exitCode).toBe(0);

      // Check .gitignore was updated, not replaced
      const gitignoreContent = await readFile(join(repoPath, ".gitignore"), "utf-8");
      expect(gitignoreContent).toContain("node_modules/");
      expect(gitignoreContent).toContain(".env");
      expect(gitignoreContent).toContain("CLDPM Note");
      expect(gitignoreContent).toContain("CLDPM-SECTION-START");
    });

    it("should create CLAUDE.md if it doesn't exist with --existing", async () => {
      const repoPath = join(testDir, "no-claude");
      await mkdir(repoPath, { recursive: true });

      // Create some existing content but no CLAUDE.md
      await writeFile(join(repoPath, "README.md"), "# My Repo");

      const result = runCli("init --existing", repoPath);

      expect(result.exitCode).toBe(0);

      // Check CLAUDE.md was created
      expect(await pathExists(join(repoPath, "CLAUDE.md"))).toBe(true);
      const claudeContent = await readFile(join(repoPath, "CLAUDE.md"), "utf-8");
      expect(claudeContent).toContain("CLDPM");
    });

    it("should not duplicate CLDPM section in .gitignore", async () => {
      const repoPath = join(testDir, "duplicate-gitignore");
      await mkdir(repoPath, { recursive: true });

      // Create .gitignore with CLDPM section already
      const existingGitignore = `node_modules/
.env
# CLDPM-SECTION-START
# CLDPM - Claude Project Manager
.cldpm/cache/
# CLDPM-SECTION-END
`;
      await writeFile(join(repoPath, ".gitignore"), existingGitignore);

      const result = runCli("init --existing", repoPath);

      expect(result.exitCode).toBe(0);

      // Check .gitignore doesn't have duplicate CLDPM sections
      const gitignoreContent = await readFile(join(repoPath, ".gitignore"), "utf-8");
      const cldpmSectionCount = (gitignoreContent.match(/CLDPM-SECTION-START/g) || []).length;
      expect(cldpmSectionCount).toBe(1);
    });
  });
});
