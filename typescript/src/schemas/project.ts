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
 * Convert a string to kebab-case.
 */
function toKebabCase(str: string): string {
  return str
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * Schema for project.json configuration file.
 * The `id` field is optional for backward compatibility — if omitted,
 * it is derived as the kebab-case of `name`.
 */
export const ProjectConfigSchema = z
  .object({
    id: z.string().optional(),
    name: z.string().min(1, "Name is required"),
    description: z.string().optional(),
    dependencies: ProjectDependenciesSchema.default({
      skills: [],
      agents: [],
      hooks: [],
      rules: [],
    }),
  })
  .transform((data) => ({
    ...data,
    id: data.id && data.id.length > 0 ? data.id : toKebabCase(data.name),
  }));

export type ProjectConfig = z.infer<typeof ProjectConfigSchema>;

/**
 * Create a ProjectConfig with defaults.
 */
export function createProjectConfig(
  name: string,
  options: Partial<Omit<ProjectConfig, "name" | "id">> = {}
): ProjectConfig {
  return ProjectConfigSchema.parse({
    id: toKebabCase(name),
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
