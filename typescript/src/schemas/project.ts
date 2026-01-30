/**
 * Project configuration schema.
 */

import { z } from "zod";

/**
 * Schema for project dependencies.
 */
export const ProjectDependenciesSchema = z.object({
  skills: z.array(z.string()).default([]),
  agents: z.array(z.string()).default([]),
  hooks: z.array(z.string()).default([]),
  rules: z.array(z.string()).default([]),
});

export type ProjectDependencies = z.infer<typeof ProjectDependenciesSchema>;

/**
 * Schema for project.json configuration file.
 */
export const ProjectConfigSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  dependencies: ProjectDependenciesSchema.default({
    skills: [],
    agents: [],
    hooks: [],
    rules: [],
  }),
});

export type ProjectConfig = z.infer<typeof ProjectConfigSchema>;

/**
 * Create a ProjectConfig with defaults.
 */
export function createProjectConfig(
  name: string,
  options: Partial<Omit<ProjectConfig, "name">> = {}
): ProjectConfig {
  return ProjectConfigSchema.parse({
    name,
    ...options,
  });
}

/**
 * Create empty project dependencies.
 */
export function createProjectDependencies(
  deps: Partial<ProjectDependencies> = {}
): ProjectDependencies {
  return ProjectDependenciesSchema.parse(deps);
}
