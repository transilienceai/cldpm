/**
 * Tests for linker module.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdir, rm, writeFile, symlink, lstat, readFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  createSymlink,
  removeProjectLinks,
  updateComponentGitignore,
  syncProjectLinks,
  addComponentLink,
  removeComponentLink,
  getLocalComponents,
  getSharedComponents,
} from "../src/core/linker.js";
import { pathExists } from "../src/core/config.js";

describe("Linker", () => {
  let testDir: string;

  beforeEach(async () => {
    testDir = join(tmpdir(), `cpm-linker-test-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    await mkdir(testDir, { recursive: true });
  });

  afterEach(async () => {
    await rm(testDir, { recursive: true, force: true });
  });

  async function setupRepo() {
    // Create cpm.json
    await writeFile(
      join(testDir, "cpm.json"),
      JSON.stringify({
        name: "test-repo",
        version: "1.0.0",
        projectsDir: "projects",
        sharedDir: "shared",
      })
    );

    // Create directories
    await mkdir(join(testDir, "projects"), { recursive: true });
    for (const type of ["skills", "agents", "hooks", "rules"]) {
      await mkdir(join(testDir, "shared", type), { recursive: true });
    }
  }

  async function createSharedComponent(type: string, name: string) {
    const compPath = join(testDir, "shared", type, name);
    await mkdir(compPath, { recursive: true });

    const singular = type.slice(0, -1);
    await writeFile(join(compPath, `${singular.toUpperCase()}.md`), `# ${name}`);
    await writeFile(
      join(compPath, `${singular}.json`),
      JSON.stringify({ name })
    );
  }

  async function createProject(name: string, deps?: Record<string, string[]>) {
    const projectPath = join(testDir, "projects", name);
    await mkdir(projectPath, { recursive: true });

    // Create .claude structure
    for (const type of ["skills", "agents", "hooks", "rules"]) {
      await mkdir(join(projectPath, ".claude", type), { recursive: true });
    }

    const config = {
      name,
      dependencies: deps || { skills: [], agents: [], hooks: [], rules: [] },
    };
    await writeFile(
      join(projectPath, "project.json"),
      JSON.stringify(config)
    );

    return projectPath;
  }

  describe("createSymlink", () => {
    it("should create valid symlink", async () => {
      const source = join(testDir, "source");
      await mkdir(source);
      await writeFile(join(source, "file.txt"), "content");

      const target = join(testDir, "target", "link");
      await mkdir(join(testDir, "target"), { recursive: true });

      const result = await createSymlink(source, target);

      expect(result).toBe(true);
      const stats = await lstat(target);
      expect(stats.isSymbolicLink()).toBe(true);
      expect(await pathExists(join(target, "file.txt"))).toBe(true);
    });

    it("should replace existing symlink", async () => {
      const source1 = join(testDir, "source1");
      await mkdir(source1);

      const source2 = join(testDir, "source2");
      await mkdir(source2);
      await writeFile(join(source2, "new.txt"), "new");

      const target = join(testDir, "link");
      await symlink(source1, target);

      const result = await createSymlink(source2, target);

      expect(result).toBe(true);
      expect(await pathExists(join(target, "new.txt"))).toBe(true);
    });

    it("should fail if non-symlink file exists", async () => {
      const source = join(testDir, "source");
      await mkdir(source);

      const target = join(testDir, "target");
      await writeFile(target, "existing file");

      const result = await createSymlink(source, target);

      expect(result).toBe(false);
      const stats = await lstat(target);
      expect(stats.isSymbolicLink()).toBe(false);
    });
  });

  describe("removeProjectLinks", () => {
    it("should remove all symlinks", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");
      await createSharedComponent("skills", "skill-a");
      await createSharedComponent("skills", "skill-b");

      // Create symlinks
      const skillsDir = join(projectPath, ".claude", "skills");
      await symlink(
        join(testDir, "shared", "skills", "skill-a"),
        join(skillsDir, "skill-a")
      );
      await symlink(
        join(testDir, "shared", "skills", "skill-b"),
        join(skillsDir, "skill-b")
      );

      await removeProjectLinks(projectPath);

      expect(await pathExists(join(skillsDir, "skill-a"))).toBe(false);
      expect(await pathExists(join(skillsDir, "skill-b"))).toBe(false);
    });

    it("should preserve local components", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");
      await createSharedComponent("skills", "shared-skill");

      // Create local component
      const localSkill = join(projectPath, ".claude", "skills", "local-skill");
      await mkdir(localSkill);
      await writeFile(join(localSkill, "SKILL.md"), "# Local");

      // Create symlink
      await symlink(
        join(testDir, "shared", "skills", "shared-skill"),
        join(projectPath, ".claude", "skills", "shared-skill")
      );

      await removeProjectLinks(projectPath);

      expect(await pathExists(localSkill)).toBe(true);
      expect(
        await pathExists(join(projectPath, ".claude", "skills", "shared-skill"))
      ).toBe(false);
    });
  });

  describe("updateComponentGitignore", () => {
    it("should create gitignore", async () => {
      const compDir = join(testDir, "skills");
      await mkdir(compDir);

      await updateComponentGitignore(compDir, ["skill-a", "skill-b"]);

      const gitignore = join(compDir, ".gitignore");
      expect(await pathExists(gitignore)).toBe(true);
      const content = await readFile(gitignore, "utf-8");
      expect(content).toContain("skill-a");
      expect(content).toContain("skill-b");
      expect(content).toContain("CPM shared components");
    });

    it("should remove gitignore when empty", async () => {
      const compDir = join(testDir, "skills");
      await mkdir(compDir);

      // Create initial gitignore (with exact CPM header)
      const gitignore = join(compDir, ".gitignore");
      await writeFile(gitignore, "# CPM shared components (auto-generated)\nskill-a\n");

      await updateComponentGitignore(compDir, []);

      expect(await pathExists(gitignore)).toBe(false);
    });

    it("should preserve custom gitignore", async () => {
      const compDir = join(testDir, "skills");
      await mkdir(compDir);

      // Create custom gitignore
      const gitignore = join(compDir, ".gitignore");
      await writeFile(gitignore, "# Custom content\n*.tmp\n");

      await updateComponentGitignore(compDir, []);

      expect(await pathExists(gitignore)).toBe(true);
      const content = await readFile(gitignore, "utf-8");
      expect(content).toContain("Custom content");
    });
  });

  describe("syncProjectLinks", () => {
    it("should create symlinks for dependencies", async () => {
      await setupRepo();
      await createSharedComponent("skills", "skill-a");
      await createSharedComponent("skills", "skill-b");
      const projectPath = await createProject("my-project", {
        skills: ["skill-a", "skill-b"],
        agents: [],
        hooks: [],
        rules: [],
      });

      const result = await syncProjectLinks(projectPath, testDir);

      expect(result.created).toContain("skills/skill-a");
      expect(result.created).toContain("skills/skill-b");

      const skillAPath = join(projectPath, ".claude", "skills", "skill-a");
      const skillBPath = join(projectPath, ".claude", "skills", "skill-b");
      const statsA = await lstat(skillAPath);
      const statsB = await lstat(skillBPath);
      expect(statsA.isSymbolicLink()).toBe(true);
      expect(statsB.isSymbolicLink()).toBe(true);
    });

    it("should report missing components", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project", {
        skills: ["nonexistent"],
        agents: [],
        hooks: [],
        rules: [],
      });

      const result = await syncProjectLinks(projectPath, testDir);

      expect(result.missing).toContain("skills/nonexistent");
    });

    it("should update gitignore", async () => {
      await setupRepo();
      await createSharedComponent("skills", "skill-a");
      const projectPath = await createProject("my-project", {
        skills: ["skill-a"],
        agents: [],
        hooks: [],
        rules: [],
      });

      await syncProjectLinks(projectPath, testDir);

      const gitignore = join(projectPath, ".claude", "skills", ".gitignore");
      expect(await pathExists(gitignore)).toBe(true);
      const content = await readFile(gitignore, "utf-8");
      expect(content).toContain("skill-a");
    });
  });

  describe("addComponentLink", () => {
    it("should add single link", async () => {
      await setupRepo();
      await createSharedComponent("skills", "code-review");
      const projectPath = await createProject("my-project");

      const result = await addComponentLink(
        projectPath,
        "skills",
        "code-review",
        testDir
      );

      expect(result).toBe(true);
      const linkPath = join(projectPath, ".claude", "skills", "code-review");
      const stats = await lstat(linkPath);
      expect(stats.isSymbolicLink()).toBe(true);
    });

    it("should update gitignore", async () => {
      await setupRepo();
      await createSharedComponent("skills", "code-review");
      const projectPath = await createProject("my-project");

      await addComponentLink(projectPath, "skills", "code-review", testDir);

      const gitignore = join(projectPath, ".claude", "skills", ".gitignore");
      const content = await readFile(gitignore, "utf-8");
      expect(content).toContain("code-review");
    });

    it("should fail for non-existent component", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");

      const result = await addComponentLink(
        projectPath,
        "skills",
        "nonexistent",
        testDir
      );

      expect(result).toBe(false);
    });
  });

  describe("removeComponentLink", () => {
    it("should remove link", async () => {
      await setupRepo();
      await createSharedComponent("skills", "skill-a");
      const projectPath = await createProject("my-project");

      // Add link first
      await addComponentLink(projectPath, "skills", "skill-a", testDir);

      // Then remove it
      const result = await removeComponentLink(projectPath, "skills", "skill-a");

      expect(result).toBe(true);
      const linkPath = join(projectPath, ".claude", "skills", "skill-a");
      expect(await pathExists(linkPath)).toBe(false);
    });

    it("should return false for non-existent link", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");

      const result = await removeComponentLink(
        projectPath,
        "skills",
        "nonexistent"
      );

      expect(result).toBe(false);
    });

    it("should return false for non-symlink", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");

      // Create a regular directory, not a symlink
      const dirPath = join(projectPath, ".claude", "skills", "local-skill");
      await mkdir(dirPath);

      const result = await removeComponentLink(
        projectPath,
        "skills",
        "local-skill"
      );

      expect(result).toBe(false);
    });
  });

  describe("getLocalComponents", () => {
    it("should get local components", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");

      // Create local skills
      await mkdir(join(projectPath, ".claude", "skills", "local-a"));
      await mkdir(join(projectPath, ".claude", "skills", "local-b"));

      const result = await getLocalComponents(projectPath);

      expect(result.skills).toContain("local-a");
      expect(result.skills).toContain("local-b");
    });

    it("should ignore symlinks", async () => {
      await setupRepo();
      await createSharedComponent("skills", "shared-skill");
      const projectPath = await createProject("my-project");

      // Create symlink
      await symlink(
        join(testDir, "shared", "skills", "shared-skill"),
        join(projectPath, ".claude", "skills", "shared-skill")
      );

      // Create local
      await mkdir(join(projectPath, ".claude", "skills", "local-skill"));

      const result = await getLocalComponents(projectPath);

      expect(result.skills).toContain("local-skill");
      expect(result.skills).not.toContain("shared-skill");
    });
  });

  describe("getSharedComponents", () => {
    it("should get shared (symlinked) components", async () => {
      await setupRepo();
      await createSharedComponent("skills", "shared-a");
      await createSharedComponent("skills", "shared-b");
      const projectPath = await createProject("my-project");

      // Create symlinks
      await symlink(
        join(testDir, "shared", "skills", "shared-a"),
        join(projectPath, ".claude", "skills", "shared-a")
      );
      await symlink(
        join(testDir, "shared", "skills", "shared-b"),
        join(projectPath, ".claude", "skills", "shared-b")
      );

      const result = await getSharedComponents(projectPath);

      expect(result.skills).toContain("shared-a");
      expect(result.skills).toContain("shared-b");
    });

    it("should ignore local components", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");

      // Create local
      await mkdir(join(projectPath, ".claude", "skills", "local-skill"));

      const result = await getSharedComponents(projectPath);

      expect(result.skills).not.toContain("local-skill");
    });
  });
});
