/**
 * Tests for resolver module.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdir, rm, writeFile, symlink } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  resolveProject,
  resolveComponent,
  resolveLocalComponent,
  getLocalComponentsInProject,
  listSharedComponents,
  resolveComponentDependencies,
  getAllDependenciesForComponent,
} from "../src/core/resolver.js";

describe("Resolver", () => {
  let testDir: string;

  beforeEach(async () => {
    testDir = join(tmpdir(), `cldpm-resolver-test-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    await mkdir(testDir, { recursive: true });
  });

  afterEach(async () => {
    await rm(testDir, { recursive: true, force: true });
  });

  async function setupRepo() {
    // Create cldpm.json
    await writeFile(
      join(testDir, "cldpm.json"),
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

  async function createSharedComponent(
    type: string,
    name: string,
    deps?: Record<string, string[]>
  ) {
    const compPath = join(testDir, "shared", type, name);
    await mkdir(compPath, { recursive: true });

    const singular = type.slice(0, -1);
    await writeFile(join(compPath, `${singular.toUpperCase()}.md`), `# ${name}`);

    const metadata: Record<string, unknown> = { name };
    if (deps) {
      metadata.dependencies = deps;
    }
    await writeFile(
      join(compPath, `${singular}.json`),
      JSON.stringify(metadata)
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

  describe("resolveComponent", () => {
    it("should resolve existing skill", async () => {
      await setupRepo();
      await createSharedComponent("skills", "code-review");

      const result = await resolveComponent(
        "skills",
        "code-review",
        join(testDir, "shared")
      );

      expect(result).not.toBeNull();
      expect(result!.name).toBe("code-review");
      expect(result!.type).toBe("shared");
      expect(result!.files).toContain("SKILL.md");
    });

    it("should return null for non-existent component", async () => {
      await setupRepo();

      const result = await resolveComponent(
        "skills",
        "nonexistent",
        join(testDir, "shared")
      );

      expect(result).toBeNull();
    });
  });

  describe("resolveLocalComponent", () => {
    it("should resolve local skill", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");

      // Create local skill
      const localSkill = join(projectPath, ".claude", "skills", "local-skill");
      await mkdir(localSkill, { recursive: true });
      await writeFile(join(localSkill, "SKILL.md"), "# Local Skill");

      const result = await resolveLocalComponent(
        "skills",
        "local-skill",
        projectPath
      );

      expect(result).not.toBeNull();
      expect(result!.name).toBe("local-skill");
      expect(result!.type).toBe("local");
    });

    it("should return null for symlinks", async () => {
      await setupRepo();
      await createSharedComponent("skills", "shared-skill");
      const projectPath = await createProject("my-project");

      // Create symlink
      const linkPath = join(projectPath, ".claude", "skills", "shared-skill");
      const source = join(testDir, "shared", "skills", "shared-skill");
      await symlink(source, linkPath);

      const result = await resolveLocalComponent(
        "skills",
        "shared-skill",
        projectPath
      );

      expect(result).toBeNull();
    });
  });

  describe("getLocalComponentsInProject", () => {
    it("should get all local components", async () => {
      await setupRepo();
      const projectPath = await createProject("my-project");

      // Create local components
      await mkdir(join(projectPath, ".claude", "skills", "local-skill-1"));
      await mkdir(join(projectPath, ".claude", "skills", "local-skill-2"));
      await mkdir(join(projectPath, ".claude", "agents", "local-agent"));

      const result = await getLocalComponentsInProject(projectPath);

      expect(result.skills).toHaveLength(2);
      expect(result.agents).toHaveLength(1);
      expect(result.hooks).toHaveLength(0);
      expect(result.rules).toHaveLength(0);
    });
  });

  describe("resolveProject", () => {
    it("should resolve by name", async () => {
      await setupRepo();
      await createSharedComponent("skills", "code-review");
      await createProject("my-project", {
        skills: ["code-review"],
        agents: [],
        hooks: [],
        rules: [],
      });

      const result = await resolveProject("my-project", testDir);

      expect(result.name).toBe("my-project");
      expect(result.path).toContain("my-project");
      expect(result.config).toBeDefined();
      expect(result.shared).toBeDefined();
      expect(result.local).toBeDefined();
    });

    it("should resolve by path", async () => {
      await setupRepo();
      await createProject("my-project");

      const result = await resolveProject("projects/my-project", testDir);

      expect(result.name).toBe("my-project");
    });

    it("should resolve with shared dependencies", async () => {
      await setupRepo();
      await createSharedComponent("skills", "skill-a");
      await createSharedComponent("skills", "skill-b");
      await createProject("my-project", {
        skills: ["skill-a", "skill-b"],
        agents: [],
        hooks: [],
        rules: [],
      });

      const result = await resolveProject("my-project", testDir);

      expect(result.shared.skills).toHaveLength(2);
      const names = result.shared.skills.map((s) => s.name);
      expect(names).toContain("skill-a");
      expect(names).toContain("skill-b");
    });

    it("should throw for non-existent project", async () => {
      await setupRepo();

      await expect(resolveProject("nonexistent", testDir)).rejects.toThrow();
    });
  });

  describe("listSharedComponents", () => {
    it("should list all components", async () => {
      await setupRepo();
      await createSharedComponent("skills", "skill-a");
      await createSharedComponent("skills", "skill-b");
      await createSharedComponent("agents", "agent-x");

      const result = await listSharedComponents(testDir);

      expect(result.skills).toContain("skill-a");
      expect(result.skills).toContain("skill-b");
      expect(result.agents).toContain("agent-x");
      expect(result.hooks).toEqual([]);
      expect(result.rules).toEqual([]);
    });
  });

  describe("resolveComponentDependencies", () => {
    it("should resolve simple dependencies", async () => {
      await setupRepo();
      await createSharedComponent("skills", "base-skill");
      await createSharedComponent("skills", "main-skill", {
        skills: ["base-skill"],
        agents: [],
        hooks: [],
        rules: [],
      });

      const result = await resolveComponentDependencies(
        "skills",
        "main-skill",
        testDir
      );

      expect(result).toContainEqual(["skills", "base-skill"]);
    });

    it("should resolve transitive dependencies", async () => {
      await setupRepo();
      await createSharedComponent("skills", "level-1");
      await createSharedComponent("skills", "level-2", {
        skills: ["level-1"],
        agents: [],
        hooks: [],
        rules: [],
      });
      await createSharedComponent("skills", "level-3", {
        skills: ["level-2"],
        agents: [],
        hooks: [],
        rules: [],
      });

      const result = await resolveComponentDependencies(
        "skills",
        "level-3",
        testDir
      );

      expect(result).toContainEqual(["skills", "level-2"]);
      expect(result).toContainEqual(["skills", "level-1"]);
    });

    it("should resolve cross-type dependencies", async () => {
      await setupRepo();
      await createSharedComponent("skills", "helper-skill");
      await createSharedComponent("rules", "security-rule");
      await createSharedComponent("agents", "main-agent", {
        skills: ["helper-skill"],
        agents: [],
        hooks: [],
        rules: ["security-rule"],
      });

      const result = await resolveComponentDependencies(
        "agents",
        "main-agent",
        testDir
      );

      expect(result).toContainEqual(["skills", "helper-skill"]);
      expect(result).toContainEqual(["rules", "security-rule"]);
    });

    it("should return empty for no dependencies", async () => {
      await setupRepo();
      await createSharedComponent("skills", "standalone");

      const result = await resolveComponentDependencies(
        "skills",
        "standalone",
        testDir
      );

      expect(result).toEqual([]);
    });
  });

  describe("getAllDependenciesForComponent", () => {
    it("should get dependencies organized by type", async () => {
      await setupRepo();
      await createSharedComponent("skills", "skill-a");
      await createSharedComponent("skills", "skill-b");
      await createSharedComponent("hooks", "hook-x");
      await createSharedComponent("agents", "main-agent", {
        skills: ["skill-a", "skill-b"],
        agents: [],
        hooks: ["hook-x"],
        rules: [],
      });

      const result = await getAllDependenciesForComponent(
        "agents",
        "main-agent",
        testDir
      );

      expect(result.skills).toContain("skill-a");
      expect(result.skills).toContain("skill-b");
      expect(result.hooks).toContain("hook-x");
      expect(result.agents).toEqual([]);
      expect(result.rules).toEqual([]);
    });

    it("should not have duplicates", async () => {
      await setupRepo();
      await createSharedComponent("skills", "common");
      await createSharedComponent("skills", "skill-a", {
        skills: ["common"],
        agents: [],
        hooks: [],
        rules: [],
      });
      await createSharedComponent("skills", "skill-b", {
        skills: ["common"],
        agents: [],
        hooks: [],
        rules: [],
      });
      await createSharedComponent("agents", "main-agent", {
        skills: ["skill-a", "skill-b"],
        agents: [],
        hooks: [],
        rules: [],
      });

      const result = await getAllDependenciesForComponent(
        "agents",
        "main-agent",
        testDir
      );

      // "common" should appear only once
      const commonCount = result.skills.filter((s) => s === "common").length;
      expect(commonCount).toBe(1);
    });
  });
});
