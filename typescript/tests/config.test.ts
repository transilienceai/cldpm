/**
 * Tests for config module.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  loadCpmConfig,
  saveCpmConfig,
  loadProjectConfig,
  saveProjectConfig,
  getProjectPath,
  listProjects,
  loadComponentMetadata,
} from "../src/core/config.js";
import { createCpmConfig, createProjectConfig } from "../src/schemas/index.js";

describe("Config", () => {
  let testDir: string;

  beforeEach(async () => {
    testDir = join(tmpdir(), `cpm-config-test-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    await mkdir(testDir, { recursive: true });
  });

  afterEach(async () => {
    await rm(testDir, { recursive: true, force: true });
  });

  describe("loadCpmConfig", () => {
    it("should load valid config", async () => {
      const configData = {
        name: "test-repo",
        version: "1.0.0",
        projectsDir: "projects",
        sharedDir: "shared",
      };
      await writeFile(
        join(testDir, "cpm.json"),
        JSON.stringify(configData)
      );

      const config = await loadCpmConfig(testDir);

      expect(config.name).toBe("test-repo");
      expect(config.projectsDir).toBe("projects");
    });

    it("should throw for missing config", async () => {
      await expect(loadCpmConfig(testDir)).rejects.toThrow();
    });

    it("should apply defaults", async () => {
      await writeFile(
        join(testDir, "cpm.json"),
        JSON.stringify({ name: "minimal" })
      );

      const config = await loadCpmConfig(testDir);

      expect(config.version).toBe("1.0.0");
      expect(config.projectsDir).toBe("projects");
    });
  });

  describe("saveCpmConfig", () => {
    it("should save config", async () => {
      const config = createCpmConfig("new-repo", { version: "2.0.0" });

      await saveCpmConfig(config, testDir);
      const loaded = await loadCpmConfig(testDir);

      expect(loaded.name).toBe("new-repo");
      expect(loaded.version).toBe("2.0.0");
    });
  });

  describe("loadProjectConfig", () => {
    it("should load valid project config", async () => {
      const projectDir = join(testDir, "my-project");
      await mkdir(projectDir, { recursive: true });

      const configData = {
        name: "my-project",
        description: "Test",
        dependencies: { skills: ["skill-a"], agents: [], hooks: [], rules: [] },
      };
      await writeFile(
        join(projectDir, "project.json"),
        JSON.stringify(configData)
      );

      const config = await loadProjectConfig(projectDir);

      expect(config.name).toBe("my-project");
      expect(config.dependencies.skills).toEqual(["skill-a"]);
    });

    it("should throw for missing project config", async () => {
      await expect(loadProjectConfig(testDir)).rejects.toThrow();
    });
  });

  describe("saveProjectConfig", () => {
    it("should save project config", async () => {
      const projectDir = join(testDir, "my-project");
      await mkdir(projectDir, { recursive: true });

      const config = createProjectConfig("my-project", {
        description: "Test project",
      });

      await saveProjectConfig(config, projectDir);
      const loaded = await loadProjectConfig(projectDir);

      expect(loaded.name).toBe("my-project");
      expect(loaded.description).toBe("Test project");
    });
  });

  describe("getProjectPath", () => {
    it("should find existing project", async () => {
      // Setup repo
      await writeFile(
        join(testDir, "cpm.json"),
        JSON.stringify({ name: "test-repo" })
      );
      const projectDir = join(testDir, "projects", "my-project");
      await mkdir(projectDir, { recursive: true });
      await writeFile(
        join(projectDir, "project.json"),
        JSON.stringify({ name: "my-project" })
      );

      const path = await getProjectPath("my-project", testDir);

      expect(path).toBe(projectDir);
    });

    it("should return null for non-existent project", async () => {
      await writeFile(
        join(testDir, "cpm.json"),
        JSON.stringify({ name: "test-repo" })
      );
      await mkdir(join(testDir, "projects"), { recursive: true });

      const path = await getProjectPath("nonexistent", testDir);

      expect(path).toBeNull();
    });
  });

  describe("listProjects", () => {
    it("should list all projects", async () => {
      // Setup repo
      await writeFile(
        join(testDir, "cpm.json"),
        JSON.stringify({ name: "test-repo" })
      );

      for (const name of ["project-a", "project-b"]) {
        const projectDir = join(testDir, "projects", name);
        await mkdir(projectDir, { recursive: true });
        await writeFile(
          join(projectDir, "project.json"),
          JSON.stringify({ name })
        );
      }

      const projects = await listProjects(testDir);

      expect(projects).toHaveLength(2);
      expect(projects.map((p) => p.name).sort()).toEqual([
        "project-a",
        "project-b",
      ]);
    });

    it("should return empty for no projects", async () => {
      await writeFile(
        join(testDir, "cpm.json"),
        JSON.stringify({ name: "test-repo" })
      );
      await mkdir(join(testDir, "projects"), { recursive: true });

      const projects = await listProjects(testDir);

      expect(projects).toEqual([]);
    });
  });

  describe("loadComponentMetadata", () => {
    it("should load component metadata", async () => {
      // Setup repo
      await writeFile(
        join(testDir, "cpm.json"),
        JSON.stringify({ name: "test-repo" })
      );

      const skillDir = join(testDir, "shared", "skills", "my-skill");
      await mkdir(skillDir, { recursive: true });
      await writeFile(
        join(skillDir, "skill.json"),
        JSON.stringify({
          name: "my-skill",
          description: "Test skill",
          dependencies: { skills: ["base"], agents: [], hooks: [], rules: [] },
        })
      );

      const metadata = await loadComponentMetadata("skills", "my-skill", testDir);

      expect(metadata).not.toBeNull();
      expect(metadata!.name).toBe("my-skill");
      expect(metadata!.dependencies.skills).toEqual(["base"]);
    });

    it("should return null for non-existent component", async () => {
      await writeFile(
        join(testDir, "cpm.json"),
        JSON.stringify({ name: "test-repo" })
      );

      const metadata = await loadComponentMetadata(
        "skills",
        "nonexistent",
        testDir
      );

      expect(metadata).toBeNull();
    });
  });
});
