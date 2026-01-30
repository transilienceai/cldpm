/**
 * Tests for schemas module.
 */

import { describe, it, expect } from "vitest";
import {
  CldpmConfigSchema,
  createCldpmConfig,
  ProjectConfigSchema,
  createProjectConfig,
  createProjectDependencies,
  ComponentMetadataSchema,
  createComponentMetadata,
  createComponentDependencies,
  parseComponentRef,
  getSingularType,
} from "../src/schemas/index.js";

describe("CldpmConfig", () => {
  it("should create config with all fields", () => {
    const config = createCldpmConfig("my-repo", {
      version: "2.0.0",
      projectsDir: "apps",
      sharedDir: "components",
    });

    expect(config.name).toBe("my-repo");
    expect(config.version).toBe("2.0.0");
    expect(config.projectsDir).toBe("apps");
    expect(config.sharedDir).toBe("components");
  });

  it("should create config with defaults", () => {
    const config = createCldpmConfig("my-repo");

    expect(config.name).toBe("my-repo");
    expect(config.version).toBe("1.0.0");
    expect(config.projectsDir).toBe("projects");
    expect(config.sharedDir).toBe("shared");
  });

  it("should parse valid config", () => {
    const data = {
      name: "test-repo",
      version: "1.0.0",
      projectsDir: "projects",
      sharedDir: "shared",
    };

    const config = CldpmConfigSchema.parse(data);

    expect(config.name).toBe("test-repo");
    expect(config.projectsDir).toBe("projects");
  });

  it("should fail without name", () => {
    expect(() => CldpmConfigSchema.parse({})).toThrow();
  });
});

describe("ProjectConfig", () => {
  it("should create config with all fields", () => {
    const config = createProjectConfig("my-project", {
      description: "Test project",
      dependencies: createProjectDependencies({
        skills: ["skill-a"],
      }),
    });

    expect(config.name).toBe("my-project");
    expect(config.description).toBe("Test project");
    expect(config.dependencies.skills).toEqual(["skill-a"]);
  });

  it("should create config with defaults", () => {
    const config = createProjectConfig("my-project");

    expect(config.name).toBe("my-project");
    expect(config.description).toBeUndefined();
    expect(config.dependencies.skills).toEqual([]);
  });

  it("should parse valid config", () => {
    const data = {
      name: "test-project",
      dependencies: {
        skills: ["skill-a"],
        agents: [],
        hooks: [],
        rules: [],
      },
    };

    const config = ProjectConfigSchema.parse(data);

    expect(config.name).toBe("test-project");
    expect(config.dependencies.skills).toEqual(["skill-a"]);
  });
});

describe("ComponentMetadata", () => {
  it("should create metadata with all fields", () => {
    const metadata = createComponentMetadata("my-component", {
      description: "Test component",
      dependencies: createComponentDependencies({
        skills: ["skill-a"],
      }),
    });

    expect(metadata.name).toBe("my-component");
    expect(metadata.description).toBe("Test component");
    expect(metadata.dependencies.skills).toEqual(["skill-a"]);
  });

  it("should create metadata with defaults", () => {
    const metadata = createComponentMetadata("my-component");

    expect(metadata.name).toBe("my-component");
    expect(metadata.description).toBeUndefined();
    expect(metadata.dependencies.skills).toEqual([]);
  });

  it("should allow extra fields", () => {
    const data = {
      name: "my-component",
      version: "1.0.0",
      author: "test",
    };

    const metadata = ComponentMetadataSchema.parse(data);

    expect(metadata.name).toBe("my-component");
    expect((metadata as Record<string, unknown>).version).toBe("1.0.0");
    expect((metadata as Record<string, unknown>).author).toBe("test");
  });
});

describe("parseComponentRef", () => {
  it("should parse typed reference", () => {
    const result = parseComponentRef("skill:my-skill");

    expect(result.type).toBe("skills");
    expect(result.name).toBe("my-skill");
  });

  it("should parse untyped reference", () => {
    const result = parseComponentRef("my-skill");

    expect(result.type).toBeNull();
    expect(result.name).toBe("my-skill");
  });

  it("should handle agent type", () => {
    const result = parseComponentRef("agent:my-agent");

    expect(result.type).toBe("agents");
    expect(result.name).toBe("my-agent");
  });
});

describe("getSingularType", () => {
  it("should return singular form", () => {
    expect(getSingularType("skills")).toBe("skill");
    expect(getSingularType("agents")).toBe("agent");
    expect(getSingularType("hooks")).toBe("hook");
    expect(getSingularType("rules")).toBe("rule");
  });
});
